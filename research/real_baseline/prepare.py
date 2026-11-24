"""Offline source-native SEntFiN preparation; row-level outputs stay private.

No source sentiment is renamed as investment stance. No training is performed.
Lexical groups are not audited semantic events and the split is not temporal.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import platform
import re
import time
import unicodedata

LABELS = ("negative", "neutral", "positive")
SPLITS = ("train", "development", "test")
HEADERS = ("S No.", "Title", "Decisions", "Words")
SEED = 130
EXPECTED_SOURCE_SHA256 = "570af7ba58f724f3fcc414dd5ba80da5b1a3b342134d76c6ebdf53a32c54a92f"
EXPECTED_SOURCE_ROWS = 10753
THRESHOLD_NUMERATOR = 4
THRESHOLD_DENOMINATOR = 5


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def title_tokens(value: str) -> frozenset[str]:
    return frozenset(re.findall(r"\w+", normalized(value), flags=re.UNICODE))


class QuarantineError(ValueError):
    """Carries a fixed reason code, never the private offending text."""


def parse_decisions(raw: str) -> list[tuple[str, str]]:
    if not isinstance(raw, str) or len(raw) > 100_000:
        raise QuarantineError("invalid_decisions_size_or_type")
    try:
        tree = ast.parse(raw, mode="eval")
    except (SyntaxError, ValueError, RecursionError):
        raise QuarantineError("decisions_syntax_error") from None
    if not isinstance(tree.body, ast.Dict) or not tree.body.keys:
        raise QuarantineError("decisions_not_nonempty_dict")
    seen_raw, seen_normal = set(), set()
    for key_node, value_node in zip(tree.body.keys, tree.body.values):
        try:
            key, value = ast.literal_eval(key_node), ast.literal_eval(value_node)
        except (ValueError, TypeError, SyntaxError, RecursionError):
            raise QuarantineError("nonliteral_decision_entry") from None
        if not isinstance(key, str) or not normalized(key) or not isinstance(value, str):
            raise QuarantineError("invalid_entity_or_label_type")
        if key in seen_raw:
            raise QuarantineError("duplicate_entity_key")
        if normalized(key) in seen_normal:
            raise QuarantineError("duplicate_normalized_entity_key")
        seen_raw.add(key)
        seen_normal.add(normalized(key))
        if value not in LABELS:
            raise QuarantineError("unknown_source_label")
    # Inspecting original AST keys above prevents literal_eval's last-key wins.
    try:
        evaluated = ast.literal_eval(tree)
    except (ValueError, TypeError, SyntaxError, RecursionError):
        raise QuarantineError("invalid_literal_decisions") from None
    return list(evaluated.items())


class DisjointSet:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, a: int, b: int) -> None:
        a, b = self.find(a), self.find(b)
        if a == b:
            return
        if self.size[a] < self.size[b] or (self.size[a] == self.size[b] and a > b):
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]


def meets_jaccard(left: frozenset[str], right: frozenset[str]) -> bool:
    # Empty token sets do not have a Jaccard identity in this contract.
    # Only exact normalized titles can merge those cases.
    if not left or not right:
        return False
    intersection = len(left & right)
    union = len(left) + len(right) - intersection
    return THRESHOLD_DENOMINATOR * intersection >= THRESHOLD_NUMERATOR * union


def exact_near_edges(sets: list[frozenset[str]]) -> tuple[list[tuple[int, int]], dict]:
    """Complete prefix join, followed by exact integer Jaccard verification.

    Globally order tokens by (document frequency, token). For t=4/5 use
    prefix length |X|-ceil(t|X|)+1. If J(A,B)>=t, their earliest common
    token must lie in both prefixes: otherwise overlap<ceil(t|A|) or
    overlap<ceil(t|B|), contradicting J>=t. Thus no qualifying pair is
    dropped by this filter. Empty sets are expressly out of this relation.
    """
    frequency = Counter(token for tokens in sets for token in tokens)
    postings = defaultdict(list)
    edges = []
    candidates_examined = length_filtered = 0
    for index, tokens in enumerate(sets):
        if not tokens:
            continue
        ordered = sorted(tokens, key=lambda token: (frequency[token], token))
        required_overlap = (THRESHOLD_NUMERATOR * len(tokens) + THRESHOLD_DENOMINATOR - 1) // THRESHOLD_DENOMINATOR
        prefix = ordered[:len(tokens) - required_overlap + 1]
        candidates = set()
        for token in prefix:
            candidates.update(postings[token])
        for other in sorted(candidates):
            lo, hi = sorted((len(tokens), len(sets[other])))
            if THRESHOLD_DENOMINATOR * lo < THRESHOLD_NUMERATOR * hi:
                length_filtered += 1
                continue
            candidates_examined += 1
            if meets_jaccard(tokens, sets[other]):
                edges.append((other, index))
        for token in prefix:
            postings[token].append(index)
    return edges, {"exact_pairs_evaluated": candidates_examined, "length_filtered_candidates": length_filtered, "all_pairs_upper_count": len(sets) * (len(sets) - 1) // 2, "near_edges": len(edges), "tokenless_normalized_titles": sum(not tokens for tokens in sets)}


def group_titles(titles: list[str]) -> tuple[dict[str, str], list[tuple[str, str]], dict]:
    unique = sorted({normalized(title) for title in titles if isinstance(title, str) and normalized(title)})
    sets = [title_tokens(title) for title in unique]
    edges, statistics = exact_near_edges(sets)
    dsu = DisjointSet(len(unique))
    for a, b in edges:
        dsu.union(a, b)
    components = defaultdict(list)
    for i, title in enumerate(unique):
        components[dsu.find(i)].append(title)
    mapping = {}
    for members in components.values():
        family = "family_" + digest(json_bytes(sorted(members)))
        for title in members:
            mapping[title] = family
    statistics.update({"unique_normalized_titles": len(unique), "lexical_components_total": len(components), "largest_component_normalized_titles": max(map(len, components.values()), default=0), "component_normalized_title_size_histogram": dict(sorted(Counter(map(len, components.values())).items()))})
    return mapping, [(unique[a], unique[b]) for a, b in edges], statistics


def split_for_family(family_id: str) -> str:
    integer = int(digest(f"sentfin-source-native-split-v1|seed={SEED}|{family_id}".encode()), 16)
    scale = 1 << 256
    if integer * 100 < 70 * scale:
        return "train"
    if integer * 100 < 85 * scale:
        return "development"
    return "test"


def prepare_records(records: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Pure preparation; records are private. Does not require all splits nonempty.

    Grouping uses every valid title before examining labels, including titles
    whose decisions will subsequently be quarantined. This preserves a fixed
    label-blind similarity graph and any bridges through quarantined rows.
    """
    family, edges, group_stats = group_titles([r.get("Title") for r in records])
    source_counts = Counter(r.get("S No.", "").strip() for r in records if isinstance(r.get("S No."), str))
    quarantine = []
    pairs = defaultdict(list)
    parse_accepted_rows = 0
    for row_number, record in enumerate(records, start=1):
        source_id = record.get("S No.")
        headline = record.get("Title")
        reason = None
        if not isinstance(source_id, str) or not source_id.strip():
            reason = "missing_source_id"
        elif source_counts[source_id.strip()] != 1:
            reason = "duplicate_source_id"
        elif not isinstance(headline, str) or not normalized(headline):
            reason = "empty_or_invalid_headline"
        elif set(record) != set(HEADERS) or any(record.get(key) is None for key in HEADERS):
            reason = "invalid_csv_row_shape"
        if reason is None:
            try:
                decisions = parse_decisions(record["Decisions"])
            except QuarantineError as exc:
                reason = str(exc)
        if reason is not None:
            quarantine.append({"stage": "row", "reason": reason, "row_number": row_number, "raw_row": record})
            continue
        parse_accepted_rows += 1
        for target, label in decisions:
            key = (normalized(headline), normalized(target))
            pairs[key].append({"source_id": source_id.strip(), "row_number": row_number, "headline": headline, "target": target, "label": label})
    rows = []
    conflicts = merged_duplicate_pairs = 0
    for key in sorted(pairs):
        members = pairs[key]
        if len({member["label"] for member in members}) != 1:
            conflicts += 1
            quarantine.append({"stage": "entity_title", "reason": "conflicting_labels_same_normalized_entity_title", "members": members})
            continue
        member = min(members, key=lambda item: item["row_number"])
        family_id = family[key[0]]
        merged_duplicate_pairs += len(members) - 1
        rows.append({
            "id": "sample_" + digest(json_bytes(key)),
            "headline": member["headline"], "target": member["target"],
            "label": member["label"], "label_id": LABELS.index(member["label"]),
            "family_id": family_id, "split": split_for_family(family_id),
            "source_ids": sorted({item["source_id"] for item in members}),
            "input_text": "[ENTITY] " + member["target"] + "\n[TITLE] " + member["headline"],
            "entity_literal_substring": member["target"] in member["headline"],
            "entity_normalized_substring": normalized(member["target"]) in normalized(member["headline"]),
        })
    rows.sort(key=lambda row: row["id"])
    by_family = defaultdict(set)
    by_title = defaultdict(set)
    for row in rows:
        by_family[row["family_id"]].add(row["split"])
        by_title[normalized(row["headline"])].add(row["split"])
    exact_cross_split = sum(len(values) > 1 for values in by_title.values())
    near_cross_split = sum(split_for_family(family[a]) != split_for_family(family[b]) for a, b in edges)
    if len({row["id"] for row in rows}) != len(rows) or any(len(x) != 1 for x in by_family.values()) or exact_cross_split or near_cross_split:
        raise RuntimeError("Internal identity or split-isolation invariant failed")
    split_counts = {}
    for split in SPLITS:
        selected = [row for row in rows if row["split"] == split]
        split_counts[split] = {"samples": len(selected), "families": len({r["family_id"] for r in selected}), "normalized_titles": len({normalized(r["headline"]) for r in selected}), "source_rows_represented": len({source_id for r in selected for source_id in r["source_ids"]}), "class_counts": {label: sum(r["label"] == label for r in selected) for label in LABELS}, "entity_not_literal_substring": sum(not r["entity_literal_substring"] for r in selected), "entity_not_normalized_substring": sum(not r["entity_normalized_substring"] for r in selected)}
    stats = {
        "source_rows": len(records), "row_parse_accepted": parse_accepted_rows,
        "row_quarantined": sum(q["stage"] == "row" for q in quarantine),
        "quarantine_reasons": dict(Counter(q["reason"] for q in quarantine)),
        "conflicting_normalized_entity_title_pairs": conflicts,
        "merged_duplicate_entity_title_occurrences": merged_duplicate_pairs,
        "retained_samples": len(rows), "retained_families": len(by_family),
        "largest_component_retained_samples": max(Counter(r["family_id"] for r in rows).values(), default=0),
        "retained_family_sample_size_histogram": dict(sorted(Counter(Counter(r["family_id"] for r in rows).values()).items())),
        "class_counts": dict(Counter(r["label"] for r in rows)),
        "entity_not_literal_substring": sum(not r["entity_literal_substring"] for r in rows),
        "entity_not_normalized_substring": sum(not r["entity_normalized_substring"] for r in rows),
        "splits": split_counts, "grouping": group_stats,
        "checks": {"unique_sample_ids": True, "family_cross_split_count": 0, "exact_title_cross_split_count": exact_cross_split, "near_edge_cross_split_count": near_cross_split, "all_training_labels_present": all(split_counts["train"]["class_counts"][label] > 0 for label in LABELS)},
    }
    return rows, quarantine, stats


