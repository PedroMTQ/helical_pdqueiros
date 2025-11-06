import mlflow


def get_latest_run_id_mlflow(model_name:str, experiment_name: str, stage_name: str)-> str | None:
    '''
    returns the latest run ID for a given model name and experiment name, filtered by the specific stage name (usually <Production>)
    can return either the latest run ID or None, is no run ID is found
    '''
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        raise ValueError(f"Experiment <{experiment_name}> not found.")
    experiment_id = experiment.experiment_id
    versions = mlflow.search_model_versions(filter_string=f"name='{model_name}'")
    versions.sort(key=lambda vs: int(vs.version), reverse=True)
    if versions:
        for v in versions:
            run_id = v.run_id
            run_info = client.get_run(run_id)
            # default value of STAGE_NAME is Production to back to the previous version of model set Staging
            if run_info.info.experiment_id == experiment_id and v.current_stage == stage_name:
                return run_id
    raise ValueError(f"Run ID for experiment <{experiment_name}>, model name <{model_name}> and stage <{stage_name}> not found...")


class MlflowClient():
    '''
    Client for Mlflow:
     - checks latest model version
     - downloads model form mlflow
     - saves model in mlflow
    '''
