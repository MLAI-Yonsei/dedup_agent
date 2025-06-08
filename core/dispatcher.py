import logging
from pathlib import Path
from typing import Iterable

from .text_collector import TextCollector
from .pdf_converter import PdfConverter
from .image_collector import ImageCollector
from ..utils.progress import progress_bar


class Dispatcher:
    SUPPORTED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff"}

    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger(self.__class__.__name__)
        self.txt_collector = TextCollector(cfg)
        self.pdf_converter = PdfConverter(cfg)
        self.img_collector = ImageCollector(cfg)

    def run(self, input_dir: Path):
        files: Iterable[Path] = input_dir.rglob("*.*")
        with progress_bar(files, desc="Dispatching") as pbar:
            for fp in pbar:
                if fp.suffix.lower() == ".txt":
                    self.txt_collector.copy(fp)
                elif fp.suffix.lower() == ".pdf":
                    self.pdf_converter.convert(fp)
                elif fp.suffix.lower() in self.SUPPORTED_IMAGE_EXT:
                    self.img_collector.copy(fp)
                else:
                    self.logger.warning("Unsupported file skipped: %s", fp)