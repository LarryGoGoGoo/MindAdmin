# coding:utf-8
"""Seed a runnable SCL-90 assessment into exampaper/examquestion.

Run from django04y80q6t:
python scripts/seed_scl90.py

The script is idempotent. It updates the same SCL-90 paper and its 90 questions
instead of creating duplicates.
"""

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


SCL90_PAPER_NAME = "SCL-90症状自评量表"

SCL90_ITEMS = [
    "头痛",
    "神经过敏，心中不踏实",
    "头脑中有不必要的想法或字句盘旋",
    "头昏或昏倒",
    "对异性的兴趣减退",
    "对旁人责备求全",
    "感到别人能控制您的思想",
    "责怪别人制造麻烦",
    "忘性大",
    "担心自己的衣饰整齐及仪态的端正",
    "容易烦恼和激动",
    "胸痛",
    "害怕空旷的场所或街道",
    "感到自己的精力下降，活动减慢",
    "想结束自己的生命",
    "听到旁人听不到的声音",
    "发抖",
    "感到大多数人都不可信任",
    "胃口不好",
    "容易哭泣",
    "同异性相处时感到害羞不自在",
    "感到受骗、中了圈套或有人想抓住您",
    "无缘无故地突然感到害怕",
    "自己不能控制地大发脾气",
    "怕单独出门",
    "经常责怪自己",
    "腰痛",
    "感到难以完成任务",
    "感到孤独",
    "感到苦闷",
    "过分担忧",
    "对事物不感兴趣",
    "感到害怕",
    "您的感情容易受到伤害",
    "旁人能知道您的私下想法",
    "感到别人不理解您、不同情您",
    "感到人们对您不友好，不喜欢您",
    "做事必须做得很慢以保证做得正确",
    "心跳得很厉害",
    "恶心或胃部不舒服",
    "感到比不上他人",
    "肌肉酸痛",
    "感到有人在监视您、谈论您",
    "难以入睡",
    "做事必须反复检查",
    "难以作出决定",
    "怕乘电车、公共汽车、地铁或火车",
    "呼吸有困难",
    "一阵阵发冷或发热",
    "因为感到害怕而避开某些东西、场合或活动",
    "脑子变空了",
    "身体发麻或刺痛",
    "喉咙有梗塞感",
    "感到前途没有希望",
    "不能集中注意力",
    "感到身体的某一部分软弱无力",
    "感到紧张或容易紧张",
    "感到手或脚发重",
    "想到死亡的事",
    "吃得太多",
    "当别人看着您或谈论您时感到不自在",
    "有一些不属于您自己的想法",
    "有想打人或伤害他人的冲动",
    "醒得太早",
    "必须反复洗手、点数目或触摸某些东西",
    "睡得不稳不深",
    "有想摔坏或破坏东西的冲动",
    "有一些别人没有的想法或念头",
    "感到对别人神经过敏",
    "在商店或电影院等人多的地方感到不自在",
    "感到任何事情都很困难",
    "一阵阵恐惧或惊恐",
    "感到在公共场合吃东西很不舒服",
    "经常与人争论",
    "单独一人时神经很紧张",
    "别人对您的成绩没有作出恰当评价",
    "即使和别人在一起也感到孤单",
    "感到坐立不安心神不定",
    "感到自己没有什么价值",
    "感到熟悉的东西变成陌生或不像是真的",
    "大叫或摔东西",
    "害怕会在公共场合昏倒",
    "感到别人想占您的便宜",
    "为一些有关性的想法而很苦恼",
    "认为应该因为自己的过错而受到惩罚",
    "感到要赶快把事情做完",
    "感到自己的身体有严重问题",
    "从未感到和其他人很亲近",
    "感到自己有罪",
    "感到自己的脑子有毛病",
]


def ensure_scl90():
    if len(SCL90_ITEMS) != 90:
        raise ValueError("SCL-90 item count must be exactly 90")

    paper = exampaper.objects.filter(name=SCL90_PAPER_NAME).first()
    if paper is None:
        paper = exampaper.objects.create(
            name=SCL90_PAPER_NAME,
            time=30,
            status="1",
            examnum=9999,
        )
    else:
        paper.time = 30
        paper.status = "1"
        paper.examnum = 9999
        paper.save(update_fields=["time", "status", "examnum"])

    option_text = json.dumps(SCL90_OPTION_TEMPLATE, ensure_ascii=False)
    existing = {
        item.sequence: item
        for item in examquestion.objects.filter(paperid=paper.id)
    }
    kept_ids = []
    for index, text in enumerate(SCL90_ITEMS, start=1):
        sequence = 91 - index
        question = existing.get(sequence)
        defaults = {
            "paperid": paper.id,
            "papername": paper.name,
            "questionname": text,
            "options": option_text,
            "score": 5,
            "answer": "",
            "analysis": "SCL-90量表题目按1-5级计分，无标准对错答案。",
            "type": 0,
            "sequence": sequence,
        }
        if question is None:
            question = examquestion.objects.create(**defaults)
        else:
            for key, value in defaults.items():
                setattr(question, key, value)
            question.save(update_fields=list(defaults.keys()))
        kept_ids.append(question.id)

    examquestion.objects.filter(paperid=paper.id).exclude(id__in=kept_ids).delete()
    return paper


if __name__ == "__main__":
    paper = ensure_scl90()
    count = examquestion.objects.filter(paperid=paper.id).count()
    print("Seeded {} paper_id={} questions={}".format(paper.name, paper.id, count))
