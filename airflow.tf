

resource "helm_release" "airflow" {
  name       = "apache-airflow"
  repository = "https://airflow.apache.org"
  chart      = "airflow"
  namespace  = var.namespace
  version    = "1.18.0" 
  
  # Dependencies are now much simpler
  depends_on = [
    kubernetes_namespace.helical_pdqueiros_namespace, 
  ] 

  set = [
    { name = "airflow.executor", value = "CeleryExecutor" },

    # https://airflow.apache.org/docs/helm-chart/stable/production-guide.html
    { name = "createUserJob.useHelmHooks", value = "false" },
    { name = "createUserJob.applyCustomEnv", value = "false" },
    { name = "migrateDatabaseJob.useHelmHooks", value = "false" },
    { name = "migrateDatabaseJob.applyCustomEnv", value = "false" },

    { name = "postgresql.enabled", value = "true" },
    
    # using this image as suggested through an issue in airflow: https://github.com/apache/airflow/issues/56498
    { name = "postgresql.image.repository", value = "bitnamilegacy/postgresql" },
    { name = "postgresql.image.tag", value = "16.1.0-debian-11-r15" },

    # 3. STORAGE FIX: Ensure the internal PostgreSQL uses a valid storage class for Minikube
    { name = "postgresql.persistence.storageClass", value = "standard" },
    
    # Optional: enable webserver service
    { name = "webserver.service.type", value = "LoadBalancer" },
  ]
}
