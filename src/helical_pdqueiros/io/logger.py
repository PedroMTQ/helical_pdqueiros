from helical_pdqueiros.settings import SERVICE_NAME, DEBUG
import logging
import sys

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

def setup_logger(logger):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s")
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    local_handler = logging.StreamHandler(sys.stdout)
    local_handler.setLevel(logging.DEBUG)
    local_handler.setFormatter(formatter)

    logger.addHandler(local_handler)
