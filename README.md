# helical-pdqueiros

# TODO



- [x] Setup Airflow (terraform):
    - [x] minimum setup with python operators
    - [x] setup with kubernetes pods
    - [x] setup with Ray work distribution
- [x] Setup Minio for data storage (terraform)
- [] Setup Ray for distributed computing (terraform)
- [x] Setup Mlflow for model versioning (terraform)
- [x] Setup Prometheus+Grafana for monitoring (terraform)
- [] Build training pipeline: 
    - [x] DAG with sensor for downloading h5ad (task), splitting data into chunks (task) and uploading unprocessed h5ad chunks to S3 (task)
    - [x] DAG with sensor for download h5ad chunks (task), processing h5ad chunks (task), and uploading processed h5ad chunks to s3 (task)
    - [x] read processed h5ad chunks, training model from streamed chunks, and logging into Mlflow (task)
    - [x] publish image with src code for all tasks
    - [] add Ray distributed work execution
- [x] define hardware with Ray
- [x] define model-specific parameters, e.g., precision
- [x] create grafana dashboards:
    - [x] cadvisor for resources profiling
    - [x] dag duration
    - [] dag counts



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


## Workflow template

I'm using this example from Helical-AI as [template](./helical/examples/run_models/run_geneformer.py) for the general workflow of this repo.



# Setup

### Base requirements

