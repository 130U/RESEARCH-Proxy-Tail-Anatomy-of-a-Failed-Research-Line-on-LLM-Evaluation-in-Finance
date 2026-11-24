"""Prepare a disjoint 32-family blind input set, offline and without scoring.

Run once with the existing Python environment. Refuses to overwrite the private
stage directory. Uses only family/ID/text/source-reference fields, not labels or
old predictions. Reproducibility seeds and the private mapping accompany inputs.
"""
from collections import defaultdict
from itertools import combinations
import argparse
import json
from pathlib import Path
import random


FAMILY_SEED = 20261119
MEMBER_SEED = 20261120
N = 32


def shuffled(values, seed):
    result = list(values)
    random.Random(seed).shuffle(result)
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def make_pair_batches(pairs, seeds):
    """Reproduce the executed split: shuffled canonical IDs, original row order."""
    batches = {}
    for panel in (1, 2):
        pair_ids = sorted(row["pair_id"] for row in pairs[f"pair_panel{panel}_a.json"]["pairs"])
        if len(pair_ids) != 496 or len(set(pair_ids)) != 496:
            raise ValueError("Expected 496 unique original pair IDs")
        random.Random(seeds[panel]).shuffle(pair_ids)
        for batch in range(4):
            selected = set(pair_ids[124 * batch:124 * (batch + 1)])
            for orientation in ("a", "b"):
                original = pairs[f"pair_panel{panel}_{orientation}.json"]
                rows = [row for row in original["pairs"] if row["pair_id"] in selected]
                if len(rows) != 124 or {row["pair_id"] for row in rows} != selected:
                    raise ValueError("Original orientations do not share the full pair set")
                batches[f"pair_panel{panel}_{orientation}_batch{batch + 1:02d}.json"] = {
                    "documents": original["documents"], "pairs": rows}
    return batches


def verify_existing_batches(target):
    """Read-only verification; never rewrites historical inputs or metadata."""
    metadata = read_json(target / "metadata.json")
    seeds = {int(key): value for key, value in metadata["pair_batching"]["panel_assignment_seeds"].items()}
    originals = {f"pair_panel{p}_{o}.json": read_json(target / f"pair_panel{p}_{o}.json")
                 for p in (1, 2) for o in ("a", "b")}
    generated = make_pair_batches(originals, seeds)
    for name, value in generated.items():
        if read_json(target / name) != value:
            raise ValueError("Existing pair batch differs from recorded-seed reconstruction: " + name)
    print(json.dumps({"status": "read_only_batch_reproduction_verified", "batch_files": len(generated),
                      "pairs_per_file": 124, "panel_assignment_seeds": seeds, "files_modified": 0}))


