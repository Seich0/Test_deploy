"""Агент-источник EMA: страницы EPAR со ссылками на SmPC."""

import html
import logging
from datetime import date, datetime
from typing import Dict, List, Optional

import requests

from utils import resolve_date_range
from validator import _find_topic

logger = logging.getLogger("archiv_tracker.ema")
SOURCE_ID = "ema"
SOURCE_NAME = "EMA (EPAR / SmPC)"
DATA_URL = "https://www.ema.europa.eu/en/media/67423"


def fetch(topics: List[str], rows: int = 20, date_from: Optional[date] = None,
          date_to: Optional[date] = None) -> List[Dict]:
    """Искать в выгрузке страниц препаратов EMA по дате обновления."""
    date_from, date_to = resolve_date_range(date_from=date_from, date_to=date_to)
    resp = requests.get(DATA_URL, timeout=60)
    resp.raise_for_status()
    items = []
    for doc in resp.json().get("data", []):
        try:
            updated = datetime.strptime(doc.get("last_updated_date", ""), "%d/%m/%Y").date()
        except ValueError:
            continue
        url = doc.get("medicine_url", "")
        if not (date_from <= updated <= date_to and url and doc.get("category") == "Human"):
            continue
        title = doc.get("name_of_medicine") or "(без названия)"
        abstract = html.unescape(" ".join(str(doc.get(k) or "") for k in (
            "active_substance", "therapeutic_area_mesh", "therapeutic_indication")))
        if not _find_topic(f"{title} {abstract}", topics):
            continue
        items.append({"source": SOURCE_ID, "identifier": f"ema:{url}", "title": title,
                      "url": url, "abstract": abstract, "updated": updated.isoformat()})
    return sorted(items, key=lambda item: item["updated"], reverse=True)[:max(rows, 0)]
