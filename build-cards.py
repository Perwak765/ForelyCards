#!/usr/bin/env python3
"""Build the static ForelCards catalog for GitHub Pages.

Input:
  incoming/*.webp
  metadata.csv (optional; columns: filename,character,rank,platform,description,link,date)
Output:
  cards/images/*.webp
  cards/cards.json
"""
from __future__ import annotations
import csv, json, re, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "incoming"
IMAGES = ROOT / "cards" / "images"
OUTPUT = ROOT / "cards" / "cards.json"
META = ROOT / "metadata.csv"
MAX_FILES = 5000

RANKS = {"A rank", "Re rank", "R rank", "X rank", "Авторская"}

def slug(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "-", s.strip(), flags=re.UNICODE).strip("-").lower()
    return s or "card"

def iso_date(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    v = value.strip()
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        raise SystemExit(f"Невірна дата в metadata.csv: {value!r}")

def main():
    INCOMING.mkdir(exist_ok=True); IMAGES.mkdir(parents=True, exist_ok=True)
    files = sorted([p for p in INCOMING.iterdir() if p.is_file() and p.suffix.lower()==".webp"])
    if len(files) > MAX_FILES:
        raise SystemExit(f"Знайдено {len(files)} WebP. Максимум цього імпортера: {MAX_FILES}.")

    rows = {}
    if META.exists():
        with META.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                name = (row.get("filename") or "").strip()
                if name: rows[name] = row

    cards=[]
    used=set()
    for idx, src in enumerate(files, 1):
        row=rows.get(src.name, {})
        character=(row.get("character") or src.stem).strip()
        rank=(row.get("rank") or "A rank").strip()
        platform=(row.get("platform") or "Авторские").strip()
        description=(row.get("description") or "").strip()
        link=(row.get("link") or "").strip()
        if rank not in RANKS and not rank: rank="A rank"
        base=f"{slug(src.stem)}-{idx:04d}.webp"
        while base in used or (IMAGES/base).exists():
            idx += 1; base=f"{slug(src.stem)}-{idx:04d}.webp"
        used.add(base)
        shutil.copy2(src, IMAGES/base)
        cards.append({
            "id": f"card-{idx:04d}-{slug(src.stem)}",
            "character": character,
            "rank": rank,
            "platform": platform,
            "description": description,
            "link": link,
            "image": f"cards/images/{base}",
            "date": iso_date(row.get("date")),
        })
    cards.sort(key=lambda c:c["date"], reverse=True)
    OUTPUT.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Готово: {len(cards)} карт -> {OUTPUT}")

if __name__ == "__main__": main()
