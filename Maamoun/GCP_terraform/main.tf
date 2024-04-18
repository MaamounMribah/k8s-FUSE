

# Retrieve an access token as the Terraform runner
data "google_client_config" "provider" {}

resource "google_service_account" "sa" {
  account_id   = "maamoun-mribah-sa-int"
  display_name = "A service account that only [members] can use"
  project      = var.project_id
}

resource "google_service_account_iam_binding" "admin-account-iam" {
  service_account_id = google_service_account.sa.name
  role               = "roles/iam.serviceAccountUser"

  members = [
    "user:${var.service_account_user_email}",
  ]
}

resource "google_container_cluster" "my-kubernetes-cluster" {
  name     = "my-kubernetes-cluster"
  location = var.region
  project      = var.project_id
  
  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection = false

  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}



resource "google_container_node_pool" "preemptible_nodes" {
  name       = "my-node-pool"
  location   = var.region
  cluster    = google_container_cluster.my-kubernetes-cluster.name
  // node_count = 3

  node_config {
    preemptible  = true
    machine_type = "e2-standard-2"

    service_account = google_service_account.sa.email
    oauth_scopes    = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
  autoscaling {
    min_node_count = 1
    max_node_count = 3
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}


resource "null_resource" "annotate_default_ksa" {
  triggers = {
    sa_email = google_service_account.sa.email
  }

  provisioner "local-exec" {
    environment = {
      KUBECONFIG = "~/.kube/config"
    }
    command = <<EOT
    gcloud container clusters get-credentials my-kubernetes-cluster --region ${var.region} --project ${var.project_id} &&
    kubectl annotate serviceaccount default --namespace default iam.gke.io/gcp-service-account=${google_service_account.sa.email} --overwrite
    EOT
  }
  depends_on = [google_container_cluster.my-kubernetes-cluster]
}

resource "google_service_account_iam_binding" "workload_identity_user" {
  service_account_id = google_service_account.sa.id
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[default/default]",
  ]
}

# Grant Artifact Registry Writer role to the service account
resource "google_project_iam_member" "sa_artifactregistry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.sa.email}"
}

resource "google_artifact_registry_repository" "docker_repository" {
  location      = var.region
  repository_id = "maamoun" # Use your desired repository name here
  description   = "Docker repository for LLM pipeline images"
  format        = "DOCKER"
}

resource "google_storage_bucket" "my_bucket" {
  name     = "my-bucket-${var.project_id}"
  location = var.region
  storage_class = "STANDARD"
  force_destroy = true
  
  
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket_iam_member" "bucket_member" {
  bucket = google_storage_bucket.my_bucket.name
  role   = "roles/storage.objectAdmin"
  
  # Grants the service account read access to the bucket
  member = "serviceAccount:${google_service_account.sa.email}"
}
