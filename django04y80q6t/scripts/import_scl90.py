# coding:utf-8
"""Import an authorized SCL-90 item CSV into exampaper/examquestion.

CSV format:
sequence,questionname
1,Your authorized item text
...
90,Your authorized item text

Run from django04y80q6t:
python scripts/import_scl90.py scripts/scl90_items_template.csv
"""

import csv
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj2.settings")

import django

django.setup()

from main.models import exampaper, examquestion
from main.scl90 import SCL90_OPTION_TEMPLATE


def load_items(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 90:
        raise ValueError("SCL-90 requires exactly 90 rows")
    items = []
    for row in rows:
        sequence = int(row["sequence"])
        text = (row["questionname"] or "").strip()
        if not text or text.startswith("请替换"):
            raise ValueError("Row {} has no authorized question text".format(sequence))
        items.append((sequence, text))
    return items


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/import_scl90.py <csv_path>")
    items = load_items(sys.argv[1])
    paper = exampaper.objects.filter(name__icontains="SCL-90").first()
    if not paper:
        paper = exampaper.objects.create(
            name="SCL-90症状自评量表",
            time=30,
            status="启用",
            examnum=99,
        )

    option_text = json.dumps(SCL90_OPTION_TEMPLATE, ensure_ascii=False)
    for sequence, text in items:
        examquestion.objects.update_or_create(
            paperid=paper.id,
            sequence=91 - sequence,
            defaults={
                "papername": paper.name,
                "questionname": text,
                "options": option_text,
                "score": 5,
                "answer": "",
                "analysis": "SCL-90量表题目按1-5级计分，无标准对错答案。",
                "type": 0,
            }
        )
    print("Imported SCL-90 paper id={} items=90".format(paper.id))


if __name__ == "__main__":
    main()
