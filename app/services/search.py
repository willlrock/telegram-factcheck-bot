from app.utils.logger import get_logger

logger = get_logger(__name__)

class SearchEngineService:
    """Stub for search engine integration to perform web searches for factual validation.

    Reserved for future implementation (Stage 3).
    """

    def __init__(self) -> None:
        logger.info("Initialized stub SearchEngineService (inactive in MVP)")

    def search(self, query: str) -> list:
        """Stub method for querying external search APIs.

        Args:
            query (str): The query string to search.

        Returns:
            list: Always returns an empty list in MVP.
        """
        logger.debug(f"Search stub called with query: '{query}'")
        return []
