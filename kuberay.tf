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

  values = [
    yamlencode({
      service = {
        type = "ClusterIP"
        port = 8080
      }
      # optional authentication/authorization settings can go here
      # see https://github.com/ray-project/kuberay/tree/master/helm-chart/kuberay-apiserver
    })
  ]

  depends_on = [helm_release.kuberay_operator]
}


locals {
  raycluster_manifest = yamldecode(file("${path.module}/config/raycluster.yaml"))
}


resource "kubernetes_manifest" "raycluster" {
  manifest = local.raycluster_manifest
  depends_on = [helm_release.kuberay_operator]
}
