from pathlib import Path
import logging
from typing import Dict
from datetime import datetime
import shutil

from .minicpm_wrapper import MiniCPMWrapper
from .mineru_wrapper import MinerUWrapper
from ..utils.path_utils import safe_move
from ..utils.progress import progress_bar


class ImageCleaner:
    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger(self.__class__.__name__)
        self.minicpm = MiniCPMWrapper(cfg)
        self.mineru = MinerUWrapper(cfg)

    def _run_minicpm(self, dir_path: Path) -> Dict[Path, str]:
        preds = {}
        with progress_bar(list(dir_path.glob("*")), desc="MiniCPM") as pbar:
            for img in pbar:
                label = self.minicpm.predict(img)
                preds[img] = label
        return preds

    def _move(self, files, dst_dir):
        for f in files:
            safe_move(f, dst_dir)

    def _save_texts(self, texts: list[str]) -> None:
        """추출된 텍스트들을 고유한 파일명으로 저장합니다."""
        if not texts:
            return
        
        self.logger.info(f"Saving {len(texts)} extracted text snippets.")
        for idx, txt in enumerate(texts):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            txt_path = self.cfg.TEXT_TEMP_DIR / f"mineru_{ts}_{idx}.txt"
            txt_path.write_text(txt, encoding="utf-8")
    
    def _run_mineru_and_cleanup(self, files_to_parse: list[Path]) -> list[Path]:
        """[수정됨] 디렉토리 단위로 MinerU를 실행하고, 원본 파일을 삭제한 뒤 결과를 반환합니다."""
        if not files_to_parse:
            return []

        # 1. MinerU용 임시 디렉토리 초기화
        in_dir, out_dir = self.cfg.MINERU_INPUT_DIR, self.cfg.MINERU_OUTPUT_DIR
        if in_dir.exists():
            shutil.rmtree(in_dir)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        in_dir.mkdir()
        out_dir.mkdir()

        # 2. mixed 파일들을 임시 입력 디렉토리로 복사
        with progress_bar(files_to_parse, desc="Copying mixed files for MinerU") as pbar:
            for f in pbar:
                shutil.copy(f, in_dir / f.name)

        # 3. 디렉토리 단위로 MinerU 실행 및 결과 수집
        all_subs = self.mineru.parse_dir(in_dir, out_dir)
        
        # 4. 파싱이 완료된 원본 mixed 파일들 삭제
        for f in files_to_parse:
            f.unlink()
        
        return all_subs

    def run(self, first_temp: Path):
        # --- 1차 처리 (TEMP1) ---
        self.logger.info("--- MiniCPM Pass-1 on %s ---", first_temp.name)
        preds1 = self._run_minicpm(first_temp)
        pure_files1 = [p for p, t in preds1.items() if t == "pure"]
        mixed_files1 = [p for p, t in preds1.items() if t == "mixed"]
        self.logger.info(f"Pass-1 Result: Pure={len(pure_files1)}, Mixed={len(mixed_files1)}")

        self._move(pure_files1, self.cfg.IMAGE_FINAL_DIR)
        
        if not mixed_files1:
            self.logger.info("No mixed files in Pass-1. Finishing.")
            return

        subs1 = self._run_mineru_and_cleanup(mixed_files1)

        if not subs1:
            self.logger.info("MinerU produced no sub-images in Pass-1. Finishing.")
            return

        # --- 2차 처리 (TEMP2) ---
        # 다음 처리를 위해 하위 이미지들을 TEMP2로 이동
        self._move(subs1, self.cfg.TEMP2_DIR)
        
        self.logger.info("--- MiniCPM Pass-2 on %s ---", self.cfg.TEMP2_DIR.name)
        preds2 = self._run_minicpm(self.cfg.TEMP2_DIR)
        pure_files2 = [p for p, t in preds2.items() if t == "pure"]
        mixed_files2 = [p for p, t in preds2.items() if t == "mixed"]
        self.logger.info(f"Pass-2 Result: Pure={len(pure_files2)}, Mixed={len(mixed_files2)}")
        
        self._move(pure_files2, self.cfg.IMAGE_FINAL_DIR)
        
        if not mixed_files2:
            self.logger.info("No mixed files in Pass-2. Finishing.")
            return

        subs2 = self._run_mineru_and_cleanup(mixed_files2)
        
        # 2차 파싱에서 나온 최종 하위 이미지는 바로 최종 목적지로 이동
        self.logger.info("Moving %d sub-images from Pass-2 to final destination.", len(subs2))
        self._move(subs2, self.cfg.IMAGE_FINAL_DIR)