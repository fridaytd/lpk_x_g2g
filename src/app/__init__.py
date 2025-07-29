import logging

from .shared.config import Config
from .shared.stores import ModelKeyValueStore
from .paths import SRC_PATH
from .shared.models import LpkStoreModel, EliStoreModel

## Seting logger
# Configure logging once at the application level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s :: %(message)s",
    handlers=[logging.StreamHandler()],
)

# Get logger for this module
logger = logging.getLogger(__name__)


config = Config.from_env()

kv_store = ModelKeyValueStore(
    name="order_mapping",
    save_dir=SRC_PATH / "data" / "store",
    model=LpkStoreModel,
)

eli_kv_store = ModelKeyValueStore(
    name="eli_order_mapping",
    save_dir=SRC_PATH / "data" / "store",
    model=EliStoreModel,
)


__all__ = ["config", "logger", "kv_store", "eli_kv_store"]
