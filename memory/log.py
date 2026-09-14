#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مساعد الذاكرة السجلية — يُلحق حدثاً مؤرخاً في LOG.md وملف الجلسة اليومي.

الاستخدام:
  python3 memory/log.py "نص الحدث" [--tag قرار] [--root .]

الوسوم المقترحة: مهمة قرار درس اختبار إصلاح بيئة نشر تحذير
"""
import argparse, os, datetime

MEM = os.path.dirname(os.path.abspath(__file__))

def entry(tag, text):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    day = now[:10]
    line = f"- [{now}] [{tag}] {text}\n"
    with open(os.path.join(MEM, "LOG.md"), "a", encoding="utf-8") as f:
        f.write(line)
    dayfile = os.path.join(MEM, "sessions", f"{day}.md")
    if not os.path.exists(dayfile):
        with open(dayfile, "w", encoding="utf-8") as f:
            f.write(f"# 🗓️ جلسة {day}\n\n## الأحداث\n")
    with open(dayfile, "a", encoding="utf-8") as f:
        # إن كان الملف موجوداً مسبقاً بدون قسم أحداث، أضف القسم
        content = open(dayfile, encoding="utf-8").read()
        if "## الأحداث" not in content:
            f.write("\n## الأحداث\n")
        f.write(line)
    print("✔️ سُجّل:", line.strip())
    return line

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", help="نص الحدث")
    ap.add_argument("--tag", default="مهمة")
    a = ap.parse_args()
    entry(a.tag, a.text)

if __name__ == "__main__":
    main()
