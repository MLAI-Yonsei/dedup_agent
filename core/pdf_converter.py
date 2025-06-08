import logging
from pathlib import Path
import pymupdf as fitz  # PyMuPDF 바인딩 (import fitz 로도 사용 가능)

from ..utils.path_utils import safe_move  # 필요 시 사용, 현재는 직접 저장

class PdfConverter:
    """주어진 PDF 파일을 각 페이지별 PNG로 저장해 TEMP1_DIR 에 배치."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger(self.__class__.__name__)

    def convert(self, pdf_path: Path):
        self.logger.info("Converting PDF → images: %s", pdf_path)
        doc = fitz.open(pdf_path)
        for page in doc:
            pix = page.get_pixmap()
            out_path = self.cfg.TEMP1_DIR / f"{pdf_path.stem}_p{page.number + 1}.png"
            pix.save(out_path)
            self.logger.debug("Saved: %s", out_path)