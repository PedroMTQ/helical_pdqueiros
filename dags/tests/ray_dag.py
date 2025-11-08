"""
## Ray Tutorial

This tutorial demonstrates how to use the Ray provider in Airflow to parallelize
a task using Ray.
"""

from airflow.sdk import dag, task
from ray_provider.decorators import ray
from airflow.models import Variable
import logging

logger = logging.getLogger(__name__)

RAY_CONNECTION_ID = Variable.get('RAY_CONNECTION_ID')
logger.info(f'Using ray connection: {RAY_CONNECTION_ID}')


RAY_TASK_CONFIG = {
    "conn_id": RAY_CONNECTION_ID,
    "num_cpus": 1,
    "num_gpus": 0,
    "memory": 0,
    "poll_interval": 5,
}


@dag(doc_md=__doc__)
def ray_example_dag():

    @task
    def generate_data() -> list:
        """
        Generate sample data
        Returns:
            list: List of integers
        """
        import random

        return [random.randint(1, 100) for _ in range(10)]

    # use the @ray.task decorator to parallelize the task
    @ray.task(config=RAY_TASK_CONFIG)
    def get_mean_squared_value(data: list) -> float:
        """
        Get the mean squared value from a list of integers
        Args:
            data (list): List of integers
        Returns:
            float: Mean value of the list
        """
        import numpy as np
        import ray

        @ray.remote
        def square(x: int) -> int:
            """
            Square a number
            Args:
                x (int): Number to square
            Returns:
                int: Squared number
            """
            return x**2

        ray.init()
        data = np.array(data)
        futures = [square.remote(x) for x in data]
        results = ray.get(futures)
        mean = np.mean(results)
        print(f"Mean squared value: {mean}")

    data = generate_data()
    get_mean_squared_value(data)


ray_example_dag()
