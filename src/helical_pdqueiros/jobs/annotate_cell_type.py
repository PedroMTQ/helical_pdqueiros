
import logging
import warnings
from datasets import load_dataset
from helical.models.geneformer import Geneformer, GeneformerConfig
import torch
from helical.utils import get_anndata_from_hf_dataset
import tempfile
import os



# dataset = load_dataset("helical-ai/yolksac_human", split="train[:10%]", trust_remote_code=True, download_mode="reuse_cache_if_exists")
# labels = dataset["LVL1"]



# ann_data = get_anndata_from_hf_dataset(dataset)
# print(ann_data)

device = "cuda" if torch.cuda.is_available() else "cpu"
model_config = GeneformerConfig(batch_size=10,device=device)
geneformer = Geneformer(configurer=model_config)

print(geneformer)

MODEL_NAME = os.getenv('MODEL_NAME', 'gf-12L-38M-i4096')
EMBEDDING_MODE = os.getenv('EMBEDDING_MODE', 'cell')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '24'))
NPROC = int(os.getenv('NPROC', '1'))

import mlflow


class CellTypeAnnotationGeneformerTraining():

    def __repr__(self):
        return f'{self.__class__.__name__}:{self.config}'


    def save_model():
        pass

    def load_model():
        '''
        loads model from Mlflow:
            - model exists
        '''
        pass

    def load_model():
        pass


    @classmethod
    def to_mlflow(cls, ctranslate2_model_path, max_input_len: int, max_target_len: int):
        """This method should only be used once the mt5 model has been converted to ct2 and saved locally.
        Then, we save the locally saved ct2 model to MLFlow.

        'max_input_len' and 'max_target_len' are the settings used to train the mt5 model
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            tokenizer_path = os.path.join(tmpdir, "tokenizer")
            MT5TokenizerSingleton().tokenizer.save_pretrained(tokenizer_path)

            config_path = os.path.join(tmpdir, "config.json")
            config = {
                "max_input_len": max_input_len,
                "max_target_len": max_target_len,
            }
            with open(config_path, "w") as f:
                json.dump(config, f)

            mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
            with mlflow.start_run():
                mlflow.pyfunc.log_model(
                    artifact_path="model",
                    python_model=cls(),
                    artifacts={"model": ctranslate2_model_path,
                               "tokenizer": tokenizer_path,
                               "config": config_path},
                    registered_model_name=cls.MLFLOW_MODEL_NAME,
                    conda_env=None,
                )

if __name__ == '__main__':
    pass