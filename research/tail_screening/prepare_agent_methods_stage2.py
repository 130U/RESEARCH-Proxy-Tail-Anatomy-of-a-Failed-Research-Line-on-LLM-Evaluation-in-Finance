"""Prepare the new Sol-only 128-family validation inputs; no scoring or training.

Excludes both earlier pilots in full. Fixed seeds; private outputs only; refuses
to overwrite a stage directory. Never uses labels, predictions or sentiment for
selection. Copies the stage-1 semantic instructions byte for byte.
"""
from collections import defaultdict
import json
from pathlib import Path
import random


def main():
    root = Path(__file__).resolve().parents[2]
    target = (root / "research/private/agent_tail_methods/stage2_n128_sol").resolve()
    research = (root / "research").resolve(strict=True)
    methods = (research / "private/agent_tail_methods").resolve()
    if (Path(__file__).resolve().parent != research / "tail_screening"
            or not research.is_relative_to(root)
            or not methods.is_relative_to(research / "private")
            or target.parent != methods):
        raise RuntimeError("Unexpected worktree or escaped target")
    if target.exists():
        raise FileExistsError("Refuse to overwrite existing stage-2 directory")
    source = (root / "research/private/real_baseline/test.jsonl").resolve(strict=True)
    prior_paths = [root / "research/private/agent_tail_pilot/metadata.json",
                   root / "research/private/agent_tail_methods/stage1_n32/metadata.json"]
    prior_sets = []
    for path, expected_count in zip(prior_paths, (128, 32)):
        prior = json.loads(path.read_text(encoding="utf-8"))
        families = {row["family_id"] for row in prior["mapping"]}
        if len(prior["mapping"]) != expected_count or len(families) != expected_count:
            raise ValueError("Earlier pilot family mapping has unexpected size")
        prior_sets.append(families)
    excluded = set.union(*prior_sets)
    if len(excluded) != 160 or prior_sets[0] & prior_sets[1]:
        raise ValueError("Earlier pilot families are not 160 distinct families")
    instruction_source = root / "research/private/agent_tail_methods/stage1_n32/rank_instructions.txt"
    instructions = instruction_source.read_bytes()
    families, source_ids = defaultdict(list), set()
    with source.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            row = json.loads(line)
            identifier, family, text = row["id"], row["family_id"], row["input_text"]
            if (not all(type(v) is str and v for v in (identifier, family, text))
                    or identifier in source_ids or row["split"] != "test"):
                raise ValueError("Invalid source ID/family/text or split")
            if text != "[ENTITY] " + row["target"] + "\n[TITLE] " + row["headline"]:
                raise ValueError("Source text contract changed")
            source_ids.add(identifier)
            families[family].append({"original_id": identifier, "family_id": family,
                                    "text": text, "source_line": line_number,
                                    "original_source_ids": row["source_ids"]})
    if not excluded <= set(families):
        raise ValueError("Earlier family missing from fixed source population")
    eligible = sorted(set(families) - excluded)
    if len(eligible) != 1410:
        raise ValueError("Expected 1410 remaining families")
    selected = random.Random(20261216).sample(eligible, 128)
    member_rng = random.Random(20261217)
    documents, mapping = [], []
    for index, family in enumerate(selected, 1):
        members = sorted(families[family], key=lambda row: row["original_id"])
        item = member_rng.choice(members)
        blind_id = f"V{index:04d}"
        documents.append({"id": blind_id, "text": item["text"]})
        mapping.append({"blind_id": blind_id,
                        **{key: value for key, value in item.items() if key != "text"},
                        "family_size_in_test": len(members)})
    if set(selected) & excluded or len(set(selected)) != 128:
        raise ValueError("New family selection overlaps earlier data")
    seeds = {f"rank_order{i}.jsonl": 20261217 + i for i in range(1, 9)}
    orders = {}
    for name, seed in seeds.items():
        rows = list(documents)
        random.Random(seed).shuffle(rows)
        orders[name] = rows
    lengths = [len(row["text"]) for row in documents]
    metadata = {
        "stage": "stage2_n128_sol", "selected_branch": "Sol plus four-ranking Borda aggregation per panel",
        "source_path": str(source), "excluded_metadata_paths": [str(p) for p in prior_paths],
        "instruction_source_path": str(instruction_source), "instructions_copied_byte_for_byte": True,
        "sampling": "Uniformly choose 128 different eligible families without replacement from sorted family IDs, then uniformly choose one sorted-ID member per family using a separate fixed stream",
        "population_samples": len(source_ids), "population_families": len(families),
        "excluded_prior_family_counts": [len(s) for s in prior_sets],
        "excluded_family_count": len(excluded), "eligible_family_count": len(eligible),
        "eligible_sample_count": sum(len(families[f]) for f in eligible),
        "selected_samples": 128, "selected_families": len(set(selected)),
        "excluded_family_intersection_n": len(set(selected) & excluded),
        "family_seed": 20261216, "within_family_seed": 20261217,
        "rank_order_seeds": seeds, "rank_panels": {"1": [1, 2, 3, 4], "2": [5, 6, 7, 8]},
        "blind_fields": ["id", "text"], "text_source": "Unmodified input_text: ENTITY and TITLE fields",
        "labels_or_predictions_used": False,
        "family_caveat": "Lexical groups do not establish independent semantic events",
        "characters": {"unit": "Unicode code points including field markers/newline",
                       "minimum": min(lengths), "maximum": max(lengths), "total": sum(lengths)},
        "mapping": mapping,
    }
    target.mkdir(parents=True, exist_ok=False)
    for name, rows in orders.items():
        with (target / name).open("x", encoding="utf-8", newline="\n") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    with (target / "metadata.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(metadata, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    with (target / "rank_instructions.txt").open("xb") as stream:
        stream.write(instructions)
    expected = {row["id"]: row["text"] for row in documents}
    observed_orders = []
    for name in orders:
        rows = [json.loads(line) for line in (target / name).read_text(encoding="utf-8").splitlines()]
        if (len(rows) != 128 or any(set(row) != {"id", "text"} for row in rows)
                or len({row["id"] for row in rows}) != 128
                or {row["id"]: row["text"] for row in rows} != expected):
            raise ValueError("Persisted blind file failed schema/ID/text verification")
        observed_orders.append(tuple(row["id"] for row in rows))
    copied = json.loads((target / "metadata.json").read_text(encoding="utf-8"))
    if len({r["family_id"] for r in copied["mapping"]}) != 128 or {r["family_id"] for r in copied["mapping"]} & excluded:
        raise ValueError("Persisted family mapping is not disjoint")
    if (target / "rank_instructions.txt").read_bytes() != instructions or len(set(observed_orders)) != 8:
        raise ValueError("Instruction copy or independent order verification failed")
    print(json.dumps({"status": "created_and_reread_verified", "target": str(target),
                      "population_samples": len(source_ids), "population_families": len(families),
                      "excluded_families": len(excluded), "eligible_families": len(eligible),
                      "eligible_samples": metadata["eligible_sample_count"],
                      "selected_samples": 128, "selected_families": 128,
                      "excluded_family_intersection_n": 0, "distinct_rank_orders": 8,
                      "instructions_byte_identical": True, "characters": metadata["characters"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
