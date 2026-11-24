"""Synthetic fixtures only; no real headlines or labels are loaded by tests."""
import itertools
import random
import unittest

from research.real_baseline.prepare import (
    QuarantineError, exact_near_edges, group_titles, meets_jaccard,
    normalized, parse_decisions, prepare_records, split_for_family,
)


def row(number, title, decisions):
    return {"S No.": str(number), "Title": title, "Decisions": decisions, "Words": "0"}


class PreparationTests(unittest.TestCase):
    def test_duplicate_raw_and_normalized_keys_quarantine(self):
        for raw in ["{'A':'positive','A':'negative'}", "{'A':'positive',' a ':'positive'}", "{'\uff21':'neutral','a':'neutral'}"]:
            with self.assertRaises(QuarantineError):
                parse_decisions(raw)

    def test_strict_literals_and_labels(self):
        for raw in ["__import__('os').system('echo forbidden')", "{'A': 'POSITIVE'}", "{'A': 1}", "{}", "{'': 'neutral'}", "{'A':'positive'", "{**{'A':'positive'}}"]:
            with self.assertRaises(QuarantineError):
                parse_decisions(raw)
        self.assertEqual(parse_decisions("{'A': 'positive', 'B':'negative'}"), [("A", "positive"), ("B", "negative")])

    def test_prefix_edges_equal_bruteforce_exhaustive(self):
        universe = ["a", "b", "c", "d", "e", "f", "g"]
        sets = [frozenset(choice) for size in range(8) for choice in itertools.combinations(universe, size)]
        expected = {(i, j) for j in range(len(sets)) for i in range(j) if meets_jaccard(sets[i], sets[j])}
        observed, _ = exact_near_edges(sets)
        self.assertEqual(set(observed), expected)

    def test_prefix_edges_equal_bruteforce_varied_lengths(self):
        rng = random.Random(130)
        sets = [frozenset(rng.sample([str(i) for i in range(30)], rng.randrange(31))) for _ in range(180)]
        sets += [frozenset("abcd"), frozenset("abcde"), frozenset("abcde"), frozenset()]
        expected = {(i, j) for j in range(len(sets)) for i in range(j) if meets_jaccard(sets[i], sets[j])}
        self.assertEqual(set(exact_near_edges(sets)[0]), expected)

    def test_threshold_boundary_and_transitive_bridge(self):
        a = "a b c d"
        b = "a b c d e"
        c = "a b c e"
        family, edges, _ = group_titles([a, b, c])
        self.assertFalse(meets_jaccard(frozenset(a.split()), frozenset(c.split())))
        self.assertEqual(len(edges), 2)
        self.assertEqual(len(set(family.values())), 1)

    def test_empty_token_titles_do_not_all_merge(self):
        family, edges, stats = group_titles(["!!!", "???", " !!! "])
        self.assertEqual(len(set(family.values())), 2)
        self.assertEqual(edges, [])
        self.assertEqual(stats["tokenless_normalized_titles"], 2)

    def test_multi_entity_labels_legal_and_pair_conflicts_isolated(self):
        records = [row(1, "A expands B contracts", "{'A':'positive','B':'negative'}"), row(2, " a expands b contracts ", "{'A':'negative','B':'negative'}")]
        samples, quarantine, stats = prepare_records(records)
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]["target"], "B")
        self.assertEqual(samples[0]["source_ids"], ["1", "2"])
        self.assertEqual(stats["conflicting_normalized_entity_title_pairs"], 1)
        self.assertEqual(quarantine[0]["stage"], "entity_title")

    def test_same_headline_entities_share_family_not_label(self):
        samples, _, stats = prepare_records([row(1, "A expands B contracts", "{'A':'positive','B':'negative'}")])
        self.assertEqual(len(samples), 2)
        self.assertEqual(len({s["family_id"] for s in samples}), 1)
        self.assertEqual(len({s["split"] for s in samples}), 1)
        self.assertEqual(stats["row_quarantined"], 0)

    def test_malformed_bridge_still_groups_before_labels(self):
        records = [row(1, "a b c d", "{'a':'positive'}"), row(2, "a b c d e", "malformed"), row(3, "a b c e", "{'a':'negative'}")]
        samples, _, stats = prepare_records(records)
        self.assertEqual(len(samples), 2)
        self.assertEqual(len({s["family_id"] for s in samples}), 1)
        self.assertEqual(stats["row_quarantined"], 1)
        self.assertEqual(stats["checks"]["near_edge_cross_split_count"], 0)

    def test_nonliteral_entity_retained(self):
        samples, _, stats = prepare_records([row(1, "market movement", "{'absent company':'neutral'}")])
        self.assertEqual(len(samples), 1)
        self.assertEqual(stats["entity_not_literal_substring"], 1)
        self.assertEqual(stats["entity_not_normalized_substring"], 1)
        self.assertTrue(samples[0]["input_text"].startswith("[ENTITY] absent company\n[TITLE]"))

    def test_duplicate_source_ids_quarantine_all(self):
        samples, _, stats = prepare_records([row(1, "a", "{'a':'positive'}"), row(1, "b", "{'b':'negative'}")])
        self.assertEqual(samples, [])
        self.assertEqual(stats["quarantine_reasons"], {"duplicate_source_id": 2})

    def test_groups_and_splits_do_not_depend_on_order_or_labels(self):
        titles = ["a b c d", "a b c d e", "x y z", "\uff21   gains"]
        mapping, _, _ = group_titles(titles)
        reversed_mapping, _, _ = group_titles(list(reversed(titles)))
        self.assertEqual(mapping, reversed_mapping)
        records = [row(i, title, "{'target':'positive'}") for i, title in enumerate(titles)]
        changed = [dict(record, Decisions="{'target':'negative'}") for record in records]
        left, _, _ = prepare_records(records)
        right, _, _ = prepare_records(changed)
        self.assertEqual([(r["id"], r["family_id"], r["split"]) for r in left], [(r["id"], r["family_id"], r["split"]) for r in right])
        self.assertEqual(normalized("\uff21   gains"), "a gains")
        self.assertTrue(all(split_for_family(f) in {"train", "development", "test"} for f in mapping.values()))


if __name__ == "__main__":
    unittest.main()
