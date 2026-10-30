# scripts/fetch_icsc_cards.py
"""Скачивает все ICSC-карты со https://chemicalsafety.ilo.org/.

Использование:
    uv run python scripts/fetch_icsc_cards.py data/raw/icsc/
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

UA = "ChemSafetyAssistant/0.1 (course project)"


def safe_name(text: str, maxlen: int = 120) -> str:
    text = text.replace("\xa0", " ").strip()
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:maxlen] or "unnamed"


def collect_cards(html: str, page_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards: list[dict] = []
    for a in soup.select('a[href*="showcard.display"]'):
        href = a.get("href", "")
        qs = parse_qs(urlparse(href).query)
        if qs.get("p_lang", [""])[0] != "ru":
            continue
        card_id = (qs.get("p_card_id") or [""])[0]
        tr = a.find_parent("tr")
        if tr is None:
            continue
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        # название: весь текст второй ячейки, переводы строк -> пробел
        title = tds[1].get_text(" ", strip=True)
        cards.append({
            "url": urljoin(page_url, href),
            "card_id": card_id,
            "title": title,
        })
    return cards


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("out_dir", type=Path)
    p.add_argument("--delay", type=float, default=1.0)
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = UA

    page_url = "https://chemicalsafety.ilo.org/dyn/icsc/showcard.listcards3?p_lang=ru"

    print(f"[search] {page_url}")
    resp = session.get(page_url, timeout=30)
    resp.raise_for_status()

    cards = collect_cards(resp.text, page_url)
    if args.limit:
        cards = cards[: args.limit]
    print(f"[found] {len(cards)} карт")

    index_rows: list[dict] = []
    for i, card in enumerate(cards, 1):
        # имя файла — по номеру карты, название — в index.csv
        fname = f"{card['card_id'] or 'unknown'}.html"
        out = args.out_dir / fname
        if out.exists():
            print(f"[skip {i}/{len(cards)}] {fname}")
        else:
            try:
                r = session.get(card["url"], timeout=30)
                r.raise_for_status()
                out.write_bytes(r.content)
                print(f"[ok {i}/{len(cards)}] {fname}  {card['title'][:60]}")
            except requests.RequestException as exc:
                print(f"[fail {i}/{len(cards)}] {card['url']}: {exc}")
                time.sleep(args.delay)
                continue
            time.sleep(args.delay)
        index_rows.append({
            "card_id": card["card_id"],
            "title": card["title"],
            "url": card["url"],
            "file": fname,
        })

    index_path = args.out_dir / "index.csv"
    with index_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["card_id", "title", "url", "file"])
        w.writeheader()
        w.writerows(index_rows)
    print(f"[index] {index_path}  ({len(index_rows)} строк)")


if __name__ == "__main__":
    main()