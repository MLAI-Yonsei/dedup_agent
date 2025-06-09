from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    # 디렉터리
    ROOT: Path = Path(__file__).resolve().parent.parent
    WORK_DIR: Path = ROOT / "work"
    TEMP1_DIR: Path = WORK_DIR / "temp1"
    TEMP2_DIR: Path = WORK_DIR / "temp2"
    IMAGE_FINAL_DIR: Path = WORK_DIR / "image_final"  # 이미지 후처리 완료, 중복 제거 대상
    IMAGE_DEDUP_DIR: Path = WORK_DIR / "image_dedup_final" # 이미지 중복 제거 후 최종 저장
    TEXT_TEMP_DIR: Path = WORK_DIR / "text_temp"  # TXT 파일 임시 수집
    TEXT_DEDUP_DIR: Path = WORK_DIR / "text_final"  # 중복 제거 후 최종 저장

    # MinerU 임시 폴더
    MINERU_INPUT_DIR: Path = WORK_DIR / "mineru_input"
    MINERU_OUTPUT_DIR_PASS1: Path = WORK_DIR / "mineru_output_pass1"
    MINERU_OUTPUT_DIR_PASS2: Path = WORK_DIR / "mineru_output_pass2"

    # --- 외부 도구 설정 ---
    # MiniCPM (VQA)
    MINICPM_MODEL_PATH: str = "/data1/doongsae/models/models--openbmb--MiniCPM-V-2_6/snapshots/4719557d673e9e2b4b3f083801626098f51441a8"
    # MINICPM_MODEL_PATH: str = "/data1/doongsae/models/models--openbmb--MiniCPM-o-2_6/snapshots/1758aee77fc3fceafbe2522f79124eeb81b14873"

    # MinerU (Layout Parser)
    MINERU_BIN: str = "mineru_cli"

    # --- 중복제거 파라미터 ---
    # TextUnisim
    UNISIM_THRESHOLD: float = 0.99
    # ImageFiftyOne
    FIFTYONE_MODEL: str = "mobilenet-v2-imagenet-torch"
    FIFTYONE_THRESHOLD: float = 0.98
    FIFTYONE_BATCH_SIZE: int = 1

    # 파라미터
    MAX_ITER: int = 2


def ensure_dirs(cfg: "Config") -> None:
    for d in [
        cfg.WORK_DIR,
        cfg.TEMP1_DIR,
        cfg.TEMP2_DIR,
        cfg.IMAGE_FINAL_DIR,
        cfg.IMAGE_DEDUP_DIR,
        cfg.TEXT_TEMP_DIR,
        cfg.TEXT_DEDUP_DIR,
        cfg.MINERU_INPUT_DIR,
        cfg.MINERU_OUTPUT_DIR_PASS1,
        cfg.MINERU_OUTPUT_DIR_PASS2,
    ]:
        d.mkdir(parents=True, exist_ok=True)