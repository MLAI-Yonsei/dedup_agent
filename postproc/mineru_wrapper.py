from pathlib import Path
import json
import logging
import subprocess
import shutil
from datetime import datetime

class MinerUWrapper:
    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger(self.__class__.__name__)
        # magic-pdf 명령어 자체를 설정으로 관리
        self.bin_command = "magic-pdf" 

    def parse_dir(self, input_dir: Path, output_dir: Path) -> list[Path]:
        """
        디렉토리 단위로 magic-pdf를 실행하고, 결과를 파싱하여
        텍스트는 TEXT_TEMP_DIR에 저장하고, 하위 이미지 경로 리스트를 반환한다.
        """
        all_sub_images = []

        try:
            # 1. MinerU (magic-pdf) 실행
            cmd = [
                self.bin_command,
                "-p", str(input_dir),
                "-o", str(output_dir),
                "--lang", "korean",
                "--method", "ocr"
            ]
            self.logger.info("Running MinerU command: %s", " ".join(cmd))
            # 실행 결과의 출력을 로깅하기 위해 capture_output=True 사용
            result = subprocess.run(
                cmd, check=True, text=True, capture_output=True, encoding="utf-8"
            )
            self.logger.debug("MinerU stdout:\n%s", result.stdout)
            if result.stderr:
                self.logger.warning("MinerU stderr:\n%s", result.stderr)

            # 2. 결과 파싱
            self.logger.info("Parsing MinerU output from: %s", output_dir)
            if not output_dir.exists():
                self.logger.warning("MinerU output directory not found!")
                return []

            for ori_file_dir in output_dir.iterdir():
                if not ori_file_dir.is_dir():
                    continue
                
                auto_dir = ori_file_dir / "ocr"
                if not auto_dir.is_dir():
                    continue

                # 2-1. 텍스트 추출 및 저장
                md_files = list(auto_dir.glob("*.md"))
                if md_files:
                    md_path = md_files[0]
                    self.logger.debug("Found markdown file: %s", md_path)
                    md_content_raw = md_path.read_text(encoding="utf-8")
                    
                    # 이미지 링크 라인 제거
                    lines = md_content_raw.splitlines()
                    filtered_lines = [line for line in lines if not line.strip().startswith("![](images/")]
                    md_content_cleaned = "\n".join(filtered_lines)
                    
                    # 내용이 실제로 있는 경우에만 파일 생성
                    if md_content_cleaned.strip():
                        # 최종 텍스트 저장소에 고유 이름으로 저장
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        txt_path = self.cfg.TEXT_TEMP_DIR / f"mineru_{md_path.stem}_{ts}.txt"
                        txt_path.write_text(md_content_cleaned, encoding="utf-8")
                        self.logger.debug("Saved extracted text to: %s", txt_path)

                # 2-2. 하위 이미지 경로 수집
                images_dir = auto_dir / "images"
                if images_dir.is_dir():
                    sub_images = [p for p in images_dir.iterdir() if p.is_file()]
                    all_sub_images.extend(sub_images)
                    self.logger.debug("Found %d sub-images in %s", len(sub_images), images_dir)

        except FileNotFoundError:
            self.logger.error("'%s' not found. Is magic-pdf installed and in PATH?", self.bin_command)
            return []
        except subprocess.CalledProcessError as e:
            self.logger.error("MinerU execution failed with exit code %d.", e.returncode)
            self.logger.error("Stdout: %s", e.stdout)
            self.logger.error("Stderr: %s", e.stderr)
            return []
        except Exception as e:
            self.logger.error("An unexpected error occurred during MinerU processing: %s", e, exc_info=True)
            return []
            
        return all_sub_images