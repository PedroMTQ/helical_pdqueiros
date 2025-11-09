
from helical.models.base_models import HelicalBaseFoundationModel
from helical_pdqueiros.settings import MODELS, CUDA_DEVICE
from helical_pdqueiros.io.mlflow_client import MlflowClient
from abc import abstractmethod
import os
import mlflow
from typing import Any

import logging
from helical_pdqueiros.io.logger import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

class AbstractModel():
    '''
    This is an abstract model which a client could inherit from and use to load/save into their own Mlflow server
    '''
    def __init__(self):
        self.mflow_client = MlflowClient()
        self.__wrap_functions()

    @abstractmethod
    def train(self):
        pass

    def __wrap_functions(self):
        self.train = self.__train_wrapper('train')

    def __train_wrapper(self, func):
        def wrapped(*args, **kwargs):
            try:

                if self.mflow_client._is_connected:
                    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
                    with mlflow.start_run():
                        mlflow.pyfunc.log_model(
                            artifact_path="model",
                            python_model=self,
                            artifacts={"model": ctranslate2_model_path,
                                    "tokenizer": tokenizer_path,
                                    "config": config_path},
                            registered_model_name=cls.MLFLOW_MODEL_NAME,
                            conda_env=None,
                        )

                res = func(*args, **kwargs)
                return res
            except Exception as e:
                raise e
        return wrapped

    def __repr__(self):
        return f'{self.__class__.__name__}:{self.config}'

    @classmethod
    def load(cls, model_config_settings: dict):
        '''
        loads model from Mlflow:
            - model exists
        '''
        try:
            return cls.from_mlflow(model=cls.model,
                                   model_config=cls.model_config,
                                   model_config_settings=model_config_settings)
        except Exception as e:
            logger.debug(f'Failed to load model {cls} from Mlflow due to {e}')
        logger.info(f'Loading model {cls.__class__.__name__} from Helical base model')
        return cls.from_base(model_config_settings=model_config_settings)


    @classmethod
    def from_mlflow(cls):
        raise Exception

    @classmethod
    def from_base(cls, model_config_settings: dict):
        """
        Parameters
        ----------
        model : HelicalBaseFoundationModel
            The Helical model
        model_config : HelicalBaseConfig
            The resspective class for the provided Helical model
        model_config_settings : dict
            The settings for the HelicalBaseFoundationModel model
        """
        # TODO model_config should also have a HelicalBaseFoundationModels
        model_config_settings['device'] = model_config_settings.get('device', CUDA_DEVICE)
        return cls.model(configurer=cls.model_config(**model_config_settings))




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
    # model_config = GeneformerConfig(batch_size=10,device=device)
    # base_model = Geneformer(configurer=model_config)
    print(CellTypeAnnotationGeneformerAbstractModel())

