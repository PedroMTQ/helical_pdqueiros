import logging
import sys

from helical_pdqueiros.settings import DEBUG, SERVICE_NAME

# this doesns't work, there's something wrong with Helical's logger, it's consuming all logs
LOGGER = logging.getLogger(SERVICE_NAME)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s")

if DEBUG:
    LOGGER.setLevel(logging.DEBUG)
else:
    LOGGER.setLevel(logging.INFO)

local_handler = logging.StreamHandler(sys.stdout)
local_handler.setLevel(logging.DEBUG)
local_handler.setFormatter(formatter)

LOGGER.addHandler(local_handler)

