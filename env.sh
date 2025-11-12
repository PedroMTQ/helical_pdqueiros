set -a
source .env
export MINIO_HOST="localhost"
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export MLFLOW_TRACKING_URI=http://localhost:5000
set +a
