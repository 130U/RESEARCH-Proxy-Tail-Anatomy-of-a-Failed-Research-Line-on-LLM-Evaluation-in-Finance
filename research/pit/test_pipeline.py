"""Finite synthetic mechanism checks; these do not prove real availability."""
from dataclasses import replace
from fractions import Fraction
import json
import unittest

from research.pit.pipeline import (
    FrozenConfig, build_at_cutoff,
    canonical_history, deduplicate, filter_documents, fit_tokenizer,
    naive_full_log_latest_duplicate_then_filter, naive_full_log_size_selects_historical,
    naive_full_log_vocabulary_then_filter, run_pipeline, sample_documents,
    select_tokenizer, split_documents, tombstone, upsert, world_adapter,
)


class PipelineTests(unittest.TestCase):
    def base(self):
        return [upsert("old-a", "event-a", -2, "alpha beta shared", core=True, label="negative"),
                upsert("old-b", "event-b", -1, "delta epsilon distinct", label="positive"),
                upsert("old-c", "event-c", 0, "gamma theta another")]

    def assert_artifacts_equal(self, left, right):
        self.assertEqual(set(left), set(right))
        for name in left:
            self.assertEqual(left[name], right[name], name)

    def test_future_upsert_tombstone_metadata_label_do_not_change_any_stage(self):
        base = self.base()
        old = build_at_cutoff(base, cutoff=0)
        future = [upsert("old-a", "future-revision", 5, "future replacement novelword", record_time=-2, source="not-allowed", core=False, label="changed", metadata={"selection": "future"}),
                  tombstone("old-b", "future-delete", 6, record_time=-1),
                  upsert("future-c", "future-add", 7, "alpha beta shared bridge")]
        self.assert_artifacts_equal(old, build_at_cutoff(base+future, cutoff=0))
        self.assert_artifacts_equal(old, build_at_cutoff(list(reversed(base+future)), cutoff=0))

    def test_future_body_is_opaque_even_if_malformed(self):
        base = self.base()
        opaque = {"event_id": "future", "document_id": "old-a", "knowledge_time": 5, "payload": object()}
        self.assert_artifacts_equal(build_at_cutoff(base, cutoff=0), build_at_cutoff(base+[opaque], cutoff=0))
        with self.assertRaises(ValueError):
            build_at_cutoff(base+[opaque], cutoff=5)

    def test_future_duplicate_event_id_does_not_trigger_global_uniqueness(self):
        base = self.base()
        duplicate = upsert("different-doc", "event-a", 4, "later text")
        self.assert_artifacts_equal(build_at_cutoff(base, cutoff=0), build_at_cutoff(base+[duplicate], cutoff=0))
        with self.assertRaises(ValueError):
            build_at_cutoff(base+[duplicate], cutoff=4)

    def test_projection_uses_knowledge_time_not_record_time(self):
        base = [upsert("a", "initial", -2, "old state")]
        revised = upsert("a", "new", 5, "new state", record_time=-100)
        self.assertEqual(canonical_history(base+[revised], cutoff=0).documents[0].text, "old state")
        self.assertEqual(canonical_history(base+[revised], cutoff=5).documents[0].text, "new state")

    def test_latest_visible_version_and_tombstone_same_time_tie(self):
        events = [upsert("a", "first", -2, "first"), upsert("a", "tie-a", 0, "second"), upsert("a", "tie-z", 0, "third"), tombstone("a", "delete", 2)]
        self.assertEqual(canonical_history(events, cutoff=-1).documents[0].text, "first")
        self.assertEqual(canonical_history(events, cutoff=0).documents[0].text, "third")
        self.assertEqual(canonical_history(list(reversed(events)), cutoff=0), canonical_history(events, cutoff=0))
        self.assertEqual(canonical_history(events, cutoff=2).documents, ())

    def test_visible_body_hash_and_declared_clock_constraints_reject(self):
        wrong_hash = upsert("a", "e", 0, "text")
        wrong_hash["payload"]["content_sha256"] = "not-the-hash"
        with self.assertRaises(ValueError):
            canonical_history([wrong_hash], cutoff=0)
        with self.assertRaises(ValueError):
            canonical_history([upsert("a", "e", 0, "text", record_time=1)], cutoff=0)

    def test_invalid_future_header_is_outside_input_domain(self):
        for future in [None, {"event_id": "f", "document_id": "a", "knowledge_time": True}, {"event_id": "f", "document_id": "a", "knowledge_time": "future"}, {"event_id": "", "document_id": "a", "knowledge_time": 5}]:
            with self.assertRaises(ValueError):
                build_at_cutoff(self.base()+[future], cutoff=0)

    def test_future_duplicate_bridge_is_not_clustered_first(self):
        config = FrozenConfig(stopwords=())
        base = [upsert("a", "ea", 0, "a b c d"), upsert("c", "ec", 0, "a b c e")]
        bridge = upsert("bridge", "eb", 1, "a b c d e")
        before = build_at_cutoff(base, cutoff=0, config=config)
        after = build_at_cutoff(base+[bridge], cutoff=0, config=config)
        self.assert_artifacts_equal(before, after)
        self.assertEqual(len(json.loads(before["deduplicate.json"])["documents"]), 2)
        later = build_at_cutoff(base+[bridge], cutoff=1, config=config)
        self.assertEqual(len(json.loads(later["deduplicate.json"])["documents"]), 1)

    def test_all_stages_bind_their_cutoff(self):
        snapshot = canonical_history(self.base(), cutoff=0)
        config = FrozenConfig()
        state = filter_documents(snapshot, config, cutoff=0)
        train, dev = split_documents(state, config, cutoff=0, seed=130)
        calls = [lambda: run_pipeline(snapshot, cutoff=1, config=config, seed=130),
                 lambda: filter_documents(snapshot, config, cutoff=1),
                 lambda: deduplicate(state, config, cutoff=1),
                 lambda: sample_documents(state, config, cutoff=1, seed=130),
                 lambda: split_documents(state, config, cutoff=1, seed=130),
                 lambda: fit_tokenizer(train, (4, 1), cutoff=1),
                 lambda: select_tokenizer(train, dev, config, cutoff=1)]
        for call in calls:
            with self.assertRaises(ValueError):
                call()

    def test_forged_snapshot_documents_or_history_are_rejected(self):
        snapshot = canonical_history(self.base(), cutoff=0)
        forged_doc = replace(snapshot.documents[0], text="different")
        forged = replace(snapshot, documents=(forged_doc,)+snapshot.documents[1:])
        with self.assertRaises(ValueError):
            run_pipeline(forged, cutoff=0, config=FrozenConfig(), seed=130)
        future_doc = upsert("future", "future", 10, "future")
        forged = replace(snapshot, visible_history_bytes=json.dumps(self.base()+[future_doc]).encode())
        with self.assertRaises(ValueError):
            run_pipeline(forged, cutoff=0, config=FrozenConfig(), seed=130)

    def test_snapshot_rejects_python_bool_integer_equality_bypass(self):
        snapshot = canonical_history([upsert("a", "e", 0, "text", core=True, label=0)], cutoff=1)
        for document in [replace(snapshot.documents[0], label=False), replace(snapshot.documents[0], core=1), replace(snapshot.documents[0], knowledge_time=False)]:
            forged = replace(snapshot, documents=(document,))
            with self.assertRaises(ValueError):
                run_pipeline(forged, cutoff=1, config=FrozenConfig(), seed=130)
        with self.assertRaises(ValueError):
            run_pipeline(replace(snapshot, cutoff=True), cutoff=1, config=FrozenConfig(), seed=130)
        state = filter_documents(snapshot, FrozenConfig(), cutoff=1)
        with self.assertRaises(ValueError):
            sample_documents(replace(state, cutoff=True), FrozenConfig(), cutoff=1, seed=130)

    def test_empty_history_and_empty_dev_use_frozen_first_candidate(self):
        config = FrozenConfig(tokenizer_candidates=((8, 1), (4, 1)), development_fraction=(0, 1))
        for events in [[], self.base()]:
            artifacts = build_at_cutoff(events, cutoff=0, config=config)
            selection = json.loads(artifacts["tokenizer_candidates.json"])
            self.assertEqual(selection["selected_index"], 0)
            self.assertEqual(selection["reason"], "no_development_tokens_use_frozen_first_candidate")
        empty = json.loads(build_at_cutoff([], cutoff=0)["selected_tokenizer.json"])
        self.assertEqual(empty["vocabulary"], [])

    def test_tokenizer_fits_train_only_and_selection_uses_exact_dev_objective(self):
        config = FrozenConfig(stopwords=(), tokenizer_candidates=((1, 1), (2, 1)))
        snapshot = canonical_history([upsert("train", "t", 0, "alpha alpha alpha beta beta"), upsert("dev", "d", 0, "beta never_seen")], cutoff=0)
        state = filter_documents(snapshot, config, cutoff=0)
        train = replace(state, documents=tuple(d for d in state.documents if d.document_id == "train"))
        dev = replace(state, documents=tuple(d for d in state.documents if d.document_id == "dev"))
        chosen, result = select_tokenizer(train, dev, config, cutoff=0)
        self.assertEqual(chosen["capacity"], 2)
        for candidate in result["candidates"]:
            self.assertNotIn("never_seen", {entry["token"] for entry in candidate["tokenizer"]["vocabulary"]})
            self.assertEqual(Fraction(*candidate["objective"]), Fraction(*candidate["oov"])+Fraction(*candidate["capacity_cost"]))

    def test_metadata_only_changes_are_versioned_and_future_changes_are_hidden(self):
        base = [upsert("a", "old", 0, "same text", source="fixture", core=True, label=0, metadata={"role": "old"})]
        future = upsert("a", "new", 1, "same text", record_time=0, source="excluded", core=False, label=2, metadata={"role": "new"})
        config = FrozenConfig(require_core=True)
        self.assert_artifacts_equal(build_at_cutoff(base, cutoff=0, config=config), build_at_cutoff(base+[future], cutoff=0, config=config))
        self.assertEqual(json.loads(build_at_cutoff(base+[future], cutoff=1, config=config)["filter.json"])["documents"], [])

    def test_finite_future_extensions_across_multiple_cutoffs(self):
        events = [upsert(f"d{i}", f"e{i}", i, f"document item{i} distinct{i}") for i in range(-2, 4)]
        cases = 0
        for cutoff in range(-3, 5):
            original = build_at_cutoff(events, cutoff=cutoff)
            for offset in (1, 2, 9):
                for addition in [upsert("d0", f"u{cutoff}:{offset}", cutoff+offset, "new future text", record_time=cutoff-10), tombstone("d0", f"x{cutoff}:{offset}", cutoff+offset), {"event_id": f"bad{cutoff}:{offset}", "document_id": "d0", "knowledge_time": cutoff+offset, "payload": object()}]:
                    self.assert_artifacts_equal(original, build_at_cutoff(list(reversed(events+[addition])), cutoff=cutoff))
                    cases += 1
        self.assertEqual(cases, 72)

    def test_world_adapter_never_reads_latent_fields(self):
        class GuardedRow(dict):
            def __getitem__(self, key):
                if key not in {"id", "recorded_time", "text"}:
                    raise AssertionError("latent field accessed")
                return super().__getitem__(key)
        row = GuardedRow(id="synthetic", recorded_time=0, text="visible report", available_time=999, contaminated=True, stance=2)
        adapted = world_adapter([row])
        self.assertEqual(adapted[0]["knowledge_time"], 0)
        self.assertIsNone(adapted[0]["payload"]["label"])
        self.assertFalse(adapted[0]["payload"]["core"])

    def test_naive_full_log_operations_have_actual_counterexamples(self):
        base = [upsert("a", "a", 0, "old alpha"), upsert("b", "b", 0, "old beta")]
        future_token = upsert("new", "new", 1, "future unseen")
        self.assertNotEqual(naive_full_log_vocabulary_then_filter(base, 0), naive_full_log_vocabulary_then_filter(base+[future_token], 0))
        future_duplicate = upsert("copy", "copy", 1, "old alpha")
        self.assertNotEqual(naive_full_log_latest_duplicate_then_filter(base, 0), naive_full_log_latest_duplicate_then_filter(base+[future_duplicate], 0))
        self.assertNotEqual(naive_full_log_size_selects_historical(base, 0), naive_full_log_size_selects_historical(base+[future_token], 0))
        self.assert_artifacts_equal(build_at_cutoff(base, cutoff=0), build_at_cutoff(base+[future_token,future_duplicate], cutoff=0))

    def test_configuration_and_seed_are_explicit_not_claimed_invariant(self):
        base = self.base()
        a = build_at_cutoff(base, cutoff=0, seed=130)
        b = build_at_cutoff(base, cutoff=0, seed=131)
        self.assertNotEqual(a["configuration.json"], b["configuration.json"])
        with self.assertRaises(ValueError):
            build_at_cutoff(base, cutoff=0, seed=True)


if __name__ == "__main__":
    unittest.main()
