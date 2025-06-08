from pathlib import Path
import logging
from ..utils.path_utils import safe_copy


class ImageCollector:
    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger(self.__class__.__name__)

    def copy(self, src: Path):
        dst = safe_copy(src, self.cfg.TEMP1_DIR)
        self.logger.debug("Image copied → %s", dst)