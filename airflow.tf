
resource "helm_release" "airflow" {
  name       = "apache-airflow"
  repository = "https://airflow.apache.org"
  chart      = "airflow"
  namespace  = var.namespace
  version    = "1.18.0" 
  
  # Dependencies are now much simpler
  depends_on = [
    kubernetes_namespace.helical_pdqueiros_namespace,
    # kubernetes_persistent_volume_claim.airflow_dags_pvc
  ] 

  values = [
      # The file function reads the content of the YAML file as a string
      file("${path.module}/config/airflow.yaml")
    ]
}



# resource "kubernetes_persistent_volume" "airflow_dags_pv" {
#   metadata {
#     name = "local-dags-pv"
#   }
#   spec {
#     capacity = {
#       storage = "5Gi"
#     }
    
#     access_modes = ["ReadWriteMany"] 
#     persistent_volume_source {
#       host_path {
#         # TODO in a prod environment, this would obviously be in a proper path. Unfortunately, it seems like the pods can't use path.root since they default to ./dags
#         path = "/host_workspace/helical_pdqueiros/dags"
#       }
#     }
#     # storage_class_name = "local-storage-manual" 
#   }
# }


# resource "kubernetes_persistent_volume_claim" "airflow_dags_pvc" {
#   metadata {
#     name      = "local-dags-pvc"
#     namespace = var.namespace   
#   }
#   spec {
#     access_modes = ["ReadWriteMany"]
#     resources {
#       requests = {
#         storage = "1Gi"
#       }
#     }
#     # storage_class_name = "local-storage-manual" 
#   }
  
#   depends_on = [
#     kubernetes_namespace.helical_pdqueiros_namespace,
#     kubernetes_persistent_volume.airflow_dags_pv,
#   ]
# }