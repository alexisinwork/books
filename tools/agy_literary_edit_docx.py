#!/usr/bin/env python3
"""Run a source-preserving Ukrainian literary edit over a DOCX in chunks.

The source DOCX is never overwritten. Each model response must contain one
edited string for every non-empty body paragraph in the input chunk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from docx import Document


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(path: Path) -> list[str]:
    if path.suffix.lower() in {".md", ".txt"}:
        return [p for p in path.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    return [p.text for p in Document(path).paragraphs if p.text.strip()]


def ask(model: str, effort: str, chunk: list[dict], context: str, timeout: int) -> list[str]:
    prompt = f"""ВІДПОВІДАЙ ОДРАЗУ. НЕ ВИКОРИСТОВУЙ ЖОДНИХ ІНСТРУМЕНТІВ, КОМАНД, ФАЙЛОВОГО ДОСТУПУ АБО ПОШУКУ.
Увесь потрібний матеріал уже вставлено нижче; не шукай його в робочому каталозі.
Ти — український літературний редактор. Виконай обережну редактуру уривка роману.
Контекст тому: {context}
Виправляй природність української, граматику, керування, милозвучність, неточні слова,
кальки, повтори й ритм там, де це справді покращує прозу. Зберігай авторський голос,
POV, час, факти, послідовність подій, розділову структуру, імена, числа та навмисну
сухість або розмовність. Не додавай подій, пояснень, психології чи нових деталей.
Заголовки, службові рядки й короткі технічні примітки редагуй лише мовно. Якщо абзац
добрий, поверни його без змін. Поверни тільки JSON за схемою, без markdown.
Має бути рівно {len(chunk)} рядків у тому самому порядку; не об'єднуй і не розділяй абзаци.

Вхідні абзаци:
{json.dumps(chunk, ensure_ascii=False)}
"""
    cmd = ["agy", "--new-project", "--model", model, "--output-format", "stream-json",
           "--input-format", "stream-json", "--mode", "plan", "--sandbox",
           "--print-timeout", "20m"]
    if effort:
        cmd.extend(["--effort", effort])
    stdin = json.dumps({"event": "user", "message": {"content": prompt}}, ensure_ascii=False) + "\n"
    result = subprocess.run(cmd, input=stdin, capture_output=True, text=True, encoding="utf-8",
                            timeout=timeout)
    raw = result.stdout.strip()
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:] or raw[-2000:])
    events = [json.loads(line) for line in raw.splitlines() if line.strip()]
    result_events = [event["result"] for event in events if event.get("event") == "result"]
    if not result_events:
        raise RuntimeError(result.stderr[-2000:] or raw[-2000:])
    envelope = result_events[-1]
    if envelope.get("status") != "SUCCESS":
        raise RuntimeError(envelope.get("error") or envelope)
    response = envelope.get("response", "").strip()
    if not response:
        response = "".join(
            event.get("step_update", {}).get("text_delta", "")
            for event in events
            if event.get("event") == "step_update"
        ).strip()
    if response:
        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model response is not JSON: {response[:2000]!r}") from exc
    else:
        data = envelope.get("structuredContent") or envelope.get("output")
        if not isinstance(data, dict):
            raise RuntimeError(f"Model returned no text; events={len(events)} last={events[-3:]}")
    values = data if isinstance(data, list) else data.get("paragraphs")
    if isinstance(values, list) and all(isinstance(x, dict) and isinstance(x.get("text"), str) for x in values):
        values = [x["text"] for x in values]
    if not isinstance(values, list) or len(values) != len(chunk) or not all(isinstance(x, str) for x in values):
        raise RuntimeError(f"Invalid paragraph response: expected {len(chunk)}, got {len(values) if isinstance(values, list) else type(values)}")
    return values


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--projection", type=Path, required=True)
    ap.add_argument("--metadata", type=Path, required=True)
    ap.add_argument("--model", default="gemini-3.8-flash-high")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--max-chars", type=int, default=85000)
    ap.add_argument("--context", required=True)
    ap.add_argument("--timeout", type=int, default=1500)
    args = ap.parse_args()
    source = args.source.resolve()
    original = extract(source)
    edited: list[str] = []
    chunks: list[list[dict]] = []
    current: list[dict] = []
    size = 0
    for idx, text in enumerate(original):
        item = {"id": idx, "text": text}
        if current and size + len(text) > args.max_chars:
            chunks.append(current); current = []; size = 0
        current.append(item); size += len(text)
    if current:
        chunks.append(current)
    started = time.time()
    for n, chunk in enumerate(chunks, 1):
        print(f"chunk {n}/{len(chunks)} paragraphs {chunk[0]['id']}-{chunk[-1]['id']}", flush=True)
        edited.extend(ask(args.model, args.effort, chunk, args.context, args.timeout))
    if len(edited) != len(original):
        raise RuntimeError("Edited paragraph count differs from source")
    args.projection.parent.mkdir(parents=True, exist_ok=True)
    args.projection.write_text("\n\n".join(edited) + "\n", encoding="utf-8")
    metadata = {
        "source_path": str(source), "source_sha256": sha256(source),
        "source_paragraphs": len(original), "chunks": len(chunks),
        "model": args.model, "effort": args.effort,
        "projection_path": str(args.projection.resolve()),
        "projection_sha256": sha256(args.projection),
        "elapsed_seconds": round(time.time() - started, 1),
        "status": "model_edit_complete",
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
