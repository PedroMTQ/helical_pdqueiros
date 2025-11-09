# helical-pdqueiros

# TODO



- [] Setup Airflow (terraform):
    - [] minimum setup with python operators
    - [] setup with kubernetes pods
    - [] setup with Ray work distribution
- [] Setup Minio for data storage (terraform)
- [] Setup Ray for distributed computing (terraform)
- [] Setup Mlflow for model versioning (terraform)
- [] Setup Prometheus+Grafana for monitoring (terraform)
- [] Build training pipeline: 
    - [] DAG with sensor for downloading h5ad (task), splitting data into chunks (task) and uploading unprocessed h5ad chunks to S3 (task)
    - [] DAG with sensor for download h5ad chunks (task), processing h5ad chunks (task), and uploading processed h5ad chunks to s3 (task)
    - [] DAG with sensor for reading processed h5ad chunks, training model from streamed chunks, and logging into Mlflow (task)
    - [] publish image with src code for all tasks
- [] define hardware with Ray
- [] define model-specific parameters, e.g., precision
- [] create grafana dashboards:
    - [] cadvisor for resources profiling
    - [] dag duration and counts



# NOTES

Im using ./helical/examples/run_models/run_geneformer.py as a template
Some references:

- for community edition airflow deployment (not being used): https://github.com/airflow-helm/charts

# Useful commands:

