import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
from pilot_inputs import select_inputs, require_checked_binding, sha
import check_final_draft
import assemble_delivery


class ReachedSource(Exception):
    pass


class InputBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "stories-ru-uk-pilot"
        self.book_id = "fixture-story"
        self.edition = self.project / "books" / self.book_id / "editions/uk"
        self.edition.mkdir(parents=True)
        self.pairs = {version: self.make_pair(version) for version in (1, 2, 3)}

    def write_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def make_pair(self, version):
        ready = self.edition / f"preparation/pilot/ready-v{version}"
        ready.mkdir(parents=True)
        segments = ready / "source-segments.json"
        # Identical projections deliberately cannot distinguish packet versions.
        self.write_json(segments, {"segments": []})
        packet = {"book_id": self.book_id, "source_language": "ru", "target_language": "uk",
                  "source": {"sha256": "a" * 64}, "source_segments_sha256": sha(segments), "inputs": []}
        self.write_json(ready / "packet.json", packet)
        manifest = self.edition / f"INPUTS-V{version}.json"
        self.write_json(manifest, {"book_id": self.book_id,
                        "packet": {"path": str((ready / "packet.json").relative_to(self.root)),
                                   "sha256": sha(ready / "packet.json")},
                        "source_sha256": packet["source"]["sha256"],
                        "source_segments_sha256": packet["source_segments_sha256"], "inputs": []})
        return {"input_manifest": str(manifest.relative_to(self.root)),
                "input_manifest_sha256": sha(manifest), "ready_packet": str(ready.relative_to(self.root))}

    def test_omitted_pair_keeps_legacy_v1_without_guessing_from_book_metadata(self):
        manifest, ready, identity = select_inputs(self.root, self.edition, self.book_id)
        self.assertEqual(manifest, self.edition / "INPUTS-V1.json")
        self.assertEqual(ready, self.edition / "preparation/pilot/ready-v1")
        self.assertIsNone(identity)

    def test_explicit_v2_and_v3_select_and_record_the_requested_pair(self):
        for version in (2, 3):
            with self.subTest(version=version):
                spec = self.pairs[version]
                manifest, ready, identity = select_inputs(self.root, self.edition, self.book_id, spec)
                self.assertEqual(manifest, self.root / spec["input_manifest"])
                self.assertEqual(ready, self.root / spec["ready_packet"])
                self.assertEqual(identity["input_manifest_sha256"], sha(manifest))
                self.assertEqual(identity["packet_sha256"], sha(ready / "packet.json"))

    def test_crossed_pair_is_rejected_even_with_identical_packet_and_segment_bytes(self):
        explicit = {**self.pairs[2], "ready_packet": self.pairs[1]["ready_packet"]}
        self.assertEqual(sha(self.root / self.pairs[1]["ready_packet"] / "packet.json"),
                         sha(self.root / self.pairs[2]["ready_packet"] / "packet.json"))
        with self.assertRaisesRegex(ValueError, "same frozen pair"):
            select_inputs(self.root, self.edition, self.book_id, explicit)

    def test_partial_pair_wrong_book_and_stale_manifest_hash_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "together"):
            select_inputs(self.root, self.edition, self.book_id, {"input_manifest": self.pairs[2]["input_manifest"]})
        with self.assertRaisesRegex(ValueError, "another book"):
            select_inputs(self.root, self.edition, "different-book", self.pairs[2])
        with self.assertRaisesRegex(ValueError, "manifest hash changed"):
            select_inputs(self.root, self.edition, self.book_id,
                          {**self.pairs[2], "input_manifest_sha256": "0" * 64})

    def test_changed_packet_and_changed_projection_are_rejected(self):
        packet = self.root / self.pairs[2]["ready_packet"] / "packet.json"
        packet.write_text(packet.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "packet hash"):
            select_inputs(self.root, self.edition, self.book_id, self.pairs[2])
        segments = self.root / self.pairs[3]["ready_packet"] / "source-segments.json"
        segments.write_text('{"segments": ["changed"]}\n')
        with self.assertRaisesRegex(ValueError, "source segments"):
            select_inputs(self.root, self.edition, self.book_id, self.pairs[3])

    def test_final_checker_dispatches_selected_packet_and_preserves_legacy_call(self):
        calls = []
        technical = SimpleNamespace(check_translation=lambda root, packet, *rest:
                                    calls.append(packet) or {"errors": ["stop before any report"]})
        language = SimpleNamespace(check=lambda *args: {"findings": []})
        def loader(name, path):
            return technical if name == "final_literary_translation" else language
        with mock.patch.object(check_final_draft, "ROOT", self.root), mock.patch.object(check_final_draft, "module", loader):
            with self.assertRaises(AssertionError):
                check_final_draft.check(self.book_id, "draft-fixture")
            with self.assertRaises(AssertionError):
                check_final_draft.check(self.book_id, "draft-fixture",
                                        self.pairs[2]["input_manifest"], self.pairs[2]["ready_packet"],
                                        self.pairs[2]["input_manifest_sha256"])
        self.assertEqual(calls, [self.edition / "preparation/pilot/ready-v1",
                                 self.edition / "preparation/pilot/ready-v2"])
        self.assertFalse((self.edition / "draft-fixture/final-checks.json").exists())

    def selection_reaches(self, chosen):
        seen = []
        selection_path = self.root / "selection.json"
        out = self.root / "delivery-not-created"
        def reader(path):
            if path == selection_path:
                return {"books": [chosen]}
            if path.name == "translation.json":
                return {}
            if path.name == "source-segments.json":
                seen.append(path)
                raise ReachedSource()
            raise AssertionError(f"Unexpected read before source selection: {path}")
        with mock.patch.object(assemble_delivery, "ROOT", self.root), \
             mock.patch.object(assemble_delivery, "PROJECT", self.project), \
             mock.patch.object(assemble_delivery, "read", reader):
            with self.assertRaises(ReachedSource):
                assemble_delivery.main(selection_path, out)
        self.assertFalse(out.exists())
        return seen

    def test_assembler_uses_explicit_pair_and_keeps_old_flat_metadata_behavior(self):
        chosen = {"book_id": self.book_id, "draft": "draft-fixture"}
        old = {**chosen, "input_manifest": "historical-flat-metadata.json", "input_manifest_sha256": "0" * 64}
        self.assertEqual(self.selection_reaches(old), [self.edition / "preparation/pilot/ready-v1/source-segments.json"])
        self.assertEqual(self.selection_reaches({**chosen, "input_binding": self.pairs[3]}),
                         [self.edition / "preparation/pilot/ready-v3/source-segments.json"])

    def test_assembler_rejects_crossed_pair_before_creating_delivery(self):
        selection = self.root / "bad-selection.json"
        self.write_json(selection, {"books": [{"book_id": self.book_id, "draft": "draft-fixture",
                        "input_binding": {**self.pairs[2], "ready_packet": self.pairs[1]["ready_packet"]}}]})
        out = self.root / "delivery-not-created"
        with mock.patch.object(assemble_delivery, "ROOT", self.root), mock.patch.object(assemble_delivery, "PROJECT", self.project):
            with self.assertRaisesRegex(ValueError, "same frozen pair"):
                assemble_delivery.main(selection, out)
        self.assertFalse(out.exists())

    def test_explicit_assembly_requires_checks_bound_to_that_pair(self):
        _, _, identity = select_inputs(self.root, self.edition, self.book_id, self.pairs[2])
        require_checked_binding({"result": "historical"}, None)
        with self.assertRaisesRegex(ValueError, "create new checks"):
            require_checked_binding({"result": "historical"}, identity)
        with self.assertRaises(ValueError):
            require_checked_binding({"input_binding": {**identity, "input_manifest_sha256": "0" * 64}}, identity)
        require_checked_binding({"input_binding": identity}, identity)

    def test_existing_checks_are_never_replaced(self):
        checks = self.edition / "draft-fixture/final-checks.json"
        checks.parent.mkdir()
        original = b"immutable historical fixture\n"
        checks.write_bytes(original)
        with mock.patch.object(check_final_draft, "ROOT", self.root):
            with self.assertRaisesRegex(AssertionError, "immutable"):
                check_final_draft.check(self.book_id, "draft-fixture")
        self.assertEqual(checks.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
