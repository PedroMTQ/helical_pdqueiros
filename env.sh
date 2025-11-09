set -a
source .env
export MINIO_HOST="localhost"
export MLFLOW_S3_ENDPOINT_URL="http://localhost:9000"
# for the Ray cluster
export HEAD_POD=$(kubectl get pods -n helical-pdqueiros --selector=ray.io/identifier=helical-raycluster-head -o custom-columns=POD:metadata.name --no-headers)
set +a
