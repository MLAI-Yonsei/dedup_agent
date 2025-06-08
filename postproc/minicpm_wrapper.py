from pathlib import Path
import logging
import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer


class MiniCPMWrapper:
    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        try:
            self.logger.info("Loading MiniCPM model...")
            model_path = self.cfg.MINICPM_MODEL_PATH
            
            if not Path(model_path).exists():
                raise FileNotFoundError(f"Model path not found: {model_path}")

            self.model = AutoModel.from_pretrained(
                model_path,
                trust_remote_code=True,
                attn_implementation='sdpa',
                torch_dtype=torch.bfloat16
            ).eval().cuda()
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            self.logger.info("MiniCPM model loaded successfully.")
        except Exception as e:
            self.logger.error("Failed to load MiniCPM model: %s", e, exc_info=True)
            # 모델 로딩 실패 시, 이후 predict 호출이 실패하도록 model을 None으로 둡니다.
            self.model = None

    def predict(self, image_path: Path) -> str:
        if not self.model:
            self.logger.error("Model is not loaded, cannot predict. Returning 'mixed'.")
            return "mixed"
            
        try:
            image = Image.open(image_path).convert('RGB')
            # 모델이 'pure' 또는 'mixed'로 확실하게 답변하도록 유도하는 프롬프트
            question = "Does this image contain any text? Answer with only one word: 'pure' or 'mixed'."
            msgs = [{'role': 'user', 'content': [image, question]}]

            # 모델 추론
            res = self.model.chat(
                image=image,  # image 인자를 직접 전달합니다
                msgs=msgs,
                tokenizer=self.tokenizer
            )
            
            # 결과 파싱
            answer = res.lower()
            if "pure" in answer:
                return "pure"
            else:
                return "mixed"

        except Exception as e:
            self.logger.error("MiniCPM prediction failed for %s: %s", image_path, e)
            return "mixed" # 에러 발생 시 안전하게 'mixed'로 처리