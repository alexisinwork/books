#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ru_readability.py — оценка читабельности русского текста по 5 формулам,
переобученным под русский язык (проект plainrussian, лицензия CC0).

Выдаёт «сколько лет обучения нужно, чтобы понять текст» (grade level)
по пяти индексам: Flesch-Kincaid Grade, Coleman-Liau, Dale-Chale, SMOG, ARI,
плюс сырые метрики и человекочитаемую интерпретацию.

В отличие от qa_readability.py (тепловая карта: длина предложений, диалог,
паразиты) — это слой ФОРМАЛЬНЫХ индексов сложности. Используются вместе.

Запуск:
    python3 ru_readability.py файл.md                # весь текст
    python3 ru_readability.py файл.md --chapters      # + разбивка по главам (## Глава)
    python3 ru_readability.py файл.docx               # docx тоже
    echo "текст" | python3 ru_readability.py -        # из stdin

Поддержка: .md, .txt, .docx и stdin. Markdown-разметка (##, **, `HUD`, ---)
вычищается до подсчёта, чтобы символы разметки не загрязняли метрики.

Источник формул и коэффициентов: infoculture/plainrussian, textmetric/metric.py.
Коэффициенты подобраны на корпусе русских текстов с экспертной разметкой по классам.
"""

import sys
import os
import re
import argparse
from math import sqrt

# ─────────────────────────────────────────────────────────────────────────────
# 1. Алфавит и подсчёт (1:1 с plainrussian, чтобы попадать в калибровку формул)
# ─────────────────────────────────────────────────────────────────────────────
RU_CONSONANTS = list("кпстфхцчшщбвгджзлмнрй")
RU_VOWELS     = list("аеиуояёэюы")
RU_MARKS      = list("ьъ")
RU_LETTERS    = set(RU_CONSONANTS + RU_VOWELS + RU_MARKS)
VOWELS        = set(RU_VOWELS)
SENTENCE_END  = set(".?!")          # как в оригинале: считаем символы-терминаторы
COMPLEX_SYL   = 4                   # слово «сложное», если гласных > 4

# ─────────────────────────────────────────────────────────────────────────────
# 2. Русско-адаптированные коэффициенты (из metric.py, константные варианты)
# ─────────────────────────────────────────────────────────────────────────────
FLG = (0.318, 14.2, 30.5)          # Flesch-Kincaid Grade rus
CLI = (0.055, 0.35, 20.33)         # Coleman-Liau rus
DC  = (0.552, 0.273)               # Dale-Chale rus
SMOG = (1.1, 64.6, 0.05)           # SMOG rus
ARI = (6.26, 0.2805, 31.04)        # Automated Readability Index rus


def fk_grade(syl, words, sent):
    if not words or not sent:
        return 0.0
    x, y, z = FLG
    return x * (words / sent) + y * (syl / words) - z


def coleman_liau(letters, words, sent):
    if not words:
        return 0.0
    x, y, z = CLI
    return x * (letters * 100.0 / words) - y * (sent * 100.0 / words) - z


def dale_chale(complex_w, words, sent):
    if not words or not sent:
        return 0.0
    x, y = DC
    return x * (100.0 * complex_w / words) + y * (words / sent)


def smog(complex_w, sent):
    if not sent:
        return 0.0
    x, y, z = SMOG
    return x * sqrt((y / sent) * complex_w) + z


def ari(letters, words, sent):
    if not words or not sent:
        return 0.0
    x, y, z = ARI
    return x * (letters / words) + y * (words / sent) - z


# ─────────────────────────────────────────────────────────────────────────────
# 3. Человекочитаемая интерпретация grade level (из plainrussian)
# ─────────────────────────────────────────────────────────────────────────────
GRADE_TEXT = {
    range(1, 4):   "1–3 класс (≈6–8 лет)",
    range(4, 7):   "4–6 класс (≈9–11 лет)",
    range(7, 10):  "7–9 класс (≈12–14 лет)",
    range(10, 12): "10–11 класс (≈15–16 лет)",
    range(12, 15): "1–3 курс вуза (≈17–19 лет)",
    range(15, 18): "4–6 курс вуза (≈20–22 года)",
}
POST_GRADE = "аспирантура / второе высшее / phD"


def grade_label(grade):
    g = round(grade)
    if g > 17:
        return POST_GRADE
    if g < 1:
        return "проще 1 класса (очень лёгкий)"
    for rng, label in GRADE_TEXT.items():
        if g in rng:
            return label
    return f"неизвестно ({g})"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Подсчёт сырых метрик (логика plainrussian: слог = гласная)
# ─────────────────────────────────────────────────────────────────────────────
def count_metrics(text):
    sentences = chars = spaces = letters = syllabes = 0
    words = complex_w = simple_w = 0

    for line in text.splitlines():
        chars += len(line)
        for ch in line:
            if ch in SENTENCE_END:
                sentences += 1
            if ch in (" ", "\t"):
                spaces += 1
        for tok in line.split():
            wsyl = 0
            has_syl = False
            for ch in tok.lower():
                if ch in RU_LETTERS:
                    letters += 1
                if ch in VOWELS:
                    syllabes += 1
                    wsyl += 1
                    has_syl = True
            if wsyl > COMPLEX_SYL:
                complex_w += 1
            elif 0 < wsyl <= COMPLEX_SYL:
                simple_w += 1
            if has_syl:
                words += 1

    return {
        "chars": chars, "spaces": spaces, "letters": letters,
        "syllabes": syllabes, "words": words, "sentences": sentences,
        "complex_words": complex_w, "simple_words": simple_w,
        "avg_slen": words / sentences if sentences else 0,   # слов / предложение
        "avg_syl": syllabes / words if words else 0,         # слогов / слово
        "c_share": complex_w * 100.0 / words if words else 0,  # % сложных слов
    }


def score(text):
    m = count_metrics(text)
    indices = {
        "Flesch-Kincaid Grade": fk_grade(m["syllabes"], m["words"], m["sentences"]),
        "Coleman-Liau":         coleman_liau(m["letters"], m["words"], m["sentences"]),
        "Dale-Chale":           dale_chale(m["complex_words"], m["words"], m["sentences"]),
        "SMOG":                 smog(m["complex_words"], m["sentences"]),
        "ARI":                  ari(m["letters"], m["words"], m["sentences"]),
    }
    vals = [v for v in indices.values() if v > 0]
    indices["СРЕДНЕЕ"] = sum(vals) / len(vals) if vals else 0
    return m, indices


# ─────────────────────────────────────────────────────────────────────────────
# 5. Чтение входа: .docx / .md / .txt / stdin + чистка markdown
# ─────────────────────────────────────────────────────────────────────────────
def read_docx(path):
    """Читает реальный .docx; если файл не zip (текстовый экспорт) — как текст."""
    import zipfile
    if not zipfile.is_zipfile(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def read_input(path):
    if path == "-":
        return sys.stdin.read()
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return read_docx(path)
    with open(path, encoding="utf-8") as f:
        return f.read()


def strip_markdown(text):
    """Убрать разметку, чтобы символы ##/**/`/--- не попадали в метрики."""
    text = re.sub(r"`[^`]*`", " ", text)            # инлайн-код / HUD-строки
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)  # заголовки -> текст без #
    text = re.sub(r"(?m)^\s*[-*_]{3,}\s*$", "", text)  # горизонтальные линии
    text = re.sub(r"[*_~>]+", "", text)             # **жирный** _курсив_ > цитата
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)  # ссылки/картинки
    return text


