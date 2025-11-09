set -a
source .env
source local.env
# for the Ray cluster
export HEAD_POD=$(kubectl get pods -n helical-pdqueiros --selector=ray.io/identifier=helical-raycluster-head -o custom-columns=POD:metadata.name --no-headers)
set +a
export MINIO_HOST=localhost
export DEBUG=1
export SLEEP_TIME=10