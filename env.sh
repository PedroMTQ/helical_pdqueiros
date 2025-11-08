set -a
source .env
source local.env
# for the Ray cluster
export HEAD_POD=$(kubectl get pods -n helical-pdqueiros --selector=ray.io/identifier=helical-raycluster-head -o custom-columns=POD:metadata.name --no-headers)
set +a
