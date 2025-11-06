from helical_pdqueiros.settings import CODE_VERSION, SERVICE_NAME, DEBUG
import logging
import sys

logger = logging.getLogger(SERVICE_NAME)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s")

if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

local_handler = logging.StreamHandler(sys.stdout)
local_handler.setLevel(logging.DEBUG)
local_handler.setFormatter(formatter)

logger.addHandler(local_handler)

