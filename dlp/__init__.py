import logging
import sys

logging.basicConfig(
    level=logging.INFO, 
    handlers=[
        logging.StreamHandler(sys.stdout)  
    ]
)

logger = logging.getLogger(__name__)