def validate_inputs(ranks, pairs, documents, canonical):
    expected = {row["id"]: row["text"] for row in documents}
    if len(expected) != N or set(expected) != {f"S{i:04d}" for i in range(1, N + 1)}:
        raise ValueError("Unexpected blind ID set")

    def check_documents(rows):
        if (len(rows) != N or any(set(row) != {"id", "text"} for row in rows)
                or {r["id"]: r["text"] for r in rows} != expected
                or len({r["id"] for r in rows}) != N):
            raise ValueError("Document schema, IDs or text changed between inputs")

    for rows in ranks.values():
        check_documents(rows)
    for value in pairs.values():
        if set(value) != {"documents", "pairs"}:
            raise ValueError("Unexpected pair input fields")
        check_documents(value["documents"])
        rows = value["pairs"]
        if len(rows) != 496:
            raise ValueError("Pair input does not contain 496 comparisons")
        seen, unordered = set(), set()
        for row in rows:
            if set(row) != {"pair_id", "left", "right"}:
                raise ValueError("Unexpected pair fields")
            identifier, left, right = row["pair_id"], row["left"], row["right"]
            if identifier in seen or identifier not in canonical:
                raise ValueError("Repeated or unknown pair ID")
            if left not in expected or right not in expected or left == right:
                raise ValueError("Invalid pair endpoint")
            endpoints = tuple(sorted((left, right)))
            if endpoints != canonical[identifier] or endpoints in unordered:
                raise ValueError("Pair does not match its canonical unordered pair")
            seen.add(identifier)
            unordered.add(endpoints)
        if seen != set(canonical) or unordered != set(combinations(sorted(expected), 2)):
            raise ValueError("Incomplete unordered-pair coverage")
    for panel in (1, 2):
        a = {r["pair_id"]: (r["left"], r["right"]) for r in pairs[f"pair_panel{panel}_a.json"]["pairs"]}
        b = {r["pair_id"]: (r["left"], r["right"]) for r in pairs[f"pair_panel{panel}_b.json"]["pairs"]}
        if any(b[key] != (value[1], value[0]) for key, value in a.items()):
            raise ValueError("Within-panel a/b orientations are not exact inverses")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-batches", action="store_true", help="Read-only reproduction check of existing stage-1 batches")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    target = (root / "research/private/agent_tail_methods/stage1_n32").resolve()
    research = (root / "research").resolve(strict=True)
    methods = (research / "private/agent_tail_methods").resolve()
    if (Path(__file__).resolve().parent != research / "tail_screening"
            or not research.is_relative_to(root)
            or not methods.is_relative_to(research / "private")
            or target.parent != methods):
        raise RuntimeError("Output must resolve inside the intended worktree")
    if args.verify_batches:
        verify_existing_batches(target)
        return
    if target.exists():
        raise FileExistsError("Refuse to overwrite the existing stage directory")
    source = (root / "research/private/real_baseline/test.jsonl").resolve(strict=True)
    old_metadata = (root / "research/private/agent_tail_pilot/metadata.json").resolve(strict=True)
    if not source.is_relative_to(root) or not old_metadata.is_relative_to(root):
        raise RuntimeError("Input path escapes worktree")
    old = read_json(old_metadata)
    excluded = {row["family_id"] for row in old["mapping"]}
    if len(old["mapping"]) != 128 or len(excluded) != 128:
        raise ValueError("Previous pilot must identify 128 distinct excluded families")
    families, seen = defaultdict(list), set()
    with source.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            identifier, family, text = row["id"], row["family_id"], row["input_text"]
            if (not all(type(value) is str and value for value in (identifier, family, text))
                    or identifier in seen or row["split"] != "test"):
                raise ValueError("Invalid source ID/family/text or non-test source row")
            if text != "[ENTITY] " + row["target"] + "\n[TITLE] " + row["headline"]:
                raise ValueError("Input field contract changed")
            seen.add(identifier)
            families[family].append({"original_id": identifier, "family_id": family,
                                    "text": text, "source_line": line_number,
                                    "original_source_ids": row["source_ids"]})
    if not excluded <= set(families):
        raise ValueError("Excluded pilot families missing from source test population")
    eligible = sorted(set(families) - excluded)
    selected = random.Random(FAMILY_SEED).sample(eligible, N)
    member_rng = random.Random(MEMBER_SEED)
    documents, mapping = [], []
    for number, family in enumerate(selected, 1):
        members = sorted(families[family], key=lambda row: row["original_id"])
        item = member_rng.choice(members)
        identifier = f"S{number:04d}"
        documents.append({"id": identifier, "text": item["text"]})
        mapping.append({"blind_id": identifier, **{key: value for key, value in item.items() if key != "text"},
                        "family_size_in_test": len(members)})
    overlap = set(selected) & excluded
    if overlap or len(set(selected)) != N:
        raise ValueError("New families overlap prior pilot or each other")
    rank_seeds = {f"rank_order{i}.jsonl": 20261120 + i for i in range(1, 9)}
    ranks = {name: shuffled(documents, seed) for name, seed in rank_seeds.items()}
    canonical = {f"E{i:04d}": pair for i, pair in enumerate(combinations(sorted(r["id"] for r in documents), 2), 1)}
    orientation_seeds = {1: 20261129, 2: 20261130}
    pair_seeds, pairs = {}, {}
    for panel in (1, 2):
        rng = random.Random(orientation_seeds[panel])
        a = []
        for identifier, endpoints in canonical.items():
            left, right = endpoints if rng.randrange(2) == 0 else endpoints[::-1]
            a.append({"pair_id": identifier, "left": left, "right": right})
        b = [{"pair_id": r["pair_id"], "left": r["right"], "right": r["left"]} for r in a]
        for offset, (orientation, rows) in enumerate((("a", a), ("b", b))):
            index = (panel - 1) * 2 + offset
            name = f"pair_panel{panel}_{orientation}.json"
            pair_seeds[name] = {"pair_order": 20261131 + index, "document_order": 20261135 + index}
            pairs[name] = {"documents": shuffled(documents, pair_seeds[name]["document_order"]),
                           "pairs": shuffled(rows, pair_seeds[name]["pair_order"])}
    validate_inputs(ranks, pairs, documents, canonical)
    batch_seeds = {1: 20261201, 2: 20261202}
    batches = make_pair_batches(pairs, batch_seeds)
    lengths = [len(row["text"]) for row in documents]
    metadata = {
        "purpose": "Blind inputs for within-model ranking aggregation and pairwise comparison; preparation only",
        "source_path": str(source), "excluded_pilot_metadata_path": str(old_metadata),
        "text_field": "Unmodified input_text: [ENTITY] target newline [TITLE] headline",
        "sampling": "Uniform 32-family sample without replacement after excluding all earlier 128 families; one uniform member per selected family, sorted by original ID before drawing",
        "population_samples": len(seen), "population_families": len(families),
        "excluded_family_count": len(excluded), "eligible_family_count": len(eligible),
        "selected_samples": N, "selected_families": len(set(selected)), "excluded_family_intersection_n": len(overlap),
        "family_seed": FAMILY_SEED, "within_family_seed": MEMBER_SEED,
        "rank_order_seeds": rank_seeds, "rank_panels": {"1": [1, 2, 3, 4], "2": [5, 6, 7, 8]},
        "panel_orientation_seeds": orientation_seeds, "pair_input_shuffle_seeds": pair_seeds,
        "canonical_pair_rule": "Lexicographic unordered combinations of S0001..S0032, numbered E0001..E0496",
        "canonical_pairs": [{"pair_id": key, "first": value[0], "second": value[1]} for key, value in canonical.items()],
        "orientation_rule": "Independent random left/right assignment by panel for a; b exactly reverses each stable pair ID. Separate pseudorandom streams shuffle pair and document order within each file",
        "all_models_share_inputs": True, "labels_or_predictions_used": False,
        "pair_batching": {"batch_count": 4, "pairs_per_batch": 124,
                          "panel_assignment_seeds": batch_seeds, "same_pair_ID_set_for_a_b_batch": True,
                          "reproduction_rule": "Shuffle sorted canonical pair IDs per panel, split into four blocks of 124, then retain original orientation-specific pair order and document order within each block"},
        "family_caveat": "Lexical connected components, not proven independent semantic events",
        "characters": {"unit": "Unicode code points including markers and newline", "minimum": min(lengths), "maximum": max(lengths), "total": sum(lengths)},
        "mapping": mapping,
    }
    target.mkdir(parents=True, exist_ok=False)
    for name, rows in ranks.items():
        with (target / name).open("x", encoding="utf-8", newline="\n") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    for name, value in {**pairs, **batches, "metadata.json": metadata}.items():
        with (target / name).open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    reread_ranks = {name: [json.loads(line) for line in (target / name).read_text(encoding="utf-8").splitlines()]
                    for name in ranks}
    reread_pairs = {name: read_json(target / name) for name in pairs}
    validate_inputs(reread_ranks, reread_pairs, documents, canonical)
    for name, value in batches.items():
        if read_json(target / name) != value:
            raise ValueError("Persisted pair batch differs from generated batch")
    reread_metadata = read_json(target / "metadata.json")
    if {r["family_id"] for r in reread_metadata["mapping"]} & excluded:
        raise ValueError("Persisted family mapping overlaps the prior pilot")
    print(json.dumps({"status": "created_and_reread_verified", "target": str(target),
                      "selected_samples": N, "selected_families": N,
                      "eligible_families": len(eligible), "excluded_family_intersection_n": 0,
                      "rank_input_files": len(ranks), "pair_input_files": len(pairs),
                      "unordered_pairs_per_file": len(canonical),
                      "exact_a_b_swaps_verified": True, "characters": metadata["characters"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
