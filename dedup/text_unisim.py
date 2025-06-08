import logging
from pathlib import Path
import pandas as pd
import shutil
from itertools import chain

try:
    from unisim import TextSim
except ImportError as e:
    raise RuntimeError("UniSim not installed. Please run 'pip install unisim'.") from e

from ..utils.progress import progress_bar


class TextUnisim:
    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger(self.__class__.__name__)
        self.in_dir = self.cfg.TEXT_TEMP_DIR
        self.out_dir = self.cfg.TEXT_DEDUP_DIR
        self.report_path = self.cfg.WORK_DIR / "text_dedup_report.csv"

    def run(self):
        self.logger.info("Starting text deduplication...")
        files = sorted(self.in_dir.glob("*.txt"))
        if not files:
            self.logger.warning("No text files found to deduplicate.")
            return

        # 1. 텍스트 로딩
        records = self._load_texts(files)
        if not records:
            self.logger.error("No text files could be read. Aborting.")
            return
        df = pd.DataFrame(records)

        # 2. 중복 판별
        kept_paths, dup_map = self._deduplicate(df)
        dup_paths = set(dup_map.keys())
        all_paths = {str(f) for f in files}
        
        # 경로가 아닌 파일 이름만 로깅
        self.logger.info(f"Total: {len(all_paths)}, Kept: {len(kept_paths)}, Duplicates: {len(dup_paths)}")

        # 3. 고유 파일 복사
        self.out_dir.mkdir(parents=True, exist_ok=True)
        with progress_bar(kept_paths, desc="Copying unique files") as pbar:
            for p_str in pbar:
                shutil.copy2(p_str, self.out_dir / Path(p_str).name)
        self.logger.info(f"Copied {len(kept_paths)} unique files to {self.out_dir}")

        # 4. 리포트 저장
        if dup_map:
            report_df = pd.DataFrame(
                dup_map.items(), columns=["duplicate_file", "source_file"]
            )
            report_df.to_csv(self.report_path, index=False, encoding="utf-8-sig")
            self.logger.info(f"Deduplication report saved to {self.report_path}")

    def _load_texts(self, files: list[Path]) -> list[dict]:
        records = []
        with progress_bar(files, desc="Loading texts") as pbar:
            for p in pbar:
                text = None
                for enc in ("utf-8", "cp949", "euc-kr"):
                    try:
                        text = p.read_text(encoding=enc)
                        break
                    except UnicodeDecodeError:
                        continue
                if text is None:
                    self.logger.warning(f"Encoding issue, skipping: {p.name}")
                    continue
                records.append({"path": str(p), "text": text})
        return records

    def _deduplicate(self, df: pd.DataFrame) -> tuple[set[str], dict[str, str]]:
        ts = TextSim(store_data=True, index_type="exact", use_accelerator=True)
        
        kept_paths = set()
        # {중복 파일: 원본 파일} 맵
        dup_map = {}

        # UniSim은 ID를 저장하지 않으므로, 추가된 텍스트의 인덱스와 파일 경로를 매핑
        indexed_paths = []

        with progress_bar(df.iterrows(), desc="Finding duplicates", total=len(df)) as pbar:
            for _, row in pbar:
                path = row["path"]
                text = str(row["text"])

                if not kept_paths:
                    ts.add([text])
                    kept_paths.add(path)
                    indexed_paths.append(path)
                    continue

                res = ts.search([text], similarity_threshold=self.cfg.UNISIM_THRESHOLD, k=1)

                if res.total_matches == 0:
                    ts.add([text])
                    kept_paths.add(path)
                    indexed_paths.append(path)
                else:
                    # res.results[0]는 첫 쿼리에 대한 Result 객체.
                    # Result 객체는 .matches 속성에 Match 객체 리스트를 가짐.
                    top_match = res.results[0].matches[0]
                    source_text_idx = top_match.idx
                    source_path = indexed_paths[source_text_idx]
                    dup_map[path] = source_path
        
        return kept_paths, dup_map
