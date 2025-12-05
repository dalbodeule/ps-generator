import os
import logging
from io import BytesIO
from typing import Optional

from google import genai
from google.genai import types


def gemini_image(model: str, prompt: str, aspect_ratio: str = "16:9") -> bytes:
    """Google Gemini(nano banana pro)로 이미지를 생성해 PNG 바이트로 반환한다.

    공식 예제:

        from google import genai
        from google.genai import types

        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
                tools=[{"google_search": {}}]
            )
        )

    를 기반으로, 여기서는 Image 응답만 집중해서 첫 번째 이미지 파트를
    메모리상의 PNG(bytes)로 직렬화한다.
    """
    logging.info("Starting Gemini image generation (nano banana pro)...")

    # 1) 클라이언트 생성
    api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else genai.Client()

    # 2) 모델명 매핑
    # - cfg.image_model 기본값은 논리적 레이블 "openai-nano-banana-pro"
    # - 실제 Gemini 모델은 "gemini-3-pro-image-preview" 사용
    model_name = "gemini-3-pro-image-preview"
    if model and model != "openai-nano-banana-pro":
        # 사용자가 실제 Gemini 모델명을 넘겼다면 우선 사용
        model_name = model

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["Image"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            ),
        )

        # 3) 첫 번째 이미지 파트를 찾아 PNG bytes로 직렬화
        for part in response.parts:
            if image := part.as_image():
                return image.image_bytes

        logging.warning("No image part found in Gemini response; returning PNG header fallback.")
        return b"\x89PNG\r\n\x1a\n"
    except Exception as e:  # pragma: no cover - 방어적 코드
        logging.exception("Gemini image generation failed: %s", e)
        # 파이프라인이 죽지 않도록 최소 PNG 헤더 반환
        return b"\x89PNG\r\n\x1a\n"