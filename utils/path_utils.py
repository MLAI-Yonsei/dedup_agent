from pathlib import Path
import shutil
import os
import errno

def safe_move(src: Path, dst_dir: Path) -> Path:
    """cross-device 환경에서도 안전하게 파일을 이동한다."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_path = dst_dir / src.name
    # 이름 충돌 처리
    counter = 1
    while dst_path.exists():
        stem, suff = src.stem, src.suffix
        dst_path = dst_dir / f"{stem}_{counter}{suff}"
        counter += 1
    try:
        # 같은 파일 시스템이면 빠른 rename 사용
        return src.rename(dst_path)
    except OSError as e:
        # cross-device 오류면 shutil.move 로 폴백
        if e.errno == errno.EXDEV:          # 18 = EXDEV
            shutil.move(str(src), str(dst_path))
            return dst_path
        raise                                 # 다른 OSError 는 그대로 올림

def safe_copy(src: Path, dst_dir: Path) -> Path:
    """파일을 안전하게 복사합니다. 이름 충돌 시 (1), (2)... 와 같이 숫자를 붙입니다."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    final_dst = dst_dir / src.name

    # 이름 충돌 시 (1), (2) ... 추가
    counter = 1
    while final_dst.exists():
        final_dst = dst_dir / f"{src.stem} ({counter}){src.suffix}"
        counter += 1

    shutil.copy2(str(src), str(final_dst))
    return final_dst

def cleanup_temp_dirs(cfg):
    """임시 작업 디렉터리를 정리합니다."""
    temp_dirs = [
        cfg.TEMP1_DIR,
        cfg.TEMP2_DIR,
        cfg.TEXT_TEMP_DIR,
        cfg.IMAGE_FINAL_DIR,
        cfg.MINERU_INPUT_DIR,
        cfg.MINERU_OUTPUT_DIR_PASS1,
        cfg.MINERU_OUTPUT_DIR_PASS2,
    ]
    for d in temp_dirs:
        if d.exists():
            shutil.rmtree(d)
