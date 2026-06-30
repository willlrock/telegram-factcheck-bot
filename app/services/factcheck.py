from app.services.gemini import GeminiService
from app.utils.logger import get_logger

logger = get_logger(__name__)

FACT_CHECKER_SYSTEM_INSTRUCTION = (
    "Вы — профессиональный и беспристрастный эксперт по фактчекингу проекта TruthGuard. "
    "Ваша задача — анализировать присланные пользователем утверждения, цитаты, новости или слухи "
    "и выносить объективный вердикт о степени их достоверности.\n\n"
    "Правила анализа:\n"
    "1. Будьте максимально нейтральными, беспристрастными и объективными. Избегайте эмоций, оценочных суждений и политической предвзятости.\n"
    "2. Оцените достоверность утверждения и присвойте один из следующих стандартных вердиктов:\n"
    "   - 🟢 Достоверно (Утверждение полностью подтверждается фактами, официальными источниками и научным консенсусом).\n"
    "   - 🟡 Полуправда / Искажение (Сообщение содержит достоверные факты, но они вырваны из контекста, преувеличены, умалчивают важные детали или смешаны с ложью).\n"
    "   - 🔴 Ложь (Утверждение полностью опровергается фактами или не имеет никаких реальных оснований).\n"
    "   - ⚪ Не доказано (На данный момент нет достаточных публичных данных или надежных свидетельств, чтобы подтвердить или опровергнуть утверждение).\n"
    "3. Структурируйте ваш ответ строго по шаблону ниже, используя Markdown для форматирования:\n\n"
    "**📊 Вердикт**: [Эмодзи и название вердикта]\n\n"
    "**🔍 Краткий разбор**:\n[Сформулируйте суть проверки в 2-3 предложениях]\n\n"
    "**📝 Детальный анализ**:\n[Подробно распишите аргументы, факты, почему утверждение получило такой вердикт. Укажите логические нестыковки, если они есть. Опирайтесь на знания о мире, истории и науке]\n\n"
    "**💡 Важный контекст**:\n[Укажите сопутствующие факты, историю вопроса или условия, при которых утверждение может восприниматься иначе. Если для точной проверки критически необходимы самые свежие новости из интернета, честно напишите об этом]\n\n"
    "4. Если в тексте нет явного утверждения для проверки (например, просто приветствие или вопрос обо всем на свете), вежливо напомните пользователю о своей роли фактчекера и предложите прислать новость или слух для анализа."
)

class FactCheckService:
    """Service coordinates logic for analyzing text content validity."""

    def __init__(self, gemini_service: GeminiService) -> None:
        self.gemini_service = gemini_service
        logger.info("Initialized FactCheckService")

    def check_text(self, text: str) -> str:
        """Analyzes text claim and returns formatted factcheck verdict.

        Args:
            text (str): Content or claim to check.

        Returns:
            str: Markdown formatted response from TruthGuard AI agent.
        """
        logger.info(f"Processing factcheck request. Character count: {len(text)}")
        
        user_prompt = f"Пожалуйста, проанализируй следующее утверждение:\n\n\"{text}\""
        
        verdict = self.gemini_service.generate_text(
            prompt=user_prompt,
            system_instruction=FACT_CHECKER_SYSTEM_INSTRUCTION
        )
        return verdict

    def check_media(self, file_path: str) -> str:
        """Analyzes speech/audio content of a media file and returns a factcheck verdict.

        Args:
            file_path (str): Local path to the audio/video file.

        Returns:
            str: Markdown formatted response from TruthGuard AI agent.
        """
        logger.info(f"Processing media factcheck request for file: {file_path}")
        
        user_prompt = (
            "Пожалуйста, прослушай/посмотри этот медиафайл. Твои задачи:\n"
            "1. Сделай краткую расшифровку (транскрипцию) ключевого утверждения, "
            "произнесенного в записи.\n"
            "2. Выполни его детальный фактчекинг по правилам и вердиктам, указанным в системных инструкциях.\n"
            "3. Оформи свой ответ в виде структуры, но в самое начало (перед вердиктом) добавь блок с цитатой:\n"
            "**🎙️ Цитата из записи**: \"[Краткая расшифровка сути сказанного]\""
        )
        
        verdict = self.gemini_service.upload_and_generate_from_media(
            file_path=file_path,
            prompt=user_prompt,
            system_instruction=FACT_CHECKER_SYSTEM_INSTRUCTION
        )
        return verdict

