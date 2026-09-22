#!/usr/bin/env python3
"""Prepare and verify independent editorial review runs.

The tool never edits a manuscript. It binds reports to one source hash, creates
an isolated packet for a blind reader, locks completed reports, and checks the
shared issue ledger before later phases can be marked complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import sys


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
REPORTS = {
    "astra": "astra-diagnosis.md",
    "claude": "claude-diagnosis.md",
    "terra": "terra-diagnosis.md",
    "gemini_flash": "gemini-flash-diagnosis.md",
    "gemini": "gemini-blind-read.md",
    "reconciliation": "reconciliation.md",
    "verification": "verification.md",
}
DECISIONS = {"accepted", "rejected", "modified", "deferred"}


class EnsembleError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnsembleError(f"Cannot read JSON {path}: {exc}") from exc


def write_json(path: Path, data: object) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def inside(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise EnsembleError(f"Path is outside workspace: {path}") from exc
    return resolved


def relative(root: Path, path: Path) -> str:
    return inside(root, path).relative_to(root.resolve()).as_posix()


def locate(root: Path, value: str, *, base: Path | None = None) -> Path:
    raw = Path(value).expanduser()
    if raw.is_absolute():
        return inside(root, raw)
    candidates = []
    if base is not None:
        candidates.append(base / raw)
    candidates.append(root / raw)
    for candidate in candidates:
        if candidate.exists():
            return inside(root, candidate)
    return inside(root, candidates[0])


def project_and_book(root: Path, project_arg: str, book_id: str) -> tuple[dict, Path, dict, Path]:
    project_dir = locate(root, project_arg)
    project_file = project_dir / "project.json"
    if not project_file.is_file():
        raise EnsembleError(f"Missing project.json: {project_file}")
    project = read_json(project_file)
    if not isinstance(project, dict):
        raise EnsembleError("project.json must contain an object")
    entry = next(
        (item for item in project.get("books", []) if item.get("id") == book_id), None
    )
    if entry is None:
        raise EnsembleError(f"Book {book_id!r} is not listed in {project_file}")
    book_dir = inside(project_dir, project_dir / entry["path"])
    book_file = book_dir / "book.json"
    book = read_json(book_file)
    if not isinstance(book, dict) or book.get("book_id") != book_id:
        raise EnsembleError(f"Book manifest disagrees with requested ID: {book_file}")
    return project, project_dir, book, book_dir


def choose_source(
    root: Path,
    book: dict,
    book_dir: Path,
    source_arg: str | None,
    reader_arg: str | None,
) -> tuple[dict, dict]:
    records = []
    working = book.get("working_revision")
    master = book.get("master")
    if isinstance(working, dict) and working.get("path"):
        records.append(("working_revision", working))
    if isinstance(master, dict) and master.get("path"):
        records.append(("master", master))

    selected_name = "explicit"
    selected = None
    if source_arg:
        source = locate(root, source_arg, base=book_dir)
        for name, record in records:
            declared = locate(root, record["path"], base=book_dir)
            if declared == source:
                selected_name, selected = name, record
                break
    elif records:
        selected_name, selected = records[0]
        source = locate(root, selected["path"], base=book_dir)
    else:
        raise EnsembleError("No source supplied and book.json has no working revision or master")

    if not source.is_file():
        raise EnsembleError(f"Source does not exist: {source}")
    actual = sha256(source)
    if selected and selected.get("sha256") and selected["sha256"] != actual:
        raise EnsembleError(
            f"Source hash mismatch: declared {selected['sha256']}, actual {actual}"
        )
    source_record = {
        "path": relative(root, source),
        "sha256": actual,
        "status": selected.get("status", selected_name) if selected else "explicit",
        "authority": selected.get("authority", selected_name) if selected else "explicit task source",
    }

    if reader_arg:
        reader = locate(root, reader_arg, base=book_dir)
        relation = "supplied_reader_projection"
    elif source.suffix.lower() in {".md", ".txt"}:
        reader = source
        relation = "source_text"
    else:
        raise EnsembleError(
            "Binary source requires --reader-file with a verified text projection"
        )
    if not reader.is_file():
        raise EnsembleError(f"Reader file does not exist: {reader}")
    try:
        reader.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise EnsembleError(f"Reader file must be UTF-8 text: {reader}") from exc
    reader_record = {
        "path": relative(root, reader),
        "sha256": sha256(reader),
        "relation": relation,
    }
    return source_record, reader_record


def render(template: Path, values: dict[str, str]) -> str:
    text = template.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    leftovers = re.findall(r"{{[A-Z0-9_]+}}", text)
    if leftovers:
        raise EnsembleError(f"Unfilled template values in {template}: {leftovers}")
    return text


def run_dir_from_arg(root: Path, value: str) -> Path:
    path = locate(root, value)
    if not path.is_dir() or not (path / "run.json").is_file():
        raise EnsembleError(f"Not an ensemble run directory: {path}")
    return path


def load_run(root: Path, value: str) -> tuple[Path, dict]:
    run_dir = run_dir_from_arg(root, value)
    data = read_json(run_dir / "run.json")
    if not isinstance(data, dict):
        raise EnsembleError("run.json must contain an object")
    return run_dir, data


def validate_issue(item: dict) -> None:
    required = {
        "id",
        "origin_reports",
        "category",
        "severity",
        "certainty",
        "locations",
        "observation",
        "reader_effect",
        "evidence",
        "proposed_actions",
        "dependencies",
        "author_decision",
        "implementation",
        "verification",
    }
    missing = required - set(item)
    if missing:
        raise EnsembleError(f"Issue {item.get('id', '<unknown>')} lacks {sorted(missing)}")
    if not re.fullmatch(r"ENS-[0-9]{3,}", str(item["id"])):
        raise EnsembleError(f"Invalid issue ID: {item['id']}")
    if not item["origin_reports"] or not set(item["origin_reports"]) <= {
        "astra",
        "claude",
        "terra",
        "gemini",
        "gemini_flash",
    }:
        raise EnsembleError(f"Invalid origin_reports in {item['id']}")
    decision = item["author_decision"]
    if decision.get("status") not in DECISIONS | {"pending"}:
        raise EnsembleError(f"Invalid author decision in {item['id']}")
    if decision.get("status") in DECISIONS and not decision.get("basis"):
        raise EnsembleError(f"Author decision lacks basis in {item['id']}")
    if item["implementation"].get("status") not in {
        "not_started",
        "not_applicable",
        "applied",
        "partial",
    }:
        raise EnsembleError(f"Invalid implementation status in {item['id']}")
    if item["verification"].get("status") not in {
        "not_run",
        "passed",
        "failed",
        "stale",
    }:
        raise EnsembleError(f"Invalid verification status in {item['id']}")


def validate_ledger(run: dict, path: Path) -> dict:
    ledger = read_json(path)
    if not isinstance(ledger, dict):
        raise EnsembleError("issue-ledger.json must contain an object")
    for key in ("run_id", "project_id", "book_id", "source_sha256"):
        expected = run["source"]["sha256"] if key == "source_sha256" else run[key]
        if ledger.get(key) != expected:
            raise EnsembleError(f"Issue ledger {key} disagrees with run.json")
    items = ledger.get("items")
    if not isinstance(items, list):
        raise EnsembleError("Issue ledger items must be an array")
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise EnsembleError("Every issue must be an object")
        validate_issue(item)
        if item["id"] in seen:
            raise EnsembleError(f"Duplicate issue ID: {item['id']}")
        seen.add(item["id"])
    return ledger


def validate_report(text: str, run: dict, role: str) -> None:
    expected = [
        f"Run ID: `{run['run_id']}`",
        f"Source SHA-256: `{run['source']['sha256']}`",
        f"Role: `{role}`",
        "Status: final",
    ]
    missing = [line for line in expected if line not in text]
    if missing:
        raise EnsembleError(f"Report {role} is not final or has wrong metadata: {missing}")
    if role != "author":
        for field in ("Model", "Client"):
            match = re.search(rf"^{field}:\s*(\S.*)$", text, re.M)
            if not match or not match.group(1).strip():
                raise EnsembleError(f"Report {role} lacks {field} metadata")
    if "<!-- FILL" in text or "{{" in text:
        raise EnsembleError(f"Report {role} still contains template markers")
    if len(text.strip()) < 300:
        raise EnsembleError(f"Report {role} is unexpectedly short")


def diagnosis_roles(run: dict) -> tuple:
    if run.get("schema_version") == 3:
        required = ("astra", "terra", "gemini_flash", "gemini")
        if run.get("required_diagnoses") != list(required):
            raise EnsembleError("Schema 3 requires Astra, Terra, Gemini Flash and Gemini Pro")
        if not run.get("review_policy_basis"):
            raise EnsembleError("Schema 3 requires an explicit review-policy basis")
        return required
    if run.get("schema_version") == 2:
        required = ("astra", "claude", "gemini_flash", "gemini")
        if run.get("required_diagnoses") != list(required):
            raise EnsembleError("Schema 2 requires Astra, Opus, Gemini Flash and Gemini Pro")
        return required
    return ("astra", "claude", "gemini")


def refresh_status(run: dict) -> None:
    first = [run["reports"][key]["status"] for key in diagnosis_roles(run)]
    if run["reports"]["verification"]["status"] == "locked":
        run["status"] = "verified"
    elif run["author_decisions"]["status"] == "locked":
        run["status"] = "author_decided"
    elif run["reports"]["reconciliation"]["status"] == "locked":
        run["status"] = "reconciled"
    elif all(status == "locked" for status in first):
        run["status"] = "diagnoses_complete"
    elif any(status == "locked" for status in first):
        run["status"] = "diagnosis_in_progress"
    else:
        run["status"] = "prepared"


def cmd_init(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    project, _, book, book_dir = project_and_book(root, args.project, args.book)
    if not RUN_ID_RE.fullmatch(args.run_id):
        raise EnsembleError("run-id must contain lowercase letters, digits and hyphens")
    source, reader = choose_source(root, book, book_dir, args.source, args.reader_file)
    terra_policy = getattr(args, "review_policy", "opus") == "terra"
    basis = getattr(args, "review_policy_basis", None)
    if terra_policy and not basis:
        raise EnsembleError("Terra policy requires --review-policy-basis")
    run_dir = book_dir / "audit" / "ensemble" / args.run_id
    if run_dir.exists():
        raise EnsembleError(f"Run already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    values = {
        "RUN_ID": args.run_id,
        "PROJECT_ID": project["project_id"],
        "BOOK_ID": args.book,
        "SOURCE_SHA256": source["sha256"],
        "READER_SHA256": reader["sha256"],
    }
    template_dir = root / "editorial" / "templates"
    active_reports = {k: v for k, v in REPORTS.items() if k != ("claude" if terra_policy else "terra")}
    for filename in active_reports.values():
        (run_dir / filename).write_text(
            render(template_dir / filename, values), encoding="utf-8"
        )
    decisions_file = "author-decisions.md"
    (run_dir / decisions_file).write_text(
        render(template_dir / decisions_file, values), encoding="utf-8"
    )
    (run_dir / "issue-ledger.json").write_text(
        render(template_dir / "issue-ledger.json", values), encoding="utf-8"
    )
    run = {
        "schema_version": 3 if terra_policy else 2,
        "run_id": args.run_id,
        "project_id": project["project_id"],
        "book_id": args.book,
        "created_at": now(),
        "status": "prepared",
        "language": getattr(args, "language", None) or book.get("canonical_language") or project.get("language_policy", {}).get("legacy_existing_source", "ru"),
        "required_diagnoses": ["astra", "terra" if terra_policy else "claude", "gemini_flash", "gemini"],
        **({"review_policy_basis": basis} if terra_policy else {}),
        "source": source,
        "reader": reader,
        "independence": {
            "astra": "must not read current Claude or Gemini reports before lock",
            "claude": "must not read current Astra or Gemini reports before lock",
            "terra": "independent literary diagnosis; no current peer reports before lock",
            "gemini_flash": "independent full-text literary/continuity analysis; no current peer reports",
            "gemini": "isolated packet only; no repository canon, audits or change hints",
        },
        "reports": {
            role: {"file": filename, "status": "draft", "sha256": None}
            for role, filename in active_reports.items()
        },
        "author_decisions": {
            "file": decisions_file,
            "status": "draft",
            "sha256": None,
        },
        "issue_ledger": "issue-ledger.json",
    }
    write_json(run_dir / "run.json", run)
    return {
        "run": relative(root, run_dir),
        "source_sha256": source["sha256"],
        "reader_sha256": reader["sha256"],
        "status": "prepared",
    }


def cmd_record(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    run_dir, run = load_run(root, args.run)
    role = args.role
    integrity = verify_run(root, run_dir, run, False)
    if integrity["errors"]:
        raise EnsembleError("; ".join(integrity["errors"]))
    if role not in run["reports"]:
        raise EnsembleError("Role not present in this historical run; create a new run")
    if role == "reconciliation" and not all(
        run["reports"][key]["status"] == "locked"
        for key in diagnosis_roles(run)
    ):
        raise EnsembleError("Reconciliation requires all mandatory locked diagnoses")
    if role == "verification" and run["author_decisions"]["status"] != "locked":
        raise EnsembleError("Verification requires locked author decisions")
    entry = run["reports"][role]
    target = run_dir / entry["file"]
    if args.input:
        if entry["status"] == "locked":
            raise EnsembleError(f"Locked report cannot be replaced: {target}")
        supplied = Path(args.input).expanduser().resolve()
        if not supplied.is_file():
            raise EnsembleError(f"Input report does not exist: {supplied}")
        target.write_bytes(supplied.read_bytes())
    text = target.read_text(encoding="utf-8")
    validate_report(text, run, role)
    digest = sha256(target)
    if entry["status"] == "locked":
        if entry["sha256"] != digest:
            raise EnsembleError(f"Locked report changed: {target}")
        return {"role": role, "status": "already_locked", "sha256": digest}

    ledger_path = run_dir / run["issue_ledger"]
    ledger = validate_ledger(run, ledger_path)
    if role == "reconciliation":
        ledger["status"] = "reconciled"
        write_json(ledger_path, ledger)
    if role == "verification":
        for item in ledger["items"]:
            decision = item["author_decision"]["status"]
            if decision in {"accepted", "modified"}:
                if item["implementation"]["status"] != "applied":
                    raise EnsembleError(f"Accepted issue is not applied: {item['id']}")
                if item["verification"]["status"] != "passed":
                    raise EnsembleError(f"Applied issue is not verified: {item['id']}")
        ledger["status"] = "verified"
        write_json(ledger_path, ledger)

    entry["status"] = "locked"
    entry["sha256"] = digest
    entry["locked_at"] = now()
    refresh_status(run)
    write_json(run_dir / "run.json", run)
    return {"role": role, "status": "locked", "sha256": digest, "run_status": run["status"]}


def cmd_lock_decisions(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    run_dir, run = load_run(root, args.run)
    if run["reports"]["reconciliation"]["status"] != "locked":
        raise EnsembleError("Author decisions require a locked reconciliation")
    entry = run["author_decisions"]
    path = run_dir / entry["file"]
    text = path.read_text(encoding="utf-8")
    validate_report(text, run, "author")
    ledger_path = run_dir / run["issue_ledger"]
    ledger = validate_ledger(run, ledger_path)
    pending = [
        item["id"]
        for item in ledger["items"]
        if item["author_decision"]["status"] == "pending"
    ]
    if pending:
        raise EnsembleError(f"Author decisions are still pending: {pending}")
    if ledger["items"]:
        if not re.search(r"^Decision: (accept|reject|modify|defer)$", text, re.M):
            raise EnsembleError("author-decisions.md lacks explicit Decision lines")
    elif "Decision: no_changes" not in text:
        raise EnsembleError("Empty ledger requires Decision: no_changes")
    digest = sha256(path)
    if entry["status"] == "locked" and entry["sha256"] != digest:
        raise EnsembleError("Locked author decisions changed")
    entry["status"] = "locked"
    entry["sha256"] = digest
    entry["locked_at"] = entry.get("locked_at", now())
    ledger["status"] = "author_decided"
    write_json(ledger_path, ledger)
    refresh_status(run)
    write_json(run_dir / "run.json", run)
    return {"status": "locked", "sha256": digest, "issues": len(ledger["items"])}


def cmd_blind_pack(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    run_dir, run = load_run(root, args.run)
    integrity = verify_run(root, run_dir, run, False)
    if integrity["errors"]:
        raise EnsembleError("; ".join(integrity["errors"]))
    if run["reports"]["gemini"]["status"] == "locked":
        raise EnsembleError("Gemini report is already locked")
    if args.out:
        out = Path(args.out).expanduser().resolve()
    else:
        out = Path("/tmp/books-editorial-ensemble") / f"{run['run_id']}-gemini"
    try:
        out.relative_to(root)
    except ValueError:
        pass
    else:
        raise EnsembleError("Blind packet must be outside the repository")
    if out.exists():
        raise EnsembleError(f"Blind packet already exists: {out}")
    out.mkdir(parents=True)
    reader = inside(root, root / run["reader"]["path"])
    manuscript_name = "MANUSCRIPT" + (reader.suffix.lower() or ".txt")
    shutil.copy2(reader, out / manuscript_name)
    shutil.copy2(run_dir / REPORTS["gemini"], out / "REPORT.md")
    skill_source = root / ".agents" / "skills" / "ru-cold-reader"
    skill_target = out / ".gemini" / "skills" / "ru-cold-reader"
    shutil.copytree(skill_source, skill_target)
    packet = {
        "schema_version": 1,
        "run_id": run["run_id"],
        "source_sha256": run["source"]["sha256"],
        "reader_sha256": run["reader"]["sha256"],
        "manuscript": manuscript_name,
        "report": "REPORT.md",
        "allowed_inputs": ["RUN.json", "GEMINI.md", manuscript_name, "REPORT.md", ".gemini/skills/ru-cold-reader"],
    }
    write_json(out / "RUN.json", packet)
    (out / "GEMINI.md").write_text(
        "# Изолированное холодное чтение\n\n"
        "Это отдельный читательский пакет. Используйте навык `ru-cold-reader`. "
        "Читайте только файлы из `RUN.json`; не ищите родительский Git-репозиторий, "
        "канон, прежние аудиты или сведения о правках. Запишите результат в `REPORT.md` "
        "и не изменяйте рукопись.\n",
        encoding="utf-8",
    )
    (out / "START.txt").write_text(
        "Use agy CLI only, in a fresh isolated session with the ru-cold-reader instructions supplied explicitly. "
        "Do not use gemini CLI or assume another client's skill-loading commands work in agy. "
        "Read only RUN.json allowed_inputs; return REPORT.md without editing the manuscript.\n",
        encoding="utf-8",
    )
    return {
        "packet": str(out),
        "manuscript": manuscript_name,
        "reader_sha256": sha256(out / manuscript_name),
        "next": "use agy CLI for Gemini in a fresh isolated session, finish REPORT.md, then import with record --role gemini --input REPORT.md",
    }


def verify_run(root: Path, run_dir: Path, run: dict, require_complete: bool) -> dict:
    errors = []
    try:
        if run.get("schema_version") not in {1, 2, 3} or not RUN_ID_RE.fullmatch(run.get("run_id", "")):
            errors.append("invalid run identity")
        required = diagnosis_roles(run)
        if not set(required).issubset(run["reports"]):
            errors.append("required diagnosis report is missing")
        for key in ("source", "reader"):
            record = run[key]
            path = inside(root, root / record["path"])
            if not path.is_file():
                errors.append(f"missing {key}: {path}")
            elif sha256(path) != record["sha256"]:
                errors.append(f"stale {key} hash")
        ledger = validate_ledger(run, run_dir / run["issue_ledger"])
        for role, entry in run["reports"].items():
            path = run_dir / entry["file"]
            if not path.is_file():
                errors.append(f"missing report {role}")
            elif entry["status"] == "locked" and sha256(path) != entry["sha256"]:
                errors.append(f"locked report changed: {role}")
        decision_entry = run["author_decisions"]
        decision_path = run_dir / decision_entry["file"]
        if decision_entry["status"] == "locked" and sha256(decision_path) != decision_entry["sha256"]:
            errors.append("locked author decisions changed")
        if require_complete:
            if run.get("status") != "verified":
                errors.append("run is not verified")
            completion_roles = (*required, "reconciliation", "verification")
            if any(run["reports"][role]["status"] != "locked" for role in completion_roles):
                errors.append("not all reports are locked")
            if decision_entry["status"] != "locked":
                errors.append("author decisions are not locked")
            if ledger.get("status") != "verified":
                errors.append("issue ledger is not verified")
    except (KeyError, TypeError, EnsembleError) as exc:
        errors.append(str(exc))
    return {
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "source_sha256": run.get("source", {}).get("sha256"),
        "result": "passed" if not errors else "failed",
        "errors": errors,
    }


def cmd_verify(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    run_dir, run = load_run(root, args.run)
    result = verify_run(root, run_dir, run, args.require_complete)
    if result["errors"]:
        raise EnsembleError("; ".join(result["errors"]))
    return result


def cmd_status(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    run_dir, run = load_run(root, args.run)
    check = verify_run(root, run_dir, run, False)
    return {
        "run": relative(root, run_dir),
        "run_id": run["run_id"],
        "status": run["status"],
        "source_sha256": run["source"]["sha256"],
        "reports": {key: value["status"] for key, value in run["reports"].items()},
        "author_decisions": run["author_decisions"]["status"],
        "integrity": check["result"],
        "errors": check["errors"],
    }


def cmd_validate_schemas(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    schema_dir = root / "editorial" / "schemas"
    template_dir = root / "editorial" / "templates"
    checked = []
    for path in sorted(schema_dir.glob("*.json")):
        read_json(path)
        checked.append(relative(root, path))
    ledger_template = read_json(template_dir / "issue-ledger.json")
    if not isinstance(ledger_template, dict) or ledger_template.get("schema_version") != 1:
        raise EnsembleError("Invalid issue ledger template")
    skills = []
    for path in sorted((root / ".agents" / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\nname:" not in text or "\ndescription:" not in text:
            raise EnsembleError(f"Invalid skill frontmatter: {path}")
        if "TODO" in text:
            raise EnsembleError(f"Unfinished skill: {path}")
        skills.append(path.parent.name)
    claude_skills = root / ".claude" / "skills"
    if not claude_skills.exists() or claude_skills.resolve() != (root / ".agents" / "skills").resolve():
        raise EnsembleError(".claude/skills must resolve to .agents/skills")
    expected = {
        "ru-chief-editor",
        "ru-literary-editor",
        "ru-cold-reader",
        "ru-editorial-reconciler",
        "ru-approved-revision",
    }
    if not expected.issubset(skills):
        raise EnsembleError(f"Unexpected skill set: {skills}")
    return {"result": "passed", "schemas": checked, "skills": skills}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", default=str(SCRIPT_ROOT), help="workspace root")
    commands = result.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create a version-bound ensemble run")
    init.add_argument("--project", required=True, help="project directory, for example riokka")
    init.add_argument("--book", required=True)
    init.add_argument("--run-id", required=True)
    init.add_argument("--source", help="explicit source path")
    init.add_argument("--reader-file", help="verified UTF-8 reading projection")
    init.add_argument("--language", choices=["uk", "en", "ru"], help="Actual source language, not the future edition language")
    init.add_argument("--review-policy", choices=["opus", "terra"], default="opus", help="Explicit per-run policy; historical default unchanged")
    init.add_argument("--review-policy-basis", help="Author instruction record required for Terra policy")
    init.set_defaults(func=cmd_init)

    record = commands.add_parser("record", help="lock a completed report")
    record.add_argument("--run", required=True)
    record.add_argument("--role", required=True, choices=sorted(REPORTS))
    record.add_argument("--input", help="copy an external report before locking")
    record.set_defaults(func=cmd_record)

    decisions = commands.add_parser("lock-decisions", help="lock explicit author decisions")
    decisions.add_argument("--run", required=True)
    decisions.set_defaults(func=cmd_lock_decisions)

    blind = commands.add_parser("blind-pack", help="create an isolated Gemini reader packet")
    blind.add_argument("--run", required=True)
    blind.add_argument("--out", help="output directory outside the repository")
    blind.set_defaults(func=cmd_blind_pack)

    verify = commands.add_parser("verify", help="check run hashes and stage invariants")
    verify.add_argument("--run", required=True)
    verify.add_argument("--require-complete", action="store_true")
    verify.set_defaults(func=cmd_verify)

    status = commands.add_parser("status", help="show current run state")
    status.add_argument("--run", required=True)
    status.set_defaults(func=cmd_status)

    schemas = commands.add_parser("validate-schemas", help="validate shared schemas and skills")
    schemas.set_defaults(func=cmd_validate_schemas)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        output = args.func(args)
    except (EnsembleError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"result": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
