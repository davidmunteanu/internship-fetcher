from abc import ABC, abstractmethod
from models import Question

class BaseExtractor(ABC):
    @abstractmethod
    async def extract_questions(self, job_id: str, ats_job_id: str, slug: str, region: str) -> list[Question]:
        """Extract application questions for a specific job."""
        ...
