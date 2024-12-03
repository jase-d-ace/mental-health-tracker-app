from pydantic import BaseModel
from datetime import datetime
import uuid

class Journal(BaseModel):
    id: uuid.UUID
    published_at: datetime
    title: str
    feeling: int
    content: str
    answer: str