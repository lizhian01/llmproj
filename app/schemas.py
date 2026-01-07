from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class TextAssistResult:
    summary_short: str
    summary_bullets: List[str]
    topic: str
    sentiment: str
    keywords: List[str]
    entities: Dict[str, Any]   # {"time":..., "location":..., "people":..., "orgs":...}
    rewrite_formal: str