You need to have these installed on your machine:
- Install [Docker](https://docs.docker.com/engine/install/)
- Install [cuda](https://docs.nvidia.com/cuda/wsl-user-guide/index.html#cuda-support-for-wsl-2)


### GPU setup

I assume you have a system with a GPU, if not I would avoid running the fine-tuning step describe below.


If you are using WSL via a Windows sytem with a GPU install [Docker desktop](https://docs.docker.com/desktop/features/gpu/) for a straightforward way to enable GPU support on your docker engine.
Eiher way, you can test if yuor GPU(s) are available by running this:
```bash
docker run --rm -it --gpus=all nvcr.io/nvidia/k8s/cuda-sample:nbody nbody -gpu -benchmark
```
You should see something like this:
```bash
> Compute 8.6 CUDA device: [NVIDIA GeForce RTX 3080]
69632 bodies, total time for 10 iterations: 54.144 ms
= 895.504 billion interactions per second
= 17910.074 single-precision GFLOP/s at 20 flops per interaction
```

### Terraform and local cluster environment setup

These are optional, and you only need them if you want to use Ray for distributed computing:
- Install [Helm](https://helm.sh/docs/intro/install/)
- Install [K8s](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
- Install [Terraform](https://developer.hashicorp.com/terraform/install)
- Install [minikube](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download)


## Docker deployment

Below you will find the instructions to setup all the necessary requirements to run Airflow and respective DAGs required for fine-tuning a Geneformer for cell type annotation.

**Note that I've included a `.env` file which contains all the necessary environmental variables for setting up your containers**

To get started with deploying the necessary containers follow these steps:
```bash
# we are using a custom Airflow image since we need open telemetry and docker operators
docker compose -f docker-compose-build.yaml build helical-pdqueiros-airflow
docker compose -f docker-compose-storage.yaml up -d
docker compose -f docker-compose-monitoring.yaml up -d
docker compose -f docker-compose-airflow.yaml up -d
```

This will deploy all basic services with docker, including:
- minio for S3 simulation and Mlflow storage
- postgres for Mlflow and Airflow. Note that I used the base docker compose file from [Airflow](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html); you could also deploy Airflow via [Terraform](https://github.com/airflow-helm/charts). To avoid exposing the host's docker.sock I'm also deploying a proxy (docker-socket-proxy) as explained [here](https://github.com/benjcabalona1029/DockerOperator-Airflow-Container/tree/master) and [here](https://medium.com/@benjcabalonajr_56579/using-docker-operator-on-airflow-running-inside-a-docker-container-7df5286daaa5).
- Prometheus, Pushgateway, Cadvisor, Redis, Grafana, node-exporter, and otel-collector for monitoring. Otel-collector is used for Airflow monitoring, whereas the others are used for system and containers monitoring.

Make sure you have all these containers:
```bash
IMAGE                                              NAMES                                       STATUS
helical-pdqueiros-airflow:latest                   helical_pdqueiros-airflow-worker-1          Up 4 minutes (healthy)
helical-pdqueiros-airflow:latest                   helical_pdqueiros-airflow-apiserver-1       Up 4 minutes (healthy)
helical-pdqueiros-airflow:latest                   helical_pdqueiros-airflow-dag-processor-1   Up 4 minutes (healthy)
helical-pdqueiros-airflow:latest                   helical_pdqueiros-airflow-triggerer-1       Up 4 minutes (healthy)
helical-pdqueiros-airflow:latest                   helical_pdqueiros-airflow-scheduler-1       Up 4 minutes (healthy)
postgres:16                                        postgres-airflow                            Up 5 minutes (healthy)
redis:7.2-bookworm                                 redis-airflow                               Up 5 minutes (healthy)
tecnativa/docker-socket-proxy:v0.4.1               airflow-docker-socket                       Up 5 minutes
grafana/grafana-oss                                monitoring-grafana                          Up 5 minutes
prom/prometheus:latest                             monitoring-prometheus                       Up 5 minutes
gcr.io/cadvisor/cadvisor:latest                    monitoring-cadvisor                         Up 5 minutes (healthy)
otel/opentelemetry-collector-contrib               monitoring-otel-collector                   Up 5 minutes
quay.io/prometheus/node-exporter:latest            monitoring-node-exporter                    Up 5 minutes
prom/pushgateway                                   monitoring-pushgateway                      Up 5 minutes
redis:latest                                       redis-monitoring                            Up 5 minutes
ghcr.io/mlflow/mlflow:latest                       storage-mlflow-server                       Up 5 minutes (healthy)
postgres:16.4-bullseye                             postgres-mlflow                             Up 5 minutes (healthy)
quay.io/minio/minio:RELEASE.2025-01-20T14-49-07Z   storage-minio                               Up 5 minutes (healthy)
```

The main tools here (i.e., that you actually might interact with) are : Airflow, Grafana, Mlflow, and Minio. All others are containers that are "supporting" these tools.

Now that you are done deploying the services, you can now build the images for the containers that will be deployed by Airflow via Docker operators. There's 2 versions here, `helical-pdqueiros-cpu` is a small image that contains some CPU-only requirements, whereas `helical-pdqueiros-gpu` contains all the requirements for running the actual fine-tuning. You likely could further trim the GPU image but for the sake of keeping it simpler, I've used Helical-AI's Dockerfile as a template.

```bash
docker compose -f docker-compose-build.yaml build helical-pdqueiros-cpu
docker compose -f docker-compose-build.yaml build helical-pdqueiros-gpu
```

This image contains all my source code as well as Helical's package (among a few other dependencies).

You should end up with these images:
```bash
REPOSITORY                             TAG                            IMAGE ID       CREATED          SIZE
helical-pdqueiros-cpu                  latest                         2a6c2dd3244a   6 minutes ago    3.87GB
helical-pdqueiros-gpu                  latest                         b064f44875c6   37 minutes ago   20.8GB
helical-pdqueiros-airflow              latest                         bb0a6e2e764c   56 minutes ago   2.92GB
```
Notice how helical-pdqueiros-cpu and helical-pdqueiros-gpu have such different sizes, and would therefore be faster to build, pull, and deploy allowing for faster development iterations.
(*I would further split the helical package into groups*)

Assuming everything was deployed correctly, you should now have access to all the necessary services and you can check their respective dashboards at:

- [Minio](http://localhost:9001) (credentials: minio/minio123)
- [Mlflow](http://localhost:5000)
- [Grafana](http://localhost:3000/login) (credentials: admin/admin)
- [Airflow](http://localhost:8080/) (credentials: airflow/airflow)
- [Prometheus](http://localhost:9090/)


When you access the [Minio](http://localhost:9001) dashboard, you should see 2 buckets: `helical` and `mlflow`; the `helical` bucket is where you will load your test data, which I've included in `tests/test_data.h5ad`.

In [Airflow](http://localhost:8080/) you will see these DAGs:

![airflow-dags](./images/airflow-dags.png)


If you open [Grafana](http://localhost:3000/login) you will have multiple dashboards, this one among them where you can track system resources and Airflow runs.
Note that the [ti_success](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/metrics.html) metric is not being exposed. This is apparently fixed in this [issue](https://github.com/apache/airflow/issues/52336), but I'm still having issues with a lack of metrics




# Workflow


As per Helical-AI's example [notebook](https://github.com/helicalAI/helical/blob/release/examples/notebooks/Cell-Type-Annotation.ipynb) I've used this [dataset](https://huggingface.co/datasets/helical-ai/yolksac_human) for the Geneformer fine-tuning.

## General workflow

I've designed this pipeline in 4 major steps: 
1. User or an automated process uploads training data to a staging area (for example to an S3 bucket).
2. When new data arrives, a Dag is triggered (as a POC I didn't include a schedule interval) which [split](#data-splitting) the data into chunks
3. These [chunks are processed](#data-processing) across multiple containers (if you set it up in that manner using K8s or Ray).
4. A model is [fine-tuned](#model-fine-tuning) and the respective experiment is logged into Mlflow. Note that this last step should be triggered manually or with a large enough schedule interval as model training is quite expensive and something you want to monitor.


Below you can find the underlying logic for each step (3-5). These were first created as Jobs for development and then deployed as Airflow Docker operators.

### Data splitting


```python

class SplitDataJob():
    def _run(self):
        downloaded_files : list[str] = self.task.download_data_to_split()
        if not downloaded_files:
            return
        chunked_files : list[str] = self.task.split_data()
        uploaded_files : list[str] = self.task.upload_chunked_files(list_files=chunked_files)
        archived_files: list[str] = self.task.archive_raw_data(list_files=downloaded_files)

```

### Data processing

```python
class ProcessDataJob():
    def run(self):
        downloaded_files : list[str] = self.task.download_data_to_process()
        if not downloaded_files:
            return
        processed_files: list[str] = self.task.process_data()
        deleted_files: list[str] = self.task.delete_chunked_files(list_files=downloaded_files)
        uploaded_files: list[str] = self.task.upload_processed_files(list_files=processed_files)
```

### Model fine-tuning

```python
class FineTuneJob():
    def _run(self):
        downloaded_files : list[str] = self.task.download_data_to_fine_tune()
        if not downloaded_files:
            return
        uncompressed_files: list[str] = self.task.uncompress_data(list_files=downloaded_files)
        fine_tuning_files: list[str] = self.task.fine_tune(list_files=uncompressed_files)
        archived_files: list[str] = self.task.archive_processed_data()
```


Below I've described how you can run these pipelines locally, and I also went through the underlying logic of each step, so even if you don't intend to do local testing, you ought to go through the following section anyhow.


## Local testing

You can test your DAGs locally without Airflow by running each job outside of Airflow, since in essence Airflow is merely providing scheduling and observability and all the business logic is within the `src` code.
Keep in mind that I'm using [UV](https://docs.astral.sh/uv/getting-started/installation/) for environment management, which you can install with:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After you install UV, you can run the following commands:
```bash
# creates the uv environment
source activate.sh
# sets up the environmental variables
source env.sh
```

After you run this, you should be able to run:
```bash
helical_pdqueiros -h
```

Now, load some data into the `helical` bucket in [Minio](http://localhost:9001). I've included some sample data in `tests/`. Just drag and drop the whole `training_data` folder into [Minio](http://localhost:9001), like so:
![minio-sample-data-1](./images/minio-sample-data-1.png)

You can then see the sample data in this path:

![minio-sample-data-2](./images/minio-sample-data-2.png)

**Keep in mind that the name of the file is irrelevant (i.e., `sample_dataset`), HOWEVER the path (i.e., `helical/training_data/cell_type_classification/raw_data`) and extension `.h5ad`) of the files need to be respected!**

Then run these commands to download all the necessary data. This is a fix to an issue within Helical's runtime download, which I assume will be resolved in the future.
```bash
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/gene_median_dictionary.pkl
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/token_dictionary.pkl
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/ensembl_mapping_dict.pkl
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/${MODEL_NAME}/config.json
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/${MODEL_NAME}/training_args.bin
```

Afterwards, run the workflow in this order:
```bash
helical_pdqueiros split_data
```
After you run this, you will see 2 new folders within Minio `minio:helical/training_data/cell_type_classification/archived_raw_data` and `minio:helical/training_data/cell_type_classification/chunked_data`. The former contains your initial raw data, which is archived in case the pipeline needs to be run again, the latter contains the chunks of the initial data, which have been split to allow for distributed processing of the data.

```bash
helical_pdqueiros process_data
```
Now you can run the data processing, which will pick up a certain amount of chunks (i.e., `PROCESSING_CHUNKS_LIMIT`, 2 by default), process them and store them into `minio:helical/training_data/cell_type_classification/processed_data`. The idea of having a `PROCESSING_CHUNKS_LIMIT` variable is to allow for distributed computing, i.e., each DAG run picks up a certain number of chunks, and processes them in a distributed manner.
Note that each chunk is compressed after the data is processed to reduce disk storage overhead.

```bash
helical_pdqueiros fine_tune
```
Now, the final step is the model fine-tuning. I'm using `gf-6L-10M-i2048` as the default since it's one of the smaller models.
This pipeline will take all the recently processed data in `minio:helical/training_data/cell_type_classification/processed_data` and fine tune the `gf-6L-10M-i2048` model. This data will then be archived in `minio:helical/training_data/cell_type_classification/archived_processed_data` since I assume that it could be re-used for future runs of this pipeline. The idea here being that the downstream user adds new data, processes it, and then wants to use all of their (both new and archived) to fine-tune the initial model.

*You should see this message `'gf-6L-10M-i2048' model is in 'eval' mode, on device 'cuda' with embedding mode 'cell'.` when running this pipeline; if you are not running GPU fine-tuning this pipeline will take quite a while.*

You will also find the model logged into Mlflow, as shown below:

![mlflow-model](./images/mlflow-model-1.png)
![mlflow-model](./images/mlflow-model-2.png)

Note that I'm logging the model (for experiment purposes) but not registering it, as you would do for serving the model. You could register it with :
```bash
model_uri = f"runs:/{run.info.run_id}/sklearn-model"
mv = mlflow.register_model(model_uri, "RandomForestRegressionModel")
```

And that's the end of the pipeline. Later on the end-user could download the model from Mlflow and use it for classifying their data.



### Airflow testing

For your reference this is how these DAGs are setup:
```python

def get_task(execution_type: Literal['split_data', 'process_data', 'fine_tune'], image_name: str, device_requests: list=None):
    command_to_run = f'helical_pdqueiros {execution_type}'
    # https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/_api/airflow/providers/docker/operators/docker/index.html
    return DockerOperator(
            task_id=f"run_helical_pdqueiros.{execution_type}",
            container_name=f'helical-pdqueiros.{execution_type}',
            image=image_name,
            mounts=[
                # We don't really need this mount since everything is hosted on MinIO (which is what you'd do in a distributed system). Anyhow, you can check the data flowing through the /tmp/ folder
                Mount(source=LOCAL_DATA_PATH, target=CONTAINER_DATA_PATH, type='bind', read_only=False)
                    ],
            command=command_to_run,
            private_environment  = dotenv_values(ENV_FILE),
            api_version='1.51',
            # api_version='auto',
            network_mode="helical-network",
            auto_remove='force',
            # for docker in docker (tecnativa/docker-socket-proxy:v0.4.1) -> https://github.com/benjcabalona1029/DockerOperator-Airflow-Container/tree/master
            mount_tmp_dir=False,
            docker_url="tcp://airflow-docker-socket:2375",
            device_requests=device_requests,
        )

with DAG(
    dag_id=f'{EXPERIMENT_NAME}.data_processing',
    start_date=pendulum.datetime(2025, 1, 1),
    # schedule='0 * * * *',
    catchup=False,
    tags=["helical-pdqueiros", 'data_processing'],
    ) as dag:
        split_data_task = get_task(execution_type='split_data', image_name=IMAGE_NAME)
        process_data_task = get_task(execution_type='process_data', image_name=IMAGE_NAME)
        split_data_task >> process_data_task

with DAG(
    dag_id=f'{EXPERIMENT_NAME}.model_fine_tuning',
    start_date=pendulum.datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["helical-pdqueiros", 'fine_tuning'],
    ) as dag:
        fine_tune_task = get_task(execution_type='fine_tune',
                                  image_name=IMAGE_NAME_GPU,
                                  # I only have one GPU, but you could use more
                                  device_requests=[DeviceRequest(capabilities=[['gpu']], device_ids=['0'])])
```

Now you can try the same in Airflow:

As you can see below, the DAG process data first split the data and then processes it, both via Docker Operators. 

![airflow-dags](./images/dag-process-data.png)

And then another DAG can be triggered to fine-tune the model training.
Notice that since we had the `DeviceRequest` defined in our DockerOperator, the fine-tuning was done with using my local GPU (highlighted `cuda`). Similar to the local run, a model experimented is also logged into MLFlow.


![airflow-dags](./images/dag-fine-tune.png)



## Ray and K8s deployment


Now, let's move on to the deployment of Ray, which as a POC, was done through Terraform. I have some other terraform deployments in `terraform`, but for the purpose of this exercise, I've only finalized Ray's terraform file `kuberay.tf`. The former terraform files *should* work but haven't been fully tested. For the airflow.tf you are probably better off using the community [charts](https://github.com/airflow-helm/charts).

Anyhow, moving on to the Ray's deployment.

```bash
# starts kubernetes
minikube start
```

You then need to build the images that the Ray workers will use. We will only build the image for the ray-cpu as this is the only pipeline where Ray was integrated; the same could be done (and should) for distributed model training.

```bash
eval $(minikube -p minikube docker-env)
# now build:
docker compose -f docker-compose-build.yaml build helical-pdqueiros-ray-cpu
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


##\ Shutting down and deleting everything

Shutting everything down

```bash
terraform destroy
minikube stop
docker compose -f docker-compose-storage.yaml down
docker compose -f docker-compose-monitoring.yaml down
docker compose -f docker-compose-airflow.yaml down
```







### Minikube dashboard

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


### Ray dashboard

I've setup my Ray worker specs in `config/raycluster.yaml`; I've done so according to my local machine with 1 GPU (10GB nvidia RTX 3080) and 23 CPUs and 32GB RAM.

Create a tunnel via minikube to inspect the Ray dashboard:
```bash
# 8265 for the dashboard, 10001 for the ray cluster
kubectl port-forward service/helical-raycluster-head-svc -n helical-pdqueiros 8265:8265 10001:10001
```
Go to `http://127.0.0.1:8265/#/overview` to see the Ray dashboard.

### Airflow with Terraform

If you deployed Airflow via Terraform you need to create a tunnel between your system and minikube. The idea is the same as with Ray.

Create a tunnel via minikube to inspect the Airflow dashboard:
```bash
kubectl port-forward service/apache-airflow-api-server -n helical-pdqueiros 8000:8080 
```

And then go to the port you specified or randomly assigned by minikube: `http://127.0.0.1:8000/`



### Destroy deployment

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




# Known issues

- Terraform apply Kuberay issues:
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

- If you have issues starting the docker operators due to this error:
```bash
HTTPError: 400 Client Error: Bad Request for url: http://airflow-docker-socket:2375/v1.51/containers/96fe8a3b85832292c1e456c20504c3f18e0190dcb31fefe33149ee0fee8db640/start
```
A docker or system reboot will fix the issue.

- `FileNotFoundError: [Errno 2] No such file or directory: '/home/pedroq/.cache/helical/models/geneformer/v1/gene_median_dictionary.pkl'` If you get this error, run these commands:
```bash
source env.sh
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/gene_median_dictionary.pkl
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/token_dictionary.pkl
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/ensembl_mapping_dict.pkl
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/${MODEL_NAME}/config.json
wget -P ${HOME}/.cache/helical/models/geneformer/v1/ https://helicalpackage.s3.eu-west-2.amazonaws.com/${MODEL_TYPE}/${MODEL_VERSION}/${MODEL_NAME}/training_args.bin
```

# Useful commands and other info

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

- [Setting up docker.sock for Airflow DockerOperators](https://github.com/benjcabalona1029/DockerOperator-Airflow-Container/blob/master/docker-compose.yaml)
- [Airflow config](https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html#config-metrics)
- [Airflow metrics](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/metrics.html)

# TODO

Repo todo:
- add GPU profiling
- add Ray-gpu training
- improve metrics dashboard and add metrics storage (maybe redis) and push to pushgateway (already deployed). You could do more interesting metrics besides counting DAGs, e.g., track model metrics over time, track amount of files/data points processed, check longitudinal data distribution, etc. The main problem here is that DAGs are ephemeral and so you'd need a way to archive the metrics. I've used Redis in the past for this and it's a rather easy solution. For example: service publishes to permanent collector using Redis for messaging; collector collects current metrics from Redis and updates values, and pushes to prometheus using pushgateway.
- improve model scaling (there's a lot of new tools that could be useful for acceleration). I'd need to do some more research on that end.
- I've setup everything to be in the same docker network, but it could be better separated 
- I didn't follow any security measures, since this was done for prototyping, obviously don't use this repo in a production environment
- I'd split the processes into multiple images, the data splitting and processing could be done via a very light image with minimal requirements.
- Find a way to retrieve data/xcom through the DockerOperators, which at the moment is not possible the containers are terminated automatically (as intended). In any case, using something like Redis would like be preferrable (and easy). 
- Find a way to deal with orphan containers generated via docker operator. If you stop your DAG midway, this will happen:
```bash
APIError: 409 Client Error for http://airflow-docker-socket:2375/v1.51/containers/create?name=helical-pdqueiros.fine_tune: Conflict ("Conflict. The container name "/helical-pdqueiros.fine_tune" is already in use by container "1b410b96c8adeeba7241c252bfdf7cff1b038cce6535a8d736d6b4293566d91c". You have to remove (or rename) that container to be able to reuse that name.")
```
- I had some issues downloading the necessary data from AWS (e.g., `gene_median_dictionary.pkl`). I'm not sure why, when I `exec` into the container, I can download them via wget and through helical. But through the DockerOperator, Helical's download method always fails. To avoid that, I baked these files into the image, which  anyway is a better practice to make sure the image is truly static and requires no external data (remember what happened during the AWS outage?).


Helical todo:
- fix logging (it's consuming too much and leading to weird behaviour)
- clean up code in models
- add accelerator to some of the models
- migrate to hugging face trainer; not sure how feasible it is since some models have some specific internal behaviour
- Add UV installation and dependencies grouping (both very easy wins). The base pyproject is way too large, e.g.:
    - dependency group for data processing
    - dependency group per model -> I imagine you also run into compability issues quite often
- Improve file path management
- There's some weird behaviour in the data downloading, both locally and within containers. This seems to work when you download the data using `wget` but I think the runtime downloading function is not working properly.
```bash
Traceback (most recent call last):
  File "/home/pedroq/envs/helical_pdqueiros/lib/python3.11/site-packages/decorator.py", line 235, in fun
    return caller(func, *(extras + args), **kw)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/pedroq/envs/helical_pdqueiros/lib/python3.11/site-packages/retry/api.py", line 73, in retry_decorator
    return __retry_internal(partial(f, *args, **kwargs), exceptions, tries, delay, max_delay, backoff, jitter,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/pedroq/envs/helical_pdqueiros/lib/python3.11/site-packages/retry/api.py", line 33, in __retry_internal
    return f()
           ^^^
  File "/home/pedroq/personal/helical_pdqueiros/src/helical_pdqueiros/core/cell_type_annotation/data_processer.py", line 30, in __init__
    self.tokenizer = TranscriptomeTokenizer(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/pedroq/envs/helical_pdqueiros/lib/python3.11/site-packages/helical/models/geneformer/geneformer_tokenizer.py", line 256, in __init__
    with open(gene_median_file, "rb") as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/pedroq/.cache/helical/models/geneformer/v1/gene_median_dictionary.pkl'
```