def split_chapters(text):
    """Разбить рукопись по '## Глава ...'. Возвращает [(заголовок, текст)]."""
    parts = re.split(r"(?m)^##\s+(Глава[^\n]*)$", text)
    if len(parts) < 3:
        return None  # нет глав — обрабатывать как единый текст
    chapters = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        chapters.append((title, body))
    return chapters


# ─────────────────────────────────────────────────────────────────────────────
# 6. Вывод
# ─────────────────────────────────────────────────────────────────────────────
def fmt_block(label, m, indices, width=64):
    out = [f"  {label}"]
    out.append(f"    слов: {m['words']:>6}   предложений: {m['sentences']:>5}   "
               f"ср.длина предл.: {m['avg_slen']:.1f} сл.")
    out.append(f"    слогов/слово: {m['avg_syl']:.2f}   сложных слов: {m['c_share']:.1f}%")
    out.append("    " + "-" * (width - 4))
    order = ["Flesch-Kincaid Grade", "Coleman-Liau", "Dale-Chale", "SMOG", "ARI", "СРЕДНЕЕ"]
    for k in order:
        v = indices[k]
        bar = "▌" * min(int(round(v)), 24)
        out.append(f"    {k:<22} {v:6.1f}  {bar}")
    avg = indices["СРЕДНЕЕ"]
    out.append(f"    → уровень: {grade_label(avg)}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(
        description="Читабельность русского текста (5 индексов plainrussian).")
    ap.add_argument("path", help="файл .md/.txt/.docx или '-' для stdin")
    ap.add_argument("--chapters", action="store_true",
                    help="разбить по '## Глава' и считать каждую отдельно")
    ap.add_argument("--raw", action="store_true",
                    help="не чистить markdown перед подсчётом")
    args = ap.parse_args()

    raw = read_input(args.path)

    print("=" * 64)
    print(f"ЧИТАБЕЛЬНОСТЬ — {os.path.basename(args.path)}")
    print("(индекс = лет обучения, нужных чтобы понять; меньше = доступнее)")
    print("=" * 64)

    if args.chapters:
        chapters = split_chapters(raw)   # делим по '## Глава' ДО чистки разметки
        if not chapters:
            print("  Главы '## Глава ...' не найдены — считаю как единый текст.\n")
        else:
            grades = []
            for title, body in chapters:
                body = body if args.raw else strip_markdown(body)
                m, idx = score(body)
                grades.append(idx["СРЕДНЕЕ"])
                print(fmt_block(title, m, idx))
                print()
            if grades:
                lo = min(range(len(grades)), key=lambda i: grades[i])
                hi = max(range(len(grades)), key=lambda i: grades[i])
                avg = sum(grades) / len(grades)
                print("-" * 64)
                print(f"  Книга: средний grade {avg:.1f}  ({grade_label(avg)})")
                print(f"  Легче всех: {chapters[lo][0]} ({grades[lo]:.1f})")
                print(f"  Тяжелее всех: {chapters[hi][0]} ({grades[hi]:.1f})")
            return

    text = raw if args.raw else strip_markdown(raw)
    m, idx = score(text)
    print(fmt_block("ВЕСЬ ТЕКСТ", m, idx))


if __name__ == "__main__":
    main()
