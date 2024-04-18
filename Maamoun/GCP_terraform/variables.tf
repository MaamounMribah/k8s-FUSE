variable "project_id" {
  description = "The project ID"
  default = "int-infra-training-gcp"
}

variable "service_account_user_email" {
  description = "Email of the user to be added as a service account user"
  type        = string
  # Ensure you provide a default value or pass this variable during terraform apply if needed.
  default = "m.mribah@instadeep.com"
}

variable "region" {
  description = "The region in which resources will be defined"
  default = "europe-west3"
}
variable "zone" {
  description = "The zone in which resources will be defined"
  default = "europe-west3-c"
}