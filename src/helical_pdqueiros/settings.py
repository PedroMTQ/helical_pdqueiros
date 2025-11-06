import importlib.metadata
import torch
import os

SERVICE_NAME = 'helical_pdqueiros'
CODE_VERSION = importlib.metadata.version(SERVICE_NAME)

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
DATA = os.path.join(ROOT, 'data')
MODELS = os.path.join(DATA, 'models')
TEMP = os.path.join(ROOT, 'tmp')
TESTS = os.path.join(ROOT, 'tests')

DEBUG = int(os.getenv('DEBUG', '0'))

# AWS
S3_BUCKET = os.getenv('S3_BUCKET')
S3_DATE_REGEX = os.getenv('S3_DATE_REGEX')
DATE_FORMAT = os.getenv('DATE_FORMAT')

AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

RETRY_LIMIT = int(os.getenv('RETRY_LIMIT', '100'))


CUDA_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# parent folder for model training data
TRAINING_DATA_PATH = os.getenv('TRAINING_DATA', 'training_data')
# where incoming data arrives
RAW_DATA_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('RAW_DATA', 'raw_data'))
# where batched data is stored
CHUNKED_DATA_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('CHUNKED_DATA_PATH', 'chunked_data'))
# where batched and processed data is stored
PROCESSED_DATA_PATH = os.path.join(TRAINING_DATA_PATH, os.getenv('PROCESSED_DATA', 'processed_data'))

H5AD_PATTERN = '(\.h5ad)$'
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))
