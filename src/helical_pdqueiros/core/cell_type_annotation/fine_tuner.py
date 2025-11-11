



import logging
import os

import mlflow
import torch
from datasets import concatenate_datasets, load_from_disk
from helical.models.geneformer import GeneformerConfig, GeneformerFineTuningModel

from helical_pdqueiros.io.logger import setup_logger
from helical_pdqueiros.settings import (
    CUDA_DEVICE,
    DATASET_LABEL_NAME,
    MLFLOW_TRACKING_URI,
    MODEL_NAME,
    TRAINING_BATCH_SIZE,
)

logger = logging.getLogger(__name__)
setup_logger(logger)

MLFLOW_EXPERIMENT_NAME = os.getenv('MLFLOW_EXPERIMENT_NAME', "Geneformer_CellType_Classification")
EPOCHS = int(os.getenv('EPOCHS', "2"))
NUM_PROC = int(os.getenv('NUM_PROC', '3'))



# Example execution (uncomment to run)

class CellTypeAnnotationFineTuner():
    '''

        decompresss datasets
        load multiple hugging face datasets in a memory efficient manner
        merge datasets into one dataset using concatenate_datasets
        extract the set of all labels in this merged dataset
        apply the fine tuning logic from above
        log the model into mlflow
    '''


    @staticmethod
    def label_to_id(data_point: dict[str, int], labels_mapping: dict) -> dict[str, int]:
        data_point[DATASET_LABEL_NAME] = labels_mapping[data_point[DATASET_LABEL_NAME]]
        return data_point

    @staticmethod
    def run(chunk_paths: list[str]) -> bool:
        if not chunk_paths:
            return False
        try:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            tracking_uri = mlflow.get_tracking_uri()
            logger.info(f"Current Mlflow tracking uri: {tracking_uri} with experiment name: {MLFLOW_EXPERIMENT_NAME}")
            # This shouldn't be necessary, but for some reason I'm getting mlflow.exceptions.RestException: RESOURCE_DOES_NOT_EXIST: No Experiment with id=1 exists if I don't initially create it. This should be handled by set_experiment automatically. Maybe it's a recent bug?
            try:
                mlflow.create_experiment(name=MLFLOW_EXPERIMENT_NAME)
            except Exception:
                pass
            mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
            geneformer_config = GeneformerConfig(model_name=MODEL_NAME, batch_size=TRAINING_BATCH_SIZE, device=CUDA_DEVICE)
            logger.info(f'GeneformerConfig: {geneformer_config.config}')
            with mlflow.start_run(run_name=f"FineTune_{MODEL_NAME}_E{EPOCHS}") as run:
                mlflow.log_param("model_name", geneformer_config.config.get('model_name'))
                mlflow.log_param("geneformer_config", geneformer_config.config)
                mlflow.log_param("epochs", EPOCHS)
                mlflow.log_param("batch_size", TRAINING_BATCH_SIZE)
                # Merge datasets (memory-efficient as it mainly links the underlying Arrow files)
                logger.info(f'Preparing data from these chunks: {chunk_paths}')
                merged_dataset = concatenate_datasets([load_from_disk(dataset_path) for dataset_path in chunk_paths])
                logger.info(f"Merged dataset Size: {len(merged_dataset)} cells.")
                labels_set = merged_dataset.unique(DATASET_LABEL_NAME)
                # Create a dictionary to map cell types (strings) to IDs (integers)
                sorted_labels = sorted(list(labels_set))
                labels_mapping: dict[str, int] = {label: idx for idx, label in enumerate(sorted_labels)}
                merged_dataset = merged_dataset.map(function=CellTypeAnnotationFineTuner.label_to_id,
                                                    fn_kwargs={'labels_mapping': labels_mapping},
                                                    num_proc=NUM_PROC)
                logger.info("Initializing Geneformer Model and Fine-Tuning...")
                geneformer_fine_tune = GeneformerFineTuningModel(geneformer_config=geneformer_config,
                                                                fine_tuning_head="classification",
                                                                output_size=len(labels_set)
                                                                )
                # TODO we need to use Hugging's face accelerator, but this is a bit too much for this exercise
                if torch.cuda.is_bf16_supported():
                    geneformer_fine_tune.model.to(torch.bfloat16)
                else:
                    geneformer_fine_tune.model.to(torch.float16)
                geneformer_fine_tune.train(train_dataset=merged_dataset, label=DATASET_LABEL_NAME, epochs=EPOCHS)

                logger.info("Logging model to MLflow...")
                # this needs to be better logged
                try:
                    mlflow.pytorch.log_model(pytorch_model=geneformer_fine_tune,
                                            name="geneformer_fine_tuned_model",
                                            )
                    logger.info(f"MLflow Run completed. View results at: {mlflow.get_tracking_uri()}/#/experiments/{mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME).experiment_id}/runs/{run.info.run_id}")
                except Exception as e:
                    logger.error(f'Failed to log model to Mlflow due to {e}')
                return True
        except Exception as e:
            logger.exception(f'Failed to fine-tune model due to {e}')
            return False


if __name__ == '__main__':
    task = CellTypeAnnotationFineTuner()
    file_path = '/home/pedroq/workspace/helical_pdqueiros/tests/training_data/cell_type_classification/processed_data/dataset__019a6a0765d1741489cb692a479e7d91.dataset'
    task.run(chunk_paths=[file_path])
