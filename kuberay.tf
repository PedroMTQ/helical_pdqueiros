
variable "namespace" {
  type        = string
  description = "The default namespace for Helical's exercise"
  default = "helical-pdqueiros"
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


resource "helm_release" "kuberay_operator" {
  name       = "kuberay-operator"
  repository = "https://ray-project.github.io/kuberay-helm/"
  chart      = "kuberay-operator"
  namespace  = var.namespace
  depends_on = [
    kubernetes_namespace.helical_pdqueiros_namespace
  ]

  set = [
    { name = "singleNamespaceInstall", value = true },
    { name = "rbacEnable", value = true },
  ]
  values = [
    yamlencode({
      watchNamespace         = [var.namespace]
    })
  ]

}

resource "helm_release" "kuberay_apiserver" {
  name       = "kuberay-apiserver"
  repository = "https://ray-project.github.io/kuberay-helm/"
  chart      = "kuberay-apiserver"
  namespace  = var.namespace

  create_namespace = false
  atomic           = true


  depends_on = [helm_release.kuberay_operator]
}


locals {
  raycluster_manifest = yamldecode(file("${path.module}/config/raycluster.yaml"))
}


resource "kubernetes_manifest" "raycluster" {
  manifest = local.raycluster_manifest
  depends_on = [helm_release.kuberay_operator]
  
}
