from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class Post:
    source: str          # "fb" | "reddit" | "twitter"
    source_label: str    # human-readable e.g. "r/bangalore", "Bangalore Flatmates"
    id: str              # source-native id
    url: str
    text: str
    posted_at: datetime

    @property
    def hash(self) -> str:
        return hashlib.sha1(f"{self.source}:{self.id}".encode()).hexdigest()[:12]
