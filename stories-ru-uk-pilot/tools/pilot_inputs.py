"""Resolve an explicit frozen-input/ready pair without changing legacy defaults."""
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rooted(root, value):
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise ValueError("Input paths must be nonempty repository-relative or absolute paths")
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Input paths must stay within the repository")
    return path


def select_inputs(root, edition, book_id, explicit=None):
    """Return manifest, ready directory and an optional verified pair identity.

    ``None`` deliberately keeps INPUTS-V1/ready-v1. Historical selections already
    contain flat input_manifest metadata that the old assembler did not consume;
    only the new input_binding object opts that caller into explicit selection.
    This function checks the pair, not every frozen dependency or prose quality.
    """
    root, edition = Path(root).resolve(), Path(edition).resolve()
    if explicit is None:
        return edition / "INPUTS-V1.json", edition / "preparation/pilot/ready-v1", None
    if not isinstance(explicit, dict):
        raise ValueError("input_binding must be an object with input_manifest and ready_packet")
    if not explicit.get("input_manifest") or not explicit.get("ready_packet"):
        raise ValueError("Specify input_manifest and ready_packet together")
    manifest_path = rooted(root, explicit["input_manifest"])
    ready = rooted(root, explicit["ready_packet"])
    manifest_sha = sha(manifest_path)
    if explicit.get("input_manifest_sha256") is not None and explicit["input_manifest_sha256"] != manifest_sha:
        raise ValueError("Selected input manifest hash changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["book_id"] != book_id:
        raise ValueError("Selected input manifest belongs to another book")
    packet_file = ready / "packet.json"
    if rooted(root, manifest["packet"]["path"]) != packet_file:
        raise ValueError("Input manifest and ready packet are not the same frozen pair")
    packet_sha = sha(packet_file)
    if manifest["packet"]["sha256"] != packet_sha:
        raise ValueError("Ready packet hash disagrees with input manifest")
    if explicit.get("packet_sha256") is not None and explicit["packet_sha256"] != packet_sha:
        raise ValueError("Selected ready packet hash changed")
    packet = json.loads(packet_file.read_text(encoding="utf-8"))
    if packet["book_id"] != book_id:
        raise ValueError("Selected ready packet belongs to another book")
    if packet["source_language"] != "ru" or packet["target_language"] != "uk":
        raise ValueError("Pilot input pair must describe RU to UK")
    if manifest["source_sha256"] != packet["source"]["sha256"]:
        raise ValueError("Input manifest and ready packet disagree on the source hash")
    segments_sha = sha(ready / "source-segments.json")
    if manifest["source_segments_sha256"] != packet["source_segments_sha256"] or packet["source_segments_sha256"] != segments_sha:
        raise ValueError("Input manifest and ready packet disagree on source segments")
    identity = {"input_manifest": str(manifest_path.relative_to(root)),
                "input_manifest_sha256": manifest_sha,
                "ready_packet": str(ready.relative_to(root)), "packet_sha256": packet_sha,
                "source_sha256": manifest["source_sha256"], "source_segments_sha256": segments_sha}
    return manifest_path, ready, identity


def require_checked_binding(checks, identity):
    if identity is not None and checks.get("input_binding") != identity:
        raise ValueError("Final checks do not certify the explicitly selected input pair; create new checks for it")
