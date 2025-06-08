import logging
from pathlib import Path
from .config import Config


def setup_logging(cfg: Config) -> None:
    log_file = cfg.WORK_DIR / "run.log"

    # 기본 로거는 DEBUG로 설정하여 모든 레벨을 핸들러로 전달
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 기존에 연결된 핸들러가 있다면 모두 제거 (중복 로깅 방지)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    # 포매터 설정
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # 파일 핸들러: DEBUG 레벨 이상의 모든 로그를 기록
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    # 콘솔(스트림) 핸들러: INFO 레벨 이상의 로그만 표시
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    root_logger.addHandler(sh)

    # 특정 라이브러리의 로그 레벨을 조정하여 과도한 출력 방지
    logging.getLogger("PIL").setLevel(logging.WARNING)