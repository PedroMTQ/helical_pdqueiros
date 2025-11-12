import logging
import os
from typing import Literal
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
import pendulum
from airflow.models.dag import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import DeviceRequest, Mount
from dotenv import dotenv_values
import uuid6
from airflow.sdk import Variable

IMAGE_NAME = 'helical-pdqueiros-cpu:latest'
IMAGE_NAME_GPU = 'helical-pdqueiros-gpu:latest'
CONTAINER_DATA_PATH = '/app/tmp'
LOCAL_DATA_PATH = '/home/pedroq/workspace/helical_pdqueiros/tmp'
ENV_FILE = '/app/.env'
logger = logging.getLogger(__name__)
EXPERIMENT_NAME = os.getenv('EXPERIMENT_NAME', 'cell_type_classification')
CUDA_DEVICE_ID = os.getenv('CUDA_DEVICE_ID', '')

ENV_CONFIG = dotenv_values(ENV_FILE)
BUCKET_NAME = ENV_CONFIG['HELICAL_S3_BUCKET']
SENSOR_TIMEOUT = int(ENV_CONFIG.get('SENSOR_TIMEOUT', '10'))

MINIO_CONNECTION = Variable.get('MINIO_CONNECTION')


def get_task(execution_type: Literal['split_data', 'process_data', 'fine_tune'], image_name: str, device_requests: list=None):
    command_to_run = f'helical_pdqueiros {execution_type}'
    # https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/_api/airflow/providers/docker/operators/docker/index.html
    container_id = uuid6.uuid7().hex
    return DockerOperator(
            task_id=f"run_helical_pdqueiros.{execution_type}",
            # I'd prefer to use run_id for traceability, but it has forbidden characters -> see this https://stackoverflow.com/questions/63138577/airflow-grab-and-sanitize-run-id-for-dockeroperator
            container_name=f'helical-pdqueiros.{execution_type}.{container_id}',
            image=image_name,
            mounts=[
                # https://docker-py.readthedocs.io/en/stable/api.html?highlight=mount#docker.types.Mount
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
    dag_id=f'{EXPERIMENT_NAME}.split_data',
    start_date=pendulum.datetime(2025, 1, 1),
    schedule='* * * * *',
    catchup=False,
    tags=["helical-pdqueiros", 'split_data'],
    ) as dag:
        sensor_key_with_regex = S3KeySensor(task_id="sensor_key_with_regex.split_data",
                                            # this is the connection ID we setup in the UI
                                            aws_conn_id=MINIO_CONNECTION,
                                            bucket_name=BUCKET_NAME,
                                            bucket_key=ENV_CONFIG['SENSOR__RAW_DATA_PATTERN'],
                                            timeout=SENSOR_TIMEOUT,
                                            use_regex=True)
        split_data_task = get_task(execution_type='split_data', image_name=IMAGE_NAME)
        sensor_key_with_regex >> split_data_task

with DAG(
    dag_id=f'{EXPERIMENT_NAME}.process_data',
    start_date=pendulum.datetime(2025, 1, 1),
    schedule='* * * * *',
    catchup=False,
    tags=["helical-pdqueiros", 'process_data'],
    ) as dag:
        sensor_key_with_regex = S3KeySensor(task_id="sensor_key_with_regex.process_data",
                                            aws_conn_id=MINIO_CONNECTION,
                                            bucket_name=BUCKET_NAME,
                                            bucket_key=ENV_CONFIG['SENSOR__CHUNKED_DATA_PATTERN'],
                                            timeout=SENSOR_TIMEOUT,
                                            use_regex=True)
        process_data_task = get_task(execution_type='process_data', image_name=IMAGE_NAME)
        sensor_key_with_regex >> process_data_task


with DAG(
    dag_id=f'{EXPERIMENT_NAME}.model_fine_tuning',
    start_date=pendulum.datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["helical-pdqueiros", 'fine_tuning'],
    ) as dag:
        fine_tune_task = get_task(execution_type='fine_tune',
                                  image_name=IMAGE_NAME_GPU,
                                  device_requests=[DeviceRequest(capabilities=[['gpu']], device_ids=['0'])])

