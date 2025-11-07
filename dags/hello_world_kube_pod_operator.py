from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG('hello_world_k8s', default_args=default_args, schedule='* * * * *') as dag:
    hello_world_task = KubernetesPodOperator(
        task_id="hello_world_and_sleep_kube_pod_operator",
        namespace="default",
        image="busybox",
        cmds=["/bin/sh", "-c"],
        arguments=[
            # The actual commands to execute: echo, then sleep, then echo again.
            "echo 'Hello World, I am about to sleep!'; sleep 60; echo 'I woke up after 60 seconds!'"
        ],
        name="hello-world-pod",
        get_logs=True,
        is_delete_operator_pod=True,
    )
