import importlib.metadata
import torch
import os
from pathlib import Path

SERVICE_NAME = 'helical_pdqueiros'
CODE_VERSION = importlib.metadata.version(SERVICE_NAME)

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
TEMP = os.path.join(ROOT, 'tmp')
LOCAL_DATA = os.path.join(TEMP, 'data')
MODELS = os.path.join(TEMP, 'models')
TESTS = os.path.join(ROOT, 'tests')

DEBUG = int(os.getenv('DEBUG', '0'))

# AWS
HELICAL_S3_BUCKET = os.getenv('HELICAL_S3_BUCKET')
S3_DATE_REGEX = os.getenv('S3_DATE_REGEX')
DATE_FORMAT = os.getenv('DATE_FORMAT')

MINIO_HOST = os.getenv('MINIO_HOST')
MINIO_PORT = os.getenv('MINIO_PORT')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')

RETRY_LIMIT = int(os.getenv('RETRY_LIMIT', '100'))


CUDA_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# parent folder for model training data
TRAINING_DATA_PATH = os.getenv('TRAINING_DATA', 'training_data')
# where incoming data arrives
ARCHIVED_RAW_DATA_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('ARCHIVED_RAW_DATA', 'archived_raw_data'))
RAW_DATA_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('RAW_DATA', 'raw_data'))
RAW_DATA_ERROR_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('RAW_DATA_ERROR', 'raw_data_error'))
# where chunked data is stored
CHUNKED_DATA_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('CHUNKED_DATA', 'chunked_data'))
CHUNKED_DATA_ERROR_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('CHUNKED_DATA_ERROR', 'chunked_data_error'))
# where chunked processed data is stored
PROCESSED_DATA_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('PROCESSED_DATA', 'processed_data'))
PROCESSED_DATA_ERROR_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('PROCESSED_DATA_ERROR', 'processed_data_error'))


LOCAL_TRAINING_DATA_PATH = os.path.join(LOCAL_DATA, TRAINING_DATA_PATH)
LOCAL_RAW_DATA_PATH = os.path.join(LOCAL_DATA, RAW_DATA_PATH)
LOCAL_CHUNKED_DATA_PATH = os.path.join(LOCAL_DATA, CHUNKED_DATA_PATH)
LOCAL_PROCESSED_DATA_PATH = os.path.join(LOCAL_DATA, PROCESSED_DATA_PATH)


for folder_path in [TEMP, LOCAL_DATA, MODELS, LOCAL_TRAINING_DATA_PATH, LOCAL_RAW_DATA_PATH, LOCAL_CHUNKED_DATA_PATH, LOCAL_PROCESSED_DATA_PATH]:
    Path(folder_path).mkdir(parents=True, exist_ok=True)


H5AD_PATTERN = '(.*\.h5ad)$'
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))
