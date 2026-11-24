"""Record orchestration metadata and validate real scorer outputs without editing them."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, default):
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else default

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "accept", "status"])
    parser.add_argument("call_ids", nargs="*")
    args = parser.parse_args()
    schedule = {r["call_id"]: r for r in read_json(ROOT / "schedule.json", [])}
    state_path = ROOT / "progress.json"
    state = read_json(state_path, {"completed": 0, "planned": 88, "scores": 0, "active": {}})
    log_path = ROOT / "calls.jsonl"
    logs = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()] if log_path.exists() else []
    accepted = {r["call_id"] for r in logs if r["status"] == "valid"}
    if args.action == "start":
        for cid in args.call_ids:
            assert cid in schedule and cid not in accepted and cid not in state["active"]
            state["active"][cid] = {"started_utc": now(), "attempt": 1 + sum(r["call_id"] == cid for r in logs)}
    elif args.action == "accept":
        for cid in args.call_ids:
            assert cid not in accepted and cid in state["active"]
            raw = ROOT / "raw" / f"{cid}.json"
            pairs = json.loads(raw.read_text(encoding="utf-8-sig"), object_pairs_hook=list)
            assert isinstance(pairs, list)
            assert len(pairs) == len(schedule[cid]["item_ids"])
            assert len({k for k, v in pairs}) == len(pairs), "duplicate ID"
            assert {k for k, v in pairs} == set(schedule[cid]["item_ids"]), "wrong IDs"
            assert all(type(v) is int and 0 <= v <= 100 for k, v in pairs), "invalid score"
            row = dict(call_id=cid, agent_path=f"/root/t3_scoring_runner/v2_{cid}", model="gpt-6-sol", reasoning_effort="low", fork_turns="none", **state["active"].pop(cid), completed_utc=now(), status="valid", score_count=len(pairs))
            with log_path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            logs.append(row)
            accepted.add(cid)
    state["completed"] = len(accepted)
    state["scores"] = sum(r["score_count"] for r in logs if r["status"] == "valid")
    state["updated_utc"] = now()
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(state))

if __name__ == "__main__":
    main()