- Inspecting minikube:
```bahs
minikube ssh
```
- Get all pods:
```bash
kubectl get pods -n helical-pdqueiros 
```
- Inspecting a pod:
```bash
kubectl exec -it <pod-name> -n helical-pdqueiros -- /bin/bash
```
- Describing a pod: 
```bash
kubectl describe pod <pod-name> -n helical-pdqueiros
```
- Deleting a pod: 
```bash
kubectl delete pod <pod-name> -n helical-pdqueiros
```
- Restarting a pod:
```bash
kubectl rollout restart deployment <pod-name> -n helical-pdqueiros
```
- get chart default values, e.g., for airflow:
```bash
helm show values apache-airflow/airflow > default-values.yaml
```
You can use this to cross-reference against specific config/*.yaml

#####



# Docker deployment


Build images for Airflow, the Docker operators and Ray workers
```bash
# There's 4 images here, 1 for airflow with additional requirements, one for a basic Helical run, and 2 others for the Ray workers (cpu and gpu)
docker compose -f docker-compose--build.yaml build
```

```bash
source env.sh
# deploys mlflow and minio (for mlflow and "cloud" storage)
# recipe: https://github.com/mlflow/mlflow/tree/master/docker-compose
docker compose -f docker-compose-storage.yaml up -d
docker compose -f docker-compose-monitoring.yaml up -d
docker compose -f docker-compose-airflow.yaml up -d
```
This will deploy all basic services with docker, including:
- minio for S3 simulation and Mlflow storage
- postgres for Mlflow and Airflow
- Prometheus, Pushgateway, Cadvisor, Redis, Grafana, node-exporter, and otel-collector for monitoring. Otel-collector is used for Airflow monitoring, whereas the others are used for system and containers monitoring.




```bash
# starts a kubernetes
minikube start
# terraform ray deployment
terraform apply
# tunnel for Ray
kubectl port-forward service/helical-raycluster-head-svc -n helical-pdqueiros 8265:8265  10001:10001

```

Now wait for everything to be deployed








Tools used
- Amazon's [S3](https://eu-central-1.console.aws.amazon.com/s3) and Amazon's [ECR](https://eu-central-1.console.aws.amazon.com/ecr)
- Dagster for orchestration
- K8s for pod deployment and auto-scaling of dagster as pods (one pod per asset)
- Terraform for infrastructure creation

# TLDR, i.e., minikube+terraform

## Setup
1. Install [K8s](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
2. Install [Terraform](https://developer.hashicorp.com/terraform/install)
3. Install [minikube](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download). We are running minikube since we are deploying a k8s cluster locally.
4. **Create .env file with these values:**

```
# credentials
AWS_DEFAULT_REGION=
S3_ACCESS_KEY=
S3_SECRET_ACCESS_KEY=
S3_BUCKET=
```
I've included a `.env-template` you can just rename to `.env` and add yhour AWS credentials.
**After** this is done you can deploy:
5. Login to ECR so you can pull the latest image:
```bash
# if you haven't set the AWS credentials in your .bashrc file, you need to export them with:
source env.sh
# and then just login:
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
```


## Deployment


```bash
# I'm mounting my workspace to minikube so that I can mount the dags into my airflow pods. In a prod env you'd pull the dags from git instead. Make sure you use the mount and driver since we need them for sharing the Airflow DAGs
# minikube start --mount --mount-string="/home/pedroq/workspace:/host_workspace" --driver=docker
minikube start
# then start terraforming...
terraform init
# we do this due to a known issue with the CRD installation planning. So we force deployment first since other pods depend on it.
terraform apply -target=helm_release.kuberay_operator
terraform plan
terraform apply
```

If you want to update the chart versions just check the repos you have with `helm repo list` and check the respective repo, e.g., `helm search repo grafana`

To check pods status:
```bash
kubectl get pods --namespace helical-pdqueiros
```


### Dashboards

#### Minikube

```
# in another console you can check the dashboard with:
minikube dashboard --port=8081
```
You can then open the provided link, e.g.,: `http://127.0.0.1:8081/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/#/workloads?namespace=helical-pdqueiros`

**If you are checking the minikube dashboard, make sure you use the correct namespace, i.e., "helical-pdqueiros"**

Generally it will take some time for terraform to finish since it waits until all deployments are done

You can check all the pods via the console with: 
```
kubectl get pods --namespace helical-pdqueiros
```

#### Airflow

Create a tunnel via minikube to inspect the Airflow dashboard:
```
minikube service apache-airflow-api-server -n helical-pdqueiros
# or if you want to use a specific port:
kubectl port-forward service/apache-airflow-api-server -n helical-pdqueiros 8000:8080 
```

And then go to the port you specified or randomly assigned by minikube: `http://127.0.0.1:8000/`
I'm using the default user and password: admin and admin

### Ray

I've setup my Ray worker specs in `config/raycluster.yaml`; I've done so according to my local machine with 1 GPU (10GB nvidia RTX 3080) and 23 CPUs and 32GB RAM.

Create a tunnel via minikube to inspect the Ray dashboard:
```
kubectl port-forward service/helical-raycluster-head-svc -n helical-pdqueiros 8265:8265 6379:6379
```
Go to `http://127.0.0.1:8265/#/overview` to see the Ray dashboard.


## Destroy deployment

```bash
terraform destroy
# or for full deletion:
kubectl delete all --all -n helical-pdqueiros --force
kubectl delete namespace helical-pdqueiros --force
kubectl delete pv local-dags-pv --force
```

Redis tends to hang while shutting down. You can skip things up with:
```bash
kubectl delete pod apache-airflow-redis-0  --namespace helical-pdqueiros --force
```

You can do the same with other problematic sticky pods, they'll be restarted anyhow.




# Description

## Task description

Objective: Build a containerized workflow orchestration environment that launches and monitors Helical model executions using Dockerized Airflow.

The goal is to demonstrate your understanding of:

- Containerized environments and orchestration tools (Docker, Airflow)
- Scalable practices for large models and large datasets in computational biology

We’re not expecting a production-grade system — we care most about your approach, simplicity, and reasoning.

Requirements
1. Airflow Environment
    - Set up Apache Airflow in a Dockerized environment (you can use docker compose or your own setup and get started here).
    - Configure Airflow to run locally with a simple DAG that:
      1. Starts a Helical container (you can use the Helical Package)
      2. Mounts a local folder containing data (e.g., sample .h5ad files or any dataset of your choice).
      3. Executes a Helical model (e.g., one of the examples like Cell Type Annotation or Fine-Tuning).

The Airflow DAG should be visible and runnable from the Airflow web UI.


2. Containerization
    - Create a Dockerfile for the Helical environment:
      - The container should have Python, the Helical package, and any necessary dependencies installed.
      - Ensure that the container can execute a simple Helical command or script when started (e.g., a workflow that prints model metadata or runs a small inference task).
      - Ensure that the data folder is mounted correctly into the container during execution.


3. Scaling
To handle larger models and datasets efficiently, consider:
    - Memory: Stream or memory-map large .h5ad data instead of loading fully into RAM.
    - Batching strategy: Implement batched loading so models process data in smaller chunks.
    - Resource profiles: Define model-specific needs (GPU type, precision, memory cap) for smarter scheduling.
    - Precision: Use FP16/mixed precision or offloading to cut GPU memory usage.

4. Monitoring & Metrics
    - Add Prometheus and Grafana to your setup (can be via docker compose or separate containers).
    - Expose and visualize basic metrics such as:
      - Airflow task success/failure counts
      - Container resource usage (CPU/memory)
      - Workflow duration





# Workflow

## Sample data, and other info

- Sample [data](https://huggingface.co/datasets/helical-ai/yolksac_human)
- Sample [notebook](https://github.com/helicalAI/helical/blob/release/examples/notebooks/Cell-Type-Annotation.ipynb)
- [Airflow helm chart](https://github.com/airflow-helm/charts)

## General workflow

1. User adds data to S3 storage (via UI), but right now we do it manually through the AWS interface
2. When new data arrives, Airflow spawns a pod which then loads the model and processes the data
3. Processed data is stored
4. Metrics are exposed to Prometheus
5. Metrics are visualized in Grafana


![dagster_workflow](images/dagster_workflow.png)

```python
defs = Definitions(
    assets=[asset_bounding_box, asset_fields],
    jobs=[job_process_fields, job_process_bounding_boxes],
    sensors=[sensor_fields, sensor_bounding_boxes],
    resources={
        "s3_resource": s3_resource,
        "io_manager_fields": io_manager_fields,
        "io_manager_bounding_box": io_manager_bounding_box,
    },
)
```

![dagster_workflow](images/dagster.drawio.png)



The sensor for the fields has a few dependencies, as per the requirements:

- bounding box needs to be processed (currently by box id)
- previous field data is processed
- field date falls within partition start date

The bounding box processing has no dependencies.




## Data format



After processing, the flag `is_processed` is set to True.

Paths are equivalent in S3 and locally (but in locally, we store in the `tmp` folder)

```
/boxes/input/bounding_box_01976dbcbdb77dc4b9b61ba545503b77.jsonl
/boxes/output/bounding_box_01976dbcbdb77dc4b9b61ba545503b77.jsonl
fields/input/01976dbcbdb77dc4b9b61ba545503b77/fields_2025-06-02.jsonl
fields/output/01976dbcbdb77dc4b9b61ba545503b77/fields_2025-06-02.jsonl
```

These data types are implemented as data classes `src/helical_pdqueiros/services/core/documents/bounding_box_document.py` and `src/helical_pdqueiros/services/core/documents/field_document.py`. 
**Since we are not dong any real data transformations, I assume that fields are rectangular (similar to bounding boxes)**

## Dependencies testing

For dependencies testing you can remove some of the boxes/fields data from s3 and delete any past runs in the dagster UI. You can then upload the data files one by one and see how the dependencies are tracked in the sensors.


### Note on late data arrival

Regarding the complication describe above (i.e., adding fields data on different timepoints without reprocessing bounding boxes):
- Upload file to the correct S3 folder, e.g., fields/input/01976dbcbdb77dc4b9b61ba545503b77/fields_2025-06-02_THIS_IS_A_RANDOM_STRING.jsonl
- wait for sensor to check dependencies

Check `sensors.py/fields_dependencies_are_available` in sensors.py for an overview of how this works.

Keep in mind that we don't do any assets aggregation since this would depend on downstream business logic.



# Local deployment

The section below is mostly for development purposes; the only infra requirement we have is postgres, for that *make sure the postgres credentials match the ones found in the `dagster.yaml` file*

## Initial setup

1. Setup .env file

```
AWS_DEFAULT_REGION=
S3_ACCESS_KEY=
S3_SECRET_ACCESS_KEY=
S3_BUCKET=
```

1. Export environmental variables:

```bash
source env.sh
```


1. Deploy postgres:

```bash
docker compose -f docker-compose-infra.yaml up -d
```

If you can't bind to postgres, e.g., you get this error:

```bash
Error response from daemon: driver failed programming external connectivity on endpoint proma-postgres-1 (a484fad4f83094cb257ff159fde87c1c3c1cb6bf7e9ebf6fc84ecbfd99b003ca): Error starting userland proxy: listen tcp4 127.0.0.1:5432: bind: address already in use
```

You can run:

```bash
# assuming the port for postgres is 5432
sudo lsof -t -i:5432 | xargs sudo kill -9
```


2. Create S3 bucket if needed (same name as `S3_BUCKET`)

3. [Install UV](https://docs.astral.sh/uv/getting-started/installation/) (**recommended**) and activate your environment with:
*Keep in mind that the `activate.sh` command assumes you are using UV for enviorenment management, if you prefer use something else like venv, conda, mamba, etc*
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source activate.sh
```

4. Create test data and upload it to S3:
```bash
python tests/create_sample_data.py
```

5. Launch dagster dev:

```bash
# check definitions:
dg list defs
# run:
uv run --active dagster dev
```

6. Launch dagster-webserver:
```bash
dagster-webserver
```



# Deployment with minikube+helm

This section was the second develoment step, i.e., putting together the infrastructure. I've kept things simple by using Dagster's default helm chart with only the essential changes so that we can run the public image of this codebase.

## Tools installation

1. Install [K8s](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
2. Install [Helm](https://helm.sh/docs/intro/install/)
3. Install [Terraform](https://developer.hashicorp.com/terraform/install)
4. Install [minikube](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download). We are running minikube since we are deploying a k8s cluster locally.


## Docker image and tools deployment

1. Authenticate to Amazon ECR (this is the public registry I've set). This step is only needed if you need to modify the image.

```bash
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
# source code
docker compose build
docker tag helical-pdqueiros:latest public.ecr.aws/d8n7f1a1/helical_pdqueiros/helical_pdqueiros:latest
docker push public.ecr.aws/d8n7f1a1/helical_pdqueiros:latest
# airflow template code
docker compose -f docker-compose-airflow.yaml build
docker tag helical-pdqueiros-airflow:latest public.ecr.aws/d8n7f1a1/helical_pdqueiros_airflow:latest
docker push public.ecr.aws/d8n7f1a1/helical_pdqueiros_airflow:latest
```

You should see an image here:
https://eu-central-1.console.aws.amazon.com/ecr/repositories/public/996091555539/helical_pdqueiros?region=eu-central-1

2. Start minikube with:
```bash
# we need this insecure registry to loag the image from localhost
# see https://gist.github.com/trisberg/37c97b6cc53def9a3e38be6143786589
minikube start
# Check node status
kubectl get nodes
# you should get something like this: `minikube   Ready    control-plane   33s   v1.33.1`
# set kubectl alias 
alias kubectl="minikube kubectl --"
kubectl config use-context minikube
```

2. Start minikube dashboard
```bash
minikube dashboard
```


*The output of the image list should match with the service_image variable in `dagster-chart.yaml`* (see below)



```

# if the namespace does not exist
kubectl create namespace helical-pdqueiros
# create the secret with the necessary env vars (if it doesnt exist)
# make sure you always check the if you have the secret with 
kubectl describe secret helical-pdqueiros-secret -n helical-pdqueiros
# if you don't run the command below
kubectl create secret generic helical-pdqueiros-secret --from-env-file=.env -n helical-pdqueiros

# set minikube config 
kubectl config use-context minikube
# and check it
kubectl config view
kubectl config set-context minikube --namespace helical-pdqueiros --cluster minikube --user=helical-pdqueiros


# get dagster chart
helm repo add dagster https://dagster-io.github.io/helm
helm repo update
```

4. Add env variables as a K8s secret:
```bash
kubectl create secret generic helical-pdqueiros-secret --from-env-file=.env -n helical-pdqueiros
```







Now let's try with fields data:
![k8s_dashboard](images/fields_data.png)

You can see the job has run
![k8s_dashboard](images/fields_process_job_tags.png)


Congratulations for making it to the end! If you want a simplified versionn go back to the [top](#tldr-ie-minikubeterraform) and have fun with your deployed service.


# Future TODO

- Logs should be cleaned up and conflicts resolved, right now the Helical logger captures logs not sent to it. I'd also add more information on logging information, e.g., what I used for log formatting.
- Use different K8s namespaces, for now everything is in helical-pdqueiros for simplicity sake. But we could have one for airlfow, monitoring, ray, etc


# Known issues

1. Terraform apply Kuberay issues:
```
╷
│ Error: API did not recognize GroupVersionKind from manifest (CRD may not be installed)
│ 
│   with kubernetes_manifest.raycluster,
│   on kuberay.tf line 51, in resource "kubernetes_manifest" "raycluster":
│   51: resource "kubernetes_manifest" "raycluster" {
│ 
│ no matches for kind "RayCluster" in group "ray.io"
╵
```

When this happens you can:
```bash
# run this first to first install the kuberay CRD 
terraform apply -target=helm_release.kuberay_operator
# deploy the rest
terraform apply
```

2. Mounting issues. Sometimes minikube won't mount the volume correctly. If that happens, you can mount it manually with:
```bash
minikube mount "/home/pedroq/workspace:/host_workspace"
```