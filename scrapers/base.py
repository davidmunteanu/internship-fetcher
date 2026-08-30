from abc import ABC, abstractmethod
from models import Job

class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, company_name: str, slug: str, region: str) -> list[Job]:
        """Fetch all open jobs for a company. Returns raw unfiltered jobs."""
        ...
