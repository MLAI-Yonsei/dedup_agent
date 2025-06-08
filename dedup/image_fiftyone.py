import logging
from pathlib import Path
import shutil
import time
from collections import defaultdict
import pandas as pd
import numpy as np

try:
    import fiftyone as fo
    import fiftyone.zoo as foz
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    raise ImportError("Please install fiftyone, fiftyone-zoo, scikit-learn")

from ..utils.progress import progress_bar

class ImageFiftyOne:
    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger(self.__class__.__name__)
        self.in_dir = self.cfg.IMAGE_FINAL_DIR
        self.out_dir = self.cfg.IMAGE_DEDUP_DIR
        self.report_path = self.cfg.WORK_DIR / "image_dedup_report.csv"
        # Fiftyone 설정
        self.model_name = self.cfg.FIFTYONE_MODEL
        self.threshold = self.cfg.FIFTYONE_THRESHOLD
        self.batch_size = self.cfg.FIFTYONE_BATCH_SIZE

    def run(self):
        self.logger.info("Starting image deduplication...")
        if not any(self.in_dir.glob("*")):
            self.logger.warning("No image files found to deduplicate in %s.", self.in_dir)
            return

        # 1. FiftyOne으로 중복 탐지
        kept_paths, dup_map = self._find_duplicates()
        
        # 2. 고유 파일 복사
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info("Copying %d unique files to %s", len(kept_paths), self.out_dir)
        with progress_bar(kept_paths, desc="Copying unique images") as pbar:
            for p_str in pbar:
                p = Path(p_str)
                shutil.copy2(p, self.out_dir / p.name)

        # 3. 리포트 저장
        if dup_map:
            report_df = pd.DataFrame(
                dup_map.items(), columns=["duplicate_file", "source_file"]
            )
            report_df.to_csv(self.report_path, index=False, encoding="utf-8-sig")
            self.logger.info("Image deduplication report saved to %s", self.report_path)

    def _find_duplicates(self) -> tuple[set[str], dict[str, str]]:
        dataset_name = f"image-dedup-{int(time.time())}"
        if fo.dataset_exists(dataset_name):
            fo.delete_dataset(dataset_name)

        self.logger.info("Creating fiftyone dataset from directory %s...", self.in_dir)
        # 오류 수정을 위해 기존 코드 방식을 따라 from_images_dir 사용
        dataset = fo.Dataset.from_images_dir(str(self.in_dir), name=dataset_name, persistent=False)

        if not dataset:
            self.logger.warning("Fiftyone was unable to find any valid images in %s.", self.in_dir)
            return set(), {}

        # Dataset 생성 후, fiftyone이 인식한 파일 경로 목록을 다시 가져와 순서를 보장
        str_image_paths = [s.filepath for s in dataset]
        
        self.logger.info("Computing embeddings with '%s'...", self.model_name)
        model = foz.load_zoo_model(self.model_name)
        embeddings = dataset.compute_embeddings(model, batch_size=self.batch_size)
        
        self.logger.info("Calculating similarity matrix...")
        sim_matrix = cosine_similarity(embeddings)
        np.fill_diagonal(sim_matrix, -1.0) # 자기 자신과의 비교는 제외

        self.logger.info("Grouping duplicates with threshold %.2f...", self.threshold)
        adj = defaultdict(set)
        n = embeddings.shape[0]
        for i in range(n):
            for j in range(i + 1, n):
                if sim_matrix[i, j] > self.threshold:
                    adj[i].add(j)
                    adj[j].add(i)

        visited = set()
        duplicate_groups = []
        for i in range(n):
            if i not in visited:
                group = []
                stack = [i]
                visited.add(i)
                while stack:
                    u = stack.pop()
                    group.append(u)
                    for v in adj[u]:
                        if v not in visited:
                            visited.add(v)
                            stack.append(v)
                if len(group) > 1:
                    duplicate_groups.append(sorted(group))

        removable_indices = set()
        dup_map = {} # {제거될 파일: 원본 파일}
        
        for group in duplicate_groups:
            # 그룹 내 첫번째 파일을 원본으로 간주
            source_idx = group[0]
            source_path = str_image_paths[source_idx]
            for dup_idx in group[1:]:
                removable_indices.add(dup_idx)
                dup_path = str_image_paths[dup_idx]
                dup_map[dup_path] = source_path
        
        all_indices = set(range(n))
        kept_indices = all_indices - removable_indices
        kept_paths = {str_image_paths[i] for i in kept_indices}
        
        self.logger.info(
            "Found %d duplicates. Kept: %d, Removed: %d",
            len(removable_indices), len(kept_paths), len(removable_indices)
        )
        
        dataset.delete()
        return kept_paths, dup_map