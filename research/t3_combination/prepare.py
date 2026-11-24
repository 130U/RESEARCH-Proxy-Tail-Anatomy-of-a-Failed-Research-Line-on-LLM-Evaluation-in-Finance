"""Create the frozen synthetic T3 inputs; never generate model scores."""
import csv
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTITY = "Virello Industries"
FACTS = {
    "P": [
        "wins a small supply contract worth 0.2% of annual revenue",
        "reports a 2% increase in recurring maintenance revenue",
        "reduces annual logistics costs by 5% through improved routing",
        "reports a 10% increase in quarterly operating profit",
        "raises its full-year free cash flow forecast by 15%",
        "reports a 25% increase in export orders",
        "secures its first license to sell into a major new overseas market",
        "wins an appeal canceling a fine equal to 30% of last year's profit",
        "wins a patent expected to double revenue at its specialty materials division",
        "repays all overdue debt and eliminates an imminent default risk",
    ],
    "N": [
        "incurs an unexpected filing fee equal to 0.2% of annual revenue",
        "loses one day's online sales during a website outage",
        "incurs warranty repair costs equal to 5% of last year's profit",
        "loses a distribution agreement accounting for 10% of retail sales",
        "cuts production at a domestic plant by 15% because of weak demand",
        "announces a product recall costing 25% of last year's profit",
        "loses a major customer accounting for 30% of annual revenue",
        "halts its largest factory for six months after a major fire",
        "faces an indefinite regulatory ban on its flagship product",
        "discovers fraud causing unrecoverable losses equal to 60% of its assets",
    ],
    "Z": [
        "schedules its annual shareholder meeting for June 18",
        "lists its registered office address on its website",
        "publishes the date of its next earnings call",
        "states that its fiscal year ends on December 31",
        "lists the names of its existing business divisions",
        "states that its headquarters is located in Westbridge",
        "posts a calendar of routine public holidays",
        "lists the telephone number of its investor relations office",
        "states that its ordinary shares use the ticker VIRI",
        "publishes the agenda for its scheduled annual meeting",
    ],
}


def write_csv(name, rows, fields):
    with (ROOT / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    if (ROOT / "raw").exists() and any((ROOT / "raw").glob("*.json")):
        raise RuntimeError("Scores already exist: refuse to overwrite frozen materials")
    atoms = [dict(atom_id=f"{p}{i:02d}", polarity=p, headline=f"{ENTITY} {fact}.")
             for p, facts in FACTS.items() for i, fact in enumerate(facts, 1)]
    opaque_ids = [f"I{i:04d}" for i in range(1, 31)]
    random.Random(2026111622).shuffle(opaque_ids)
    for atom, opaque_id in zip(atoms, opaque_ids):
        atom["atom_id"] = opaque_id
    by_id = {a["atom_id"]: a for a in atoms}
    groups = {p: [a["atom_id"] for a in atoms if a["polarity"] == p] for p in FACTS}
    pairs = [("PN", a, b) for a, b in itertools.product(groups["P"], groups["N"])]
    pairs += [(p+p, a, b) for p in ("P", "N") for a, b in itertools.combinations(groups[p], 2)]
    pairs += [(p+"0", a, b) for p in ("P", "N") for a, b in itertools.product(groups[p], groups["Z"])]
    items = [dict(item_id=a["atom_id"], kind="single", first=a["atom_id"], second="", headline=a["headline"]) for a in atoms]
    combos = []
    for kind, a, b in pairs:
        for first, second in ((a, b), (b, a)):
            combos.append(dict(item_id=f"C{len(combos)+1:04d}", kind=kind, first=first, second=second,
                               headline=by_id[first]["headline"].removesuffix(".") + "; " + by_id[second]["headline"]))
    items += combos
    write_csv("atoms.csv", atoms, ["atom_id", "polarity", "headline"])
    write_csv("items.csv", items, ["item_id", "kind", "first", "second", "headline"])
    prompt = (ROOT.parent / "absolute_scoring" / "prompt.txt").read_text(encoding="utf-8")
    (ROOT / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    (ROOT / "inputs").mkdir(exist_ok=True)
    (ROOT / "raw").mkdir(exist_ok=True)
    schedule = []
    item_map = {x["item_id"]: x for x in items}
    for phase, repetitions, ids in (("baseline", 8, [a["atom_id"] for a in atoms]), ("combination", 4, [a["item_id"] for a in combos])):
        for repeat in range(1, repetitions+1):
            shuffled = ids.copy()
            random.Random(2026111600 + (0 if phase == "baseline" else 100) + repeat).shuffle(shuffled)
            for batch, start in enumerate(range(0, len(shuffled), 40), 1):
                call_id = f"b{repeat:02d}" if phase == "baseline" else f"c{repeat:02d}_{batch:02d}"
                chosen = shuffled[start:start+40]
                schedule.append(dict(call_id=call_id, phase=phase, round=repeat, item_ids=chosen))
                payload = [{"id": i, "entity": ENTITY, "headline": item_map[i]["headline"]} for i in chosen]
                (ROOT / "inputs" / f"{call_id}.txt").write_text(prompt + "\nItems to score:\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (ROOT / "schedule.json").write_text(json.dumps(schedule, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"atoms": len(atoms), "unordered_pairs": len(pairs), "ordered_pairs": len(combos), "calls": len(schedule), "scores": sum(len(x["item_ids"]) for x in schedule)}))


if __name__ == "__main__":
    main()
