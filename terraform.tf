
variable "namespace" {
  type        = string
}

resource "kubernetes_namespace" "helical_pdqueiros_namespace" {
  metadata {
    name = var.namespace
  }
}

terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 3.1.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.38.0"
    }
  }
}

# if you are not using minikube you need to change these 2
provider "kubernetes" {
  config_path = "~/.kube/config"
  config_context = "minikube"
}

provider "helm" {
  kubernetes = {
    config_path = "~/.kube/config"
    config_context = "minikube"
  }
}
