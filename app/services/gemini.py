from google import genai
from google.genai import types
from google.genai.errors import APIError
from app import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

class GeminiService:
    """Service wrapper for interacting with the Google Gemini API."""

    def __init__(self) -> None:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")
        # Initialize client explicitly with the loaded API key
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = config.GEMINI_MODEL
        logger.info(f"Initialized GeminiService with model: {self.model}")

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        """Generates text based on prompt and optional system instructions.

        Args:
            prompt (str): User input or prompt.
            system_instruction (str, optional): Role or guidelines for the AI.

        Returns:
            str: Generated text response.
        """
        logger.debug(f"Generating content using model {self.model}. Prompt length: {len(prompt)}")
        try:
            cfg = None
            if system_instruction:
                cfg = types.GenerateContentConfig(system_instruction=system_instruction)
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=cfg
            )
            
            if not response.text:
                logger.warning("Gemini API returned empty response text.")
                return "Извините, не удалось получить ответ от модели. Попробуйте сформулировать запрос иначе."
                
            return response.text
        except APIError as e:
            logger.error(f"Gemini API Error occurred: {e}", exc_info=True)
            return "Произошла ошибка при обращении к Gemini API. Возможно, превышены лимиты запросов."
        except Exception as e:
            logger.error(f"Unexpected error in GeminiService: {e}", exc_info=True)
            return "Произошла непредвиденная ошибка при обработке запроса к AI-модели."
