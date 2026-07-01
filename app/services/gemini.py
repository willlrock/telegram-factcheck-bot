import time
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

    def upload_and_generate_from_media(self, file_path: str, prompt: str, system_instruction: str = None) -> str:
        """Uploads a file to the Gemini File API, polls until ACTIVE, generates content,
        and ensures the file is deleted from Gemini storage.

        Args:
            file_path (str): Local path to the file to upload.
            prompt (str): Text instructions for the file analysis.
            system_instruction (str, optional): Role or guidelines for the AI.

        Returns:
            str: Generated text response.
        """
        logger.info(f"Uploading file {file_path} to Gemini File API...")
        uploaded_file = None
        try:
            uploaded_file = self.client.files.upload(
                file=file_path, 
                config=types.UploadFileConfig(mime_type="audio/mp4")
            )
            logger.info(f"Uploaded file name: {uploaded_file.name}, initial state: {uploaded_file.state.name}")

            # Poll until ACTIVE
            max_attempts = 30
            attempts = 0
            while uploaded_file.state.name == "PROCESSING" and attempts < max_attempts:
                logger.debug(f"File {uploaded_file.name} is processing... (attempt {attempts+1}/{max_attempts})")
                time.sleep(2)
                uploaded_file = self.client.files.get(name=uploaded_file.name)
                attempts += 1

            if uploaded_file.state.name != "ACTIVE":
                logger.error(f"File {uploaded_file.name} processing ended in state: {uploaded_file.state.name}")
                return f"Ошибка: не удалось подготовить медиафайл для анализа (статус: {uploaded_file.state.name})."

            cfg = None
            if system_instruction:
                cfg = types.GenerateContentConfig(system_instruction=system_instruction)

            logger.info(f"Running multimodal content generation for {uploaded_file.name}...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=[uploaded_file, prompt],
                config=cfg
            )

            if not response.text:
                logger.warning("Gemini API returned empty response for media.")
                return "Извините, не удалось получить результаты анализа медиафайла."

            return response.text

        except APIError as e:
            logger.error(f"Gemini API Error during media analysis: {e}", exc_info=True)
            return "Произошла ошибка API Gemini при обработке медиафайла."
        except Exception as e:
            logger.error(f"Unexpected error during media analysis: {e}", exc_info=True)
            return "Произошла непредвиденная ошибка при анализе медиафайла."
        finally:
            if uploaded_file:
                try:
                    logger.info(f"Deleting cloud file from Gemini File API: {uploaded_file.name}")
                    self.client.files.delete(name=uploaded_file.name)
                except Exception as delete_err:
                    logger.warning(f"Failed to delete cloud file {uploaded_file.name}: {delete_err}")