def run(source: Path, private_dir: Path, aggregate_path: Path) -> dict:
    start = time.perf_counter()
    research = Path(__file__).resolve().parent.parent
    private_root = (research / "private").resolve()
    private_dir, aggregate_path = private_dir.resolve(), aggregate_path.resolve()
    if not private_dir.is_relative_to(private_root) or private_dir == private_root:
        raise ValueError("Row-level output must be inside research/private/<run-directory>")
    if not aggregate_path.is_relative_to((research / "real_baseline").resolve()):
        raise ValueError("Aggregate output must stay inside research/real_baseline")
    output_names = ["rows.jsonl", "train.jsonl", "development.jsonl", "test.jsonl", "quarantine.jsonl"]
    if aggregate_path.exists() or any((private_dir / name).exists() for name in output_names):
        raise FileExistsError("Frozen outputs exist; use a new explicitly versioned run, never overwrite")
    source_raw = source.read_bytes()
    if digest(source_raw) != EXPECTED_SOURCE_SHA256:
        raise ValueError("Source SHA256 differs from the preregistered input; preparation stopped")
    # Parse the very bytes fingerprinted above, avoiding a two-read race.
    with io.StringIO(source_raw.decode("utf-8-sig"), newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if tuple(reader.fieldnames or ()) != HEADERS:
            raise ValueError("Unexpected source CSV schema")
        records = list(reader)
    if len(records) != EXPECTED_SOURCE_ROWS:
        raise ValueError("Source row count differs from the preregistered input")
    rows, quarantine, stats = prepare_records(records)
    if any(stats["splits"][split]["samples"] == 0 for split in SPLITS):
        raise ValueError("A frozen split is empty; report failure rather than choose a new seed")
    payloads = {"rows.jsonl": b"".join(json_bytes(row) for row in rows), "quarantine.jsonl": b"".join(json_bytes(row) for row in quarantine)}
    for split in SPLITS:
        payloads[split+".jsonl"] = b"".join(json_bytes(row) for row in rows if row["split"] == split)
    private_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        with (private_dir / name).open("xb") as stream:
            stream.write(payload)
    result = {
        "schema_version": 1, "task": "source-native entity financial sentiment; not investment stance",
        "source": {"filename": source.name, "bytes": len(source_raw), "sha256": digest(source_raw)},
        "labels": list(LABELS), "statistics": stats,
        "contract": {
            "normalization": "Unicode NFKC, casefold, whitespace collapse; no numeric removal",
            "tokenization_for_grouping": "Unicode regex \\w+ token set including numbers",
            "near_duplicate_rule": "exact Jaccard >=4/5, complete global-frequency prefix join, transitive connected components",
            "empty_token_rule": "no Jaccard edge; normalized exact duplicates only",
            "grouping_population": "all source rows with valid nonempty headline, before parsing labels",
            "conflict_rule": "quarantine all instances of same normalized title+entity with different source labels",
            "duplicate_key_rule": "inspect original AST keys before literal_eval; exact/normalized duplicate entity keys quarantine entire source row",
            "duplicate_pair_rule": "merge same normalized title+entity+label and retain all source IDs",
            "split_seed": SEED, "split_proportions": {"train": "7/10", "development": "3/20", "test": "3/20"},
            "split_rule": "SHA256('sentfin-source-native-split-v1|seed=130|'+family_id), exact integer thresholds 70/100 and 85/100",
            "split_is_temporal": False, "semantic_event_audit_complete": False,
            "input_fields": "[ENTITY] target followed by newline and [TITLE] headline",
            "nonliteral_entities": "retained and counted; no identity verification implied",
            "vectorizer_fit": "not run here; downstream vectorizer must fit train only",
            "row_outputs_private": True,
        },
        "private_artifact_fingerprints": {name: {"bytes": len(payload), "sha256": digest(payload)} for name, payload in payloads.items()},
        "runtime": {"python": platform.python_version(), "source_code_sha256": digest(Path(__file__).read_bytes()), "elapsed_seconds": round(time.perf_counter()-start, 6), "peak_memory_measured": False, "network_requests": 0, "training_tokens": 0},
    }
    aggregate_path.parent.mkdir(parents=True, exist_ok=True)
    with aggregate_path.open("xb") as stream:
        stream.write(json_bytes(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, default=Path("research/private/real_baseline"))
    parser.add_argument("--aggregate", type=Path, default=Path("research/real_baseline/aggregate_manifest.json"))
    args = parser.parse_args()
    result = run(args.source, args.private_dir, args.aggregate)
    print(json.dumps({"aggregate_file": args.aggregate.name, "statistics": result["statistics"], "runtime": result["runtime"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
