import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Reduce noise from third-party libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)

logger = logging.getLogger("alternate_history")
