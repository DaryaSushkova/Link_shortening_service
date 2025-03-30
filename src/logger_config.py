import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,  # или INFO, если не нужен DEBUG
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) 
    ]
)

logger = logging.getLogger("shortener")