#!/usr/bin/env python3
"""Create only the three explicitly delegated native-review input versions."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile


SPECS = [("story-01-reptiloids", 2, 3), ("story-02-fair-killer", 2, 3),
         ("story-03-chaos-logic", 3, 4)]
TASK = "stories-ru-uk-pilot/adaptation/native-review-2026-09-14/TASK.json"
RULE_UPDATE = "stories-ru-uk-pilot/adaptation/native-review-2026-09-14/pipeline-work/native-inputs/SELECTED-RULES-V2.json"
PREVIOUS_SELECTION = "stories-ru-uk-pilot/release/SELECTION-2026-09-14-v3.json"
STYLE = "BOOK_SYSTEM/LANGUAGES/uk/STYLE.md"
EXTRA = ["BOOK_SYSTEM/LANGUAGES/uk/NATURALNESS.md",
         ".agents/skills/book-language-review/SKILL.md",
         ".agents/skills/literary-adaptation/SKILL.md",
         "stories-ru-uk-pilot/STYLE.md", "BOOK_SYSTEM/CORE.md", TASK,
         "BOOK_SYSTEM/ADAPTATION/prompts/target-only-uk.md"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def encoded(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data if isinstance(data, bytes) else encoded(data))


def load_translation_tool(root):
    spec = importlib.util.spec_from_file_location("native_input_translation", root / "tools/literary_translation.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    return tool


def validate(root, records, tool, require_isolated=False):
    results = []
    for record in records:
        manifest_path = root / record["manifest"]["path"]
        ready = root / record["ready_packet"]
        manifest = read(manifest_path)
        if digest(manifest_path.read_bytes()) != record["manifest"]["sha256"]:
            raise ValueError("New manifest changed")
        if digest((root / manifest["packet"]["path"]).read_bytes()) != manifest["packet"]["sha256"]:
            raise ValueError("New packet changed")
        packet, segments = tool.verify_packet(root, ready)
        if packet["inputs"] != manifest["inputs"]:
            raise ValueError("Manifest and packet input sets disagree")
        for entry in manifest["inputs"]:
            tool.checked(root, entry)
            if not (root / entry["path"]).resolve().is_relative_to(ready.resolve() / "context"):
                raise ValueError("Active input points outside its frozen context")
        snapshot = read(root / manifest["context_snapshot"]["path"])
        if snapshot["snapshots"] != manifest["inputs"][:-1]:
            raise ValueError("Context index and active snapshots disagree")
        if manifest["inputs"][-1]["path"] != manifest["context_snapshot"]["path"]:
            raise ValueError("Context index is not itself checked as a frozen input")
        present_origins = sum((root / entry["origin_path"]).exists() for entry in snapshot["snapshots"])
        if require_isolated and present_origins:
            raise ValueError("Staging unexpectedly contains live mutable origins")
        glossary = manifest["preserved_translation_glossary"]
        if digest((root / glossary["path"]).read_bytes()) != glossary["translation_glossary_sha256"]:
            raise ValueError("Translation glossary checksum changed")
        if manifest["source_sha256"] != packet["source"]["sha256"] or manifest["source_segments_sha256"] != packet["source_segments_sha256"]:
            raise ValueError("Source identity changed while freezing context")
        results.append({"book_id": manifest["book_id"], "result": "passed_packet_and_frozen_input_integrity",
                        "active_inputs": len(manifest["inputs"]), "context_snapshots": len(snapshot["snapshots"]),
                        "source_segments": len(segments), "source_sha256": packet["source"]["sha256"],
                        "source_segments_sha256": packet["source_segments_sha256"],
                        "source_reader_sha256": packet["source_reader_sha256"],
                        "translation_glossary_sha256": glossary["translation_glossary_sha256"],
                        "tested_without_live_mutable_origins": require_isolated,
                        "live_mutable_origin_paths_present": present_origins,
                        "literary_quality": "not_assessed", "models_run": False})
    return results


def create(root, audit):
    root, audit = root.resolve(), audit.resolve()
    cache, protected, preparations, selected_sources = {}, {}, [], {}
    timestamp = datetime.now(timezone.utc).isoformat()

    def capture(relative):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Origin escapes repository")
        if relative not in cache:
            if relative in selected_sources:
                chosen = selected_sources[relative]
                cache[relative] = (root / chosen["selected_copy"]).read_bytes()
                if digest(cache[relative]) != chosen["sha256"]:
                    raise ValueError("Selected rule copy changed: " + relative)
            else:
                cache[relative] = path.read_bytes()
        return cache[relative]

    task = json.loads(capture(TASK))
    previous_selection = json.loads(capture(PREVIOUS_SELECTION))
    selected_inputs = {entry["book_id"]: entry for entry in previous_selection["books"]}
    protected[PREVIOUS_SELECTION] = digest(capture(PREVIOUS_SELECTION))
    rule_update = json.loads(capture(RULE_UPDATE))
    selected_sources.update({entry["path"]: entry for entry in rule_update["files"]})
    for rule in rule_update["files"]:
        if digest(capture(rule["path"])) != rule["sha256"]:
            raise ValueError("Final rule bytes differ from SELECTED-RULES-V2: " + rule["path"])
        protected[rule["selected_copy"]] = rule["sha256"]
    protected[RULE_UPDATE] = digest(cache[RULE_UPDATE])
    for path in EXTRA:
        capture(path)
    for name in ["tools/run_literary_model.py", "tools/run_book_review.py", "tools/literary_translation.py"]:
        protected[name] = digest(capture(name))
    task_books = {entry["book_id"]: entry for entry in task["books"]}
    for book_id, previous, current in SPECS:
        edition = Path("stories-ru-uk-pilot/books") / book_id / "editions/uk"
        old_manifest_path = (edition / f"INPUTS-V{previous}.json").as_posix()
        new_manifest = (edition / f"INPUTS-V{current}.json").as_posix()
        new_ready = (edition / f"preparation/pilot/ready-v{current}").as_posix()
        if (root / new_manifest).exists() or (root / new_ready).exists():
            raise ValueError("New version already exists; do not overwrite: " + book_id)
        old_manifest = json.loads(capture(old_manifest_path))
        if selected_inputs[book_id]["input_manifest"] != old_manifest_path or selected_inputs[book_id]["input_manifest_sha256"] != digest(capture(old_manifest_path)):
            raise ValueError("Previous input manifest differs from the immutable release selection")
        old_packet_path = old_manifest["packet"]["path"]
        old_packet = json.loads(capture(old_packet_path))
        old_ready = Path(old_packet_path).parent
        if digest(capture(old_packet_path)) != old_manifest["packet"]["sha256"]:
            raise ValueError("Previous packet changed")
        if old_packet["inputs"] != old_manifest["inputs"]:
            raise ValueError("Previous manifest and packet have different input sets")
        if old_manifest["book_id"] != book_id or old_packet["book_id"] != book_id:
            raise ValueError("Previous inputs belong to another book")
        for ref in [old_packet["source"], old_packet["book_manifest"]]:
            if digest(capture(ref["path"])) != ref["sha256"]:
                raise ValueError("Original source or inventory changed")
            protected[ref["path"]] = ref["sha256"]
        for name, key in [("source-segments.json", "source_segments_sha256"),
                          (old_packet.get("source_reader_file", "source.ru.txt"), "source_reader_sha256")]:
            old_path = (old_ready / name).as_posix()
            if digest(capture(old_path)) != old_packet[key]:
                raise ValueError("Previous source projection changed")
            protected[old_path] = old_packet[key]
        protected[old_manifest_path] = digest(capture(old_manifest_path))
        protected[old_packet_path] = digest(capture(old_packet_path))
        book_json = (edition.parents[1] / "book.json").as_posix()
        protected[book_json] = digest(capture(book_json))
        base_translation = str(Path(task_books[book_id]["base_target"]).with_name("translation.json"))
        translation = json.loads(capture(base_translation))
        if digest(capture(base_translation)) != task_books[book_id]["base_translation_sha256"]:
            raise ValueError("Historical translation bytes differ from TASK")
        protected[base_translation] = digest(capture(base_translation))
        base_target = task_books[book_id]["base_target"]
        if digest(capture(base_target)) != task_books[book_id]["base_target_sha256"]:
            raise ValueError("Historical target bytes differ from TASK")
        protected[base_target] = digest(capture(base_target))
        refs, changes, seen = [], [], set()
        for entry in old_manifest["inputs"] + [{"path": name} for name in EXTRA]:
            origin = entry["path"]
            if origin in seen:
                continue
            seen.add(origin)
            payload = capture(origin)
            actual_sha = digest(payload)
            old_sha = entry.get("sha256")
            if old_sha is not None and actual_sha != old_sha and origin != STYLE:
                raise ValueError("Unexpected mutable-origin drift; review before freezing: " + origin)
            snapshot_path = (Path(new_ready) / "context" / origin).as_posix()
            ref = {"path": snapshot_path, "sha256": actual_sha,
                   "origin_path": origin, "origin_sha256": actual_sha,
                   "role": "frozen_context_snapshot"}
            if origin in selected_sources:
                ref["snapshot_source_path"] = selected_sources[origin]["selected_copy"]
                ref["snapshot_source_sha256"] = actual_sha
                ref["selection_record"] = {"path": RULE_UPDATE, "sha256": digest(cache[RULE_UPDATE])}
            if old_sha is not None:
                ref["previous_frozen_sha256"] = old_sha
            else:
                ref["addition_basis"] = "Current full native-review task and explicitly delegated context additions"
            if old_sha is not None and actual_sha != old_sha:
                ref["origin_change_status"] = "current_rules_captured_for_new_native_pass"
                changes.append({"origin_path": origin, "previous_frozen_sha256": old_sha,
                                "new_snapshot_sha256": actual_sha,
                                "reason": "Current Ukrainian writing rules explicitly requested for the full native-language pass; prior packages remain unchanged."})
            refs.append(ref)
        glossary_origin = (edition / "glossary.json").as_posix()
        glossary = next(entry for entry in refs if entry["origin_path"] == glossary_origin)
        if glossary["sha256"] != translation["glossary_sha256"]:
            raise ValueError("Current glossary no longer matches the unchanged translation glossary SHA")
        protected[glossary_origin] = glossary["sha256"]
        preparations.append({"book_id": book_id, "edition": edition.as_posix(), "previous": previous,
                             "current": current, "old_manifest_path": old_manifest_path,
                             "old_manifest": old_manifest, "old_packet_path": old_packet_path,
                             "old_packet": old_packet, "old_ready": old_ready.as_posix(),
                             "new_manifest": new_manifest, "new_ready": new_ready,
                             "snapshots": refs, "origin_changes": changes, "glossary": glossary})

    tool = load_translation_tool(root)
    records = []
    audit.mkdir(parents=True, exist_ok=True)
    temp_parent = audit.parent / "test-tmp"
    temp_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="native-inputs-stage-", dir=temp_parent) as temp:
        stage = Path(temp)
        for item in preparations:
            packet = copy.deepcopy(item["old_packet"])
            ready = Path(item["new_ready"])
            for ref in [packet["source"], packet["book_manifest"]]:
                write_new(stage / ref["path"], cache[ref["path"]])
            for name in ["source-segments.json", packet.get("source_reader_file", "source.ru.txt")]:
                write_new(stage / ready / name, cache[(Path(item["old_ready"]) / name).as_posix()])
            for ref in item["snapshots"]:
                write_new(stage / ref["path"], cache[ref["origin_path"]])
            task_ref = next(ref for ref in item["snapshots"] if ref["origin_path"] == TASK)
            index = {"schema_version": 1, "book_id": item["book_id"], "captured_at": timestamp,
                     "status": "frozen_context_for_full_native_language_revision",
                     "previous_input_manifest": {"path": item["old_manifest_path"],
                                                  "sha256": protected[item["old_manifest_path"]]},
                     "previous_packet": {"path": item["old_packet_path"],
                                         "sha256": protected[item["old_packet_path"]]},
                     "author_instruction": task["author_instruction"], "author_instruction_source": task_ref,
                     "snapshots": item["snapshots"], "origin_changes": item["origin_changes"],
                     "policy": "Active input paths point only to byte-preserved copies in this context directory. origin_path records provenance and is not a fallback live input. Prior frozen hashes are history, not replacements for current snapshot hashes. Internal document text and links are preserved verbatim; the frozen input set is enumerated here, not inferred by following live links.",
                     "reading_scope": "Editorial context package, not a blind target-only reader packet and not evidence that any prose was read."}
            index_path = (ready / "context/SNAPSHOT.json").as_posix()
            index_bytes = encoded(index)
            write_new(stage / index_path, index_bytes)
            index_ref = {"path": index_path, "sha256": digest(index_bytes), "role": "generated_context_index"}
            inputs = item["snapshots"] + [index_ref]
            packet.update(status="prepared_for_full_native_language_revision", inputs=inputs,
                          created_at=timestamp, context_snapshot=index_ref,
                          supersedes={"path": item["old_packet_path"], "sha256": protected[item["old_packet_path"]]},
                          author_instruction_source=task_ref,
                          context_policy="Only frozen context paths are active inputs; original source and inventory references are preserved.")
            if packet.get("author_decision"):
                decision_ref = next(ref for ref in item["snapshots"] if ref["origin_path"] == packet["author_decision"])
                packet["author_decision"] = decision_ref["path"]
                packet["author_decision_reference"] = decision_ref
            packet_path = (ready / "packet.json").as_posix()
            packet_bytes = encoded(packet)
            write_new(stage / packet_path, packet_bytes)
            glossary = {**item["glossary"], "translation_glossary_sha256": item["glossary"]["sha256"]}
            manifest = {"schema_version": 1, "book_id": item["book_id"],
                        "status": "frozen_for_full_native_language_revision", "created_at": timestamp,
                        "packet": {"path": packet_path, "sha256": digest(packet_bytes)},
                        "source_sha256": packet["source"]["sha256"],
                        "source_segments_sha256": packet["source_segments_sha256"], "inputs": inputs,
                        "context_snapshot": index_ref, "preserved_translation_glossary": glossary,
                        "author_instruction_source": task_ref, "author_canonical_approval": False,
                        "previous_input_manifest": index["previous_input_manifest"],
                        "supersedes_for_native_review": index["previous_input_manifest"],
                        "origin_changes": item["origin_changes"],
                        "activation": "Prepared context only; book.json, current pointers, target drafts and readers are unchanged by this operation.",
                        "change_policy": "Never mutate prior versions or these snapshots. New context changes require a new INPUTS/ready version.",
                        "scope": "All previous mutable inputs snapshotted plus current native-review rules, skills, project STYLE, CORE, TASK and target-only prompt; no new prose or literary QA."}
            manifest_bytes = encoded(manifest)
            write_new(stage / item["new_manifest"], manifest_bytes)
            records.append({"book_id": item["book_id"],
                            "manifest": {"path": item["new_manifest"], "sha256": digest(manifest_bytes)},
                            "packet": manifest["packet"], "ready_packet": item["new_ready"],
                            "context_snapshot": index_ref, "origin_changes": item["origin_changes"],
                            "preserved_translation_glossary": glossary})
        staged_validation = validate(stage, records, tool, require_isolated=True)
        for record in records:
            if (root / record["manifest"]["path"]).exists() or (root / record["ready_packet"]).exists():
                raise ValueError("Destination appeared while staging; refusing overwrite")
        for record in records:
            shutil.copytree(stage / record["ready_packet"], root / record["ready_packet"])
            write_new(root / record["manifest"]["path"], (stage / record["manifest"]["path"]).read_bytes())
    published_validation = validate(root, records, tool)
    preservation = []
    for path, before in protected.items():
        after = digest((root / path).read_bytes())
        preservation.append({"path": path, "before_sha256": before, "after_sha256": after, "unchanged": before == after})
    if any(not item["unchanged"] for item in preservation):
        raise ValueError("A protected path changed during creation; inspect concurrent work before declaring preservation")
    report = {"schema_version": 1, "created_at": timestamp, "status": "created_and_verified",
              "records": records, "staging_validation": staged_validation,
              "published_validation": published_validation, "protected_paths": preservation,
              "rule_update_record": {"path": RULE_UPDATE, "sha256": digest(cache[RULE_UPDATE])},
              "builder": {"path": str(Path(__file__).resolve().relative_to(root)),
                          "sha256": digest(Path(__file__).read_bytes())},
              "verification_tool": {"path": "tools/literary_translation.py", "sha256": protected["tools/literary_translation.py"]},
              "models_run": False, "exports_run": False, "literary_quality": "not_assessed"}
    write_new(audit / "CREATED-INPUTS.json", report)
    print(json.dumps({"status": report["status"], "books": [{"book_id": item["book_id"],
                      "active_inputs": item["active_inputs"], "context_snapshots": item["context_snapshots"],
                      "source_segments": item["source_segments"]} for item in published_validation]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    create(args.root, args.audit)
