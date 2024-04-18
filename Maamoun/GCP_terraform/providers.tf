provider "google" {
  project     = var.project_id
  region      = var.region
  zone        = var.zone
}

provider "helm" {
  kubernetes {
    host  = "https://${google_container_cluster.my-kubernetes-cluster.endpoint}"
    token = data.google_client_config.provider.access_token
    cluster_ca_certificate = base64decode("${google_container_cluster.my-kubernetes-cluster.master_auth[0].cluster_ca_certificate}")
  }
}
provider "kubernetes" {
  host                   = "https://${google_container_cluster.my-kubernetes-cluster.endpoint}"
  token                  = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.my-kubernetes-cluster.master_auth[0].cluster_ca_certificate)
}