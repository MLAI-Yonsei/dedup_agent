import argparse
from pathlib import Path
import logging
import os

# HuggingFace Tokenizer의 병렬 처리 비활성화 (fork 경고 방지)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from .config import Config, ensure_dirs
from .logging_conf import setup_logging
from .core.dispatcher import Dispatcher
from .postproc.image_cleaner import ImageCleaner
from .dedup.text_unisim import TextUnisim
from .dedup.image_fiftyone import ImageFiftyOne
from .utils.path_utils import cleanup_temp_dirs


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("input_dir", type=Path, help="원본 디렉터리")
    return p.parse_args()


def main():
    args = parse_args()
    cfg = Config()
    ensure_dirs(cfg)
    setup_logging(cfg)
    logger = logging.getLogger("MAIN")

    logger.info("=== Stage 1: Dispatch ===")
    Dispatcher(cfg).run(args.input_dir)

    logger.info("=== Stage 2: Image Cleaning ===")
    ImageCleaner(cfg).run(cfg.TEMP1_DIR)

    logger.info("=== Stage 3: Deduplication ===")
    logger.info("--- Running Text Deduplication ---")
    TextUnisim(cfg).run()
    logger.info("--- Running Image Deduplication ---")
    ImageFiftyOne(cfg).run()

    logger.info("=== Stage 4: Cleanup ===")
    cleanup_temp_dirs(cfg)
    
    logger.info("Pipeline finished.")


if __name__ == "__main__":
    main()