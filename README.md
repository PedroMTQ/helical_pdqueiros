# helical-pdqueiros

# TODO



- [x] Setup Airflow (terraform):
    - [x] minimum setup with python operators
    - [x] setup with kubernetes pods
    - [] setup with Ray work distribution
- [x] Setup Minio for data storage (terraform)
- [] Setup Ray for distributed computing (terraform)
- [x] Setup Mlflow for model versioning (terraform)
- [x] Setup Prometheus+Grafana for monitoring (terraform)
- [] Build training pipeline: 
    - [x] DAG with sensor for downloading h5ad (task), splitting data into chunks (task) and uploading unprocessed h5ad chunks to S3 (task)
    - [x] DAG with sensor for download h5ad chunks (task), processing h5ad chunks (task), and uploading processed h5ad chunks to s3 (task)
    - [] DAG with sensor for reading processed h5ad chunks, training model from streamed chunks, and logging into Mlflow (task)
    - [] publish image with src code for all tasks
- [x] define hardware with Ray
- [] define model-specific parameters, e.g., precision
- [] create grafana dashboards:
    - [x] cadvisor for resources profiling
    - [] dag duration and counts



# Task description

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



I'm using this example as [template](./helical/examples/run_models/run_geneformer.py) for my code.



# Setup

1. Install [Docker](https://docs.docker.com/engine/install/)
2. Install [K8s](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
3. Install [Terraform](https://developer.hashicorp.com/terraform/install)
4. Install [minikube](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download). We are running minikube since we are deploying a k8s cluster locally.


## Deployment

```bash
# deploys mlflow and minio (for mlflow and "cloud" storage)
# recipe: https://github.com/mlflow/mlflow/tree/master/docker-compose
docker compose -f docker-compose-storage.yaml up -d
docker compose -f docker-compose-monitoring.yaml up -d
docker compose -f docker-compose-airflow.yaml up -d
```

This will deploy all basic services with docker, including:
- minio for S3 simulation and Mlflow storage
- postgres for Mlflow and Airflow. Note that I used the base docker compose file from [Airflow](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html); you could also deploy Airflow via [Terraform](https://github.com/airflow-helm/charts).
- Prometheus, Pushgateway, Cadvisor, Redis, Grafana, node-exporter, and otel-collector for monitoring. Otel-collector is used for Airflow monitoring, whereas the others are used for system and containers monitoring.

Make sure you have all these containers:
```bash
CONTAINER ID   IMAGE                                              COMMAND                   CREATED             STATUS                 PORTS                                                                                                                                                                                                                                                                             NAMES
d6316072a006   gcr.io/k8s-minikube/kicbase:v0.0.47                "/usr/local/bin/entr…"    About an hour ago   Up About an hour       127.0.0.1:32783->22/tcp, 127.0.0.1:32784->2376/tcp, 127.0.0.1:32785->5000/tcp, 127.0.0.1:32786->8443/tcp, 127.0.0.1:32787->32443/tcp                                                                                                                                              minikube
ea40b08255f0   helical-pdqueiros-airflow:latest                   "/usr/bin/dumb-init …"    2 hours ago         Up 2 hours (healthy)   8080/tcp                                                                                                                                                                                                                                                                          helical_pdqueiros-airflow-worker-1
d85fe5b302a3   helical-pdqueiros-airflow:latest                   "/usr/bin/dumb-init …"    2 hours ago         Up 2 hours (healthy)   8080/tcp                                                                                                                                                                                                                                                                          helical_pdqueiros-airflow-triggerer-1
867173977c0b   helical-pdqueiros-airflow:latest                   "/usr/bin/dumb-init …"    2 hours ago         Up 2 hours (healthy)   0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp                                                                                                                                                                                                                                       helical_pdqueiros-airflow-apiserver-1
b57ca0cfd404   helical-pdqueiros-airflow:latest                   "/usr/bin/dumb-init …"    2 hours ago         Up 2 hours (healthy)   8080/tcp                                                                                                                                                                                                                                                                          helical_pdqueiros-airflow-dag-processor-1
29423e8635f7   helical-pdqueiros-airflow:latest                   "/usr/bin/dumb-init …"    2 hours ago         Up 2 hours (healthy)   8080/tcp                                                                                                                                                                                                                                                                          helical_pdqueiros-airflow-scheduler-1
24f7e5dd7595   redis:7.2-bookworm                                 "docker-entrypoint.s…"    2 hours ago         Up 2 hours (healthy)   6379/tcp                                                                                                                                                                                                                                                                          airflow-redis
e819e6ec47fe   postgres:16                                        "docker-entrypoint.s…"    2 hours ago         Up 2 hours (healthy)   5432/tcp                                                                                                                                                                                                                                                                          airflow-postgres
bf2517f2e8e3   ghcr.io/mlflow/mlflow:latest                       "/bin/bash -c '\n  pi…"   6 hours ago         Up 2 hours (healthy)   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp                                                                                                                                                                                                                                       storage-mlflow-server
afe59b44bb40   quay.io/minio/minio:RELEASE.2025-01-20T14-49-07Z   "/usr/bin/docker-ent…"    6 hours ago         Up 2 hours (healthy)   0.0.0.0:9000-9001->9000-9001/tcp, [::]:9000-9001->9000-9001/tcp                                                                                                                                                                                                                   storage-minio
09007724462f   grafana/grafana-oss                                "/run.sh"                 10 hours ago        Up 2 hours             0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp                                                                                                                                                                                                                                       monitoring-grafana
5f55669c0b09   prom/prometheus:latest                             "/bin/prometheus --w…"    10 hours ago        Up 2 hours             0.0.0.0:9090->9090/tcp, [::]:9090->9090/tcp                                                                                                                                                                                                                                       monitoring-prometheus
a415c7abb3c7   gcr.io/cadvisor/cadvisor:latest                    "/usr/bin/cadvisor -…"    10 hours ago        Up 2 hours (healthy)   0.0.0.0:8082->8080/tcp, [::]:8082->8080/tcp                                                                                                                                                                                                                                       monitoring-cadvisor
785a952c2a62   quay.io/prometheus/node-exporter:latest            "/bin/node_exporter …"    10 hours ago        Up 2 hours             0.0.0.0:9100->9100/tcp, [::]:9100->9100/tcp                                                                                                                                                                                                                                       monitoring-node-exporter
6565d3faf8a1   prom/pushgateway                                   "/bin/pushgateway"        10 hours ago        Up 2 hours             0.0.0.0:9091->9091/tcp, [::]:9091->9091/tcp                                                                                                                                                                                                                                       monitoring-pushgateway
58a3a583e8fd   otel/opentelemetry-collector-contrib               "/otelcol-contrib --…"    10 hours ago        Up 2 hours             0.0.0.0:1888->1888/tcp, [::]:1888->1888/tcp, 0.0.0.0:4317-4318->4317-4318/tcp, [::]:4317-4318->4317-4318/tcp, 0.0.0.0:8888-8889->8888-8889/tcp, [::]:8888-8889->8888-8889/tcp, 0.0.0.0:13133->13133/tcp, [::]:13133->13133/tcp, 0.0.0.0:55679->55679/tcp, [::]:55679->55679/tcp   monitoring-otel-collector

```


Build the image for Airflow and respective Docker operators:
```bash
docker compose -f docker-compose-build.yaml build helical-pdqueiros-airflow helical-pdqueiros
```
This image contains all my source code as well as Helical's package (among a few other dependencies)

Now, let's move on to the deployment of Ray, which as a POC, was done through Terraform. I have some other terraform deployments in `terraform`, but for the purpose of this exercise, I've only finalized Ray's terraform file `kuberay.tf`. The former terraform files *should* work but haven't been fully tested. For the airflow.tf you are probably better off using the community [charts](https://github.com/airflow-helm/charts).

Anyhow, moving on to the Ray's deployment.

```bash
# starts kubernetes
minikube start
```

You then need to build the images that the Ray workers will use. To do so do, this:
```bash
# There's 4 images here, 1 for airflow with additional requirements, one for a basic Helical run, and 2 others for the Ray workers (cpu and gpu)
eval $(minikube -p minikube docker-env)
# now build:
docker compose -f docker-compose-build.yaml build helical-pdqueiros-ray-cpu helical-pdqueiros-ray-gpu
# Check that the images are available with:
minikube image ls
```

These images are quite large so it might take a while. Ideally you would publish these images to something like ECR or another docker image registry.

If you have access to ECR you can this like so:
```bash
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
# source code
docker compose build
# for example:
docker tag helical-pdqueiros:latest public.ecr.aws/d8n7f1a1/helical_pdqueiros/helical_pdqueiros:latest
docker push public.ecr.aws/d8n7f1a1/helical_pdqueiros:latest
```

Keep in mind that [Amazon's](https://eu-central-1.console.aws.amazon.com/s3) [ECR](https://eu-central-1.console.aws.amazon.com/ecr) is not free, although you do some have free storage (at the time of writing it is 50GB). For prototyping purposes you are better off just building the images straight into Minikube, developing and publishing later on.


If minikube starts and the images are available, you are all set to start using Ray!

You can then start Kuberay with:

```bash
# terraform ray deployment
terraform apply
# tunnel for Ray
kubectl port-forward service/helical-raycluster-head-svc -n helical-pdqueiros 8265:8265 10001:10001
```

This will deploy multiple pods, including 1 worker as defined in `helical_pdqueiros/config/raycluster.yaml`. You can customize this file according to your system.
Notice that in `helical_pdqueiros/config/raycluster.yaml` we are using the images we built in the step above in each worker, the `*-cpu` image for the head and CPU workers, and the `*-gpu` image for the GPU worker.


If you get this error when running `terraform apply`:
```bash

│ Error: API did not recognize GroupVersionKind from manifest (CRD may not be installed)
│ 
│   with kubernetes_manifest.raycluster,
│   on kuberay.tf line 81, in resource "kubernetes_manifest" "raycluster":
│   81: resource "kubernetes_manifest" "raycluster" {
│ 
│ no matches for kind "RayCluster" in group "ray.io"
```
Run this first:
```bash
terraform apply -target=helm_release.kuberay_operator
```

And then you can run everything else as usual, i.e., `terraform apply`.

Make sure you all the pods running:
```bash
NAME                                               READY   STATUS    RESTARTS   AGE
helical-raycluster-cpu-worker-group-worker-kd8cp   1/1     Running   0          29s
helical-raycluster-head-gsjnx                      1/1     Running   0          69s
kuberay-apiserver-c6bc7f7c4-824ps                  2/2     Running   0          11m
kuberay-operator-6c8f855d77-8ghhz                  1/1     Running   0          12m

```


## Shutting down and deleting everything

Shutting everything down

```bash
terraform destroy
minikube stop
docker compose -f docker-compose-storage.yaml down
docker compose -f docker-compose-monitoring.yaml down
docker compose -f docker-compose-airflow.yaml down
```




# Dashboards

List of dashboards when deployed through Docker:

- [Minio](http://localhost:9001) (minio/minio123)
- [Mlflow](http://localhost:5000)
- [Grafana](http://localhost:3000/login) (admin/admin)
- [Airflow](http://localhost:8080/) (admin/admin)
- [Prometheus](http://localhost:9090/)


## Minikube

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


## Ray

I've setup my Ray worker specs in `config/raycluster.yaml`; I've done so according to my local machine with 1 GPU (10GB nvidia RTX 3080) and 23 CPUs and 32GB RAM.

Create a tunnel via minikube to inspect the Ray dashboard:
```bash
# 8265 for the dashboard, 10001 for the ray cluster
kubectl port-forward service/helical-raycluster-head-svc -n helical-pdqueiros 8265:8265 10001:10001
```
Go to `http://127.0.0.1:8265/#/overview` to see the Ray dashboard.

## Airflow with Terraform

If you deployed Airflow via Terraform you need to create a tunnel between your system and minikube. The idea is the same as with Ray.

Create a tunnel via minikube to inspect the Airflow dashboard:
```bash
kubectl port-forward service/apache-airflow-api-server -n helical-pdqueiros 8000:8080 
```

And then go to the port you specified or randomly assigned by minikube: `http://127.0.0.1:8000/`






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




# Workflow

## Sample data, and other info

- Sample [data](https://huggingface.co/datasets/helical-ai/yolksac_human)
- Sample [notebook](https://github.com/helicalAI/helical/blob/release/examples/notebooks/Cell-Type-Annotation.ipynb)

## General workflow

1. User adds data to S3 storage (via UI)
2. When new data arrives, Airflow spawns a pod which then loads the model and processes the data
3. Data is [split](#data-splitting)
4. Data is [processed](#data-processing)
5. Model is [fine-tuned](#model-fine-tuning) and logged into Mlflow

During these steps you have metrics being logged to Prometheus as well, which you can visualize in Grafana.


Below you can find the underlying logic for each step (3-5). These were first created as Jobs for development and then deployed as Airflow Docker operators.

### Data splitting


```python

class SplitDataJob():
    def run(self):
        task = SplitData()
        downloaded_files : list[str] = task.download_data_to_split()
        if not downloaded_files:
            return
        chunked_files: list[str] = task.split_data()
        uploaded_files = task.upload_chunked_files(list_files=chunked_files)
        archived_files = task.archive_raw_data(list_files=downloaded_files)
```

### Data processing

```python
class ProcessDataJob():
    def run(self):
        task = ProcessData()
        downloaded_files : list[str] = task.download_data_to_process()
        if not downloaded_files:
            return
        processed_files: list[str] = task.process_data()
        deleted_files: list[str] = task.delete_chunked_files(list_files=downloaded_files)
        uploaded_files: list[str] = task.upload_processed_files(list_files=processed_files)
```

### Model fine-tuning

```python

```

Note that in each step we have a sensor step `task.download_data_to_process()` which will trigger downstream steps




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


# Useful commands

These are some commands I've used during development; you don't necessarily need them, these are just some references for myself.

- Inspecting minikube:
```bash
minikube ssh
```
- Using Minikube's docker:
```bash
eval $(minikube -p minikube docker-env)
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
- Delete a namespace:
```bash
kubectl delete namespace helical-pdqueiros
```
- Restarting a pod:
```bash
kubectl rollout restart deployment <pod-name> -n helical-pdqueiros
```
- get chart default values, e.g., for airflow:
```bash
helm show values apache-airflow/airflow > default-values.yaml
```
- check Helm repos:
```bash
helm repo list
```
- check chart releases
```bash
# e.g., for grafana
helm search repo grafana
```


# TODO

- fix logging
- clean up code ein models
- add accelerator to some of the models
- migrate to hugging face trainer; not sure how feasible it is since some models have some specific internal behaviour