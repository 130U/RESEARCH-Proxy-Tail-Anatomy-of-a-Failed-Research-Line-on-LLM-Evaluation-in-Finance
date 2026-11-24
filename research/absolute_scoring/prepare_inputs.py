"""Reproducible text-blind selection; headline inputs stay outside the repository."""
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research/absolute_scoring"
PRIVATE = ROOT.parent / "proxy-tail-absolute-inputs"


def write_csv(path, fields, rows):
    with path.open("x", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    if PRIVATE.exists() or (OUT / "sample.csv").exists():
        raise FileExistsError("Refusing to replace an existing sample or input directory")
    prior_paths = ["agent_tail_pilot/metadata.json", "agent_tail_methods/stage1_n32/metadata.json", "agent_tail_methods/stage2_n128_sol/metadata.json"]
    excluded = set()
    for name in prior_paths:
        prior = json.loads((ROOT / "research/private" / name).read_text(encoding="utf-8"))
        excluded.update(x["family_id"] for x in prior["mapping"])
    assert len(excluded) == 288
    families = defaultdict(list)
    with (ROOT / "research/private/real_baseline/test.jsonl").open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            families[row["family_id"]].append({k: row[k] for k in ("id", "family_id", "input_text", "source_ids")})
    assert len(families) == 1570 and sum(map(len, families.values())) == 2107
    eligible = sorted(set(families) - excluded)
    assert len(eligible) == 1282
    selected = random.Random(2026111601).sample(eligible, 1000)
    member_rng = random.Random(2026111602)
    samples, texts = [], {}
    for i, family in enumerate(selected, 1):
        row = member_rng.choice(sorted(families[family], key=lambda x: x["id"]))
        aid = f"A{i:04d}"
        samples.append({"id": aid, "original_id": row["id"], "family_id": family, "source_ids": json.dumps(row["source_ids"])})
        texts[aid] = row["input_text"]
    control = sorted(random.Random(2026111603).sample(sorted(texts), 100))
    prompt = (OUT / "prompt.txt").read_text(encoding="utf-8")
    PRIVATE.mkdir()
    (OUT / "raw_scores").mkdir(exist_ok=True)
    batch_rows, schedule, control_batches = [], [], []
    for rnd in range(1, 9):
        order = sorted(texts)
        random.Random(2026111610 + rnd).shuffle(order)
        for batch in range(1, 26):
            ids = order[(batch - 1) * 40:batch * 40]
            key = f"r{rnd:02d}_b{batch:02d}"
            folder = PRIVATE / key
            folder.mkdir()
            items = [{"id": aid, "text": texts[aid]} for aid in ids]
            (folder / "input.txt").write_text(prompt + "\nItems:\n" + json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            batch_rows.extend({"input_key": key, "position": j, "id": aid} for j, aid in enumerate(ids, 1))
            schedule.append({"call_id": key, "kind": "main", "round": rnd, "batch": batch, "input_key": key})
            if rnd == 1 and set(ids) & set(control):
                control_batches.append(batch)
        if rnd in (2, 6):
            c = 1 if rnd == 2 else 2
            schedule.extend({"call_id": f"c{c}_b{b:02d}", "kind": "control", "round": c, "batch": b, "input_key": f"r01_b{b:02d}"} for b in control_batches)
    write_csv(OUT / "sample.csv", list(samples[0]), samples)
    write_csv(OUT / "control_ids.csv", ["id"], [{"id": x} for x in control])
    write_csv(OUT / "batches.csv", ["input_key", "position", "id"], batch_rows)
    write_csv(OUT / "schedule.csv", ["call_id", "kind", "round", "batch", "input_key"], schedule)
    assert len({x["family_id"] for x in samples}) == 1000
    assert not ({x["family_id"] for x in samples} & excluded)
    for rnd in range(1, 9):
        observed = [x["id"] for x in batch_rows if x["input_key"].startswith(f"r{rnd:02d}_")]
        assert len(observed) == 1000 and set(observed) == set(texts)
    print(json.dumps({"samples": 1000, "families": 1000, "excluded_families": 288, "eligible_families": 1282, "control_targets": 100, "control_batches": len(control_batches), "calls": len(schedule), "headline_inputs_outside_repository": str(PRIVATE)}))


if __name__ == "__main__":
    main()
