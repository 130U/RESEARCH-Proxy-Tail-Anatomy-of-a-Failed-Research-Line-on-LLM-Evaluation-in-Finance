"""Offline, read-only FOMC source-date audit; writes metadata beside this script.

No network client, model, raw-text export, or SEntFiN row reader is included.
This verifies local declarations and hashes, not historical public availability.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import platform
import re
import time
from datetime import date, datetime, timezone
from urllib.parse import urljoin, urlsplit
import unittest

MONTHS = "January February March April May June July August September October November December".split()
DATE_PATTERN = r"(?:" + "|".join(MONTHS) + r")\s+\d{1,2},?\s+\d{4}"
RELEASE = re.compile(r"(?:Released|Release\s+Date)\s*:?\s*(" + DATE_PATTERN + r")", re.I)
UPDATE = re.compile(r"Last\s+Update(?:d)?\s*:\s*(" + DATE_PATTERN + r")", re.I)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
DATE_KEYS = {"date", "datepublished", "datemodified", "pubdate", "publicationdate", "last-modified", "article:published_time", "article:modified_time", "dc.date", "dc.date.issued"}
RIGHTS_EVIDENCE_FILES = [
    "docs/research/expanded_corpus_sources_20261011.md",
    "docs/research/stance_sources_20261009.md",
    "docs/POST_DOMAIN_NEXT.md",
    "docs/TASK_REVIEW_NEXT.md",
    "docs/REVIEW_WORKSPACE.md",
    "docs/ENTITY_SFT_PILOT.md",
    "data/raw/candidates/sentfin/LICENSE",
    "runs/task_pilot/entity_v1/task_manifest.json",
]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_date(value: str) -> str | None:
    value = value.strip()
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})(?:[T ][0-9:.+Z-]+)?", value)
    if match:
        return date.fromisoformat(match.group(1)).isoformat()
    match = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", value)
    if match and match.group(1).lower() in [m.lower() for m in MONTHS]:
        return date(int(match.group(3)), [m.lower() for m in MONTHS].index(match.group(1).lower()) + 1, int(match.group(2))).isoformat()
    return None


def decode_html(raw: bytes) -> tuple[str, str]:
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        # Legacy Fed snapshot has cp1252 punctuation. Hashes always use raw bytes.
        return raw.decode("cp1252"), "cp1252-fallback"


class DateHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes = [{"tag": "root", "parent": None, "attrs": {}, "text": []}]
        self.stack = [0]
        self.machine_dates: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        index = len(self.nodes)
        self.nodes.append({"tag": tag, "parent": self.stack[-1], "attrs": attributes, "text": []})
        key = str(attributes.get("name") or attributes.get("property") or attributes.get("itemprop") or "").lower()
        if key in DATE_KEYS:
            value = attributes.get("content") or attributes.get("datetime") or ""
            normalized = normalize_date(value)
            self.machine_dates.append({"tag": tag, "field": key, "date": normalized, "value_parsed": normalized is not None})
        if tag == "time" and attributes.get("datetime"):
            normalized = normalize_date(attributes["datetime"])
            self.machine_dates.append({"tag": tag, "field": "datetime", "date": normalized, "value_parsed": normalized is not None})
        if tag not in VOID:
            self.stack.append(index)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for position in range(len(self.stack) - 1, 0, -1):
            if self.nodes[self.stack[position]]["tag"] == tag:
                self.stack = self.stack[:position]
                break

    def handle_data(self, value: str) -> None:
        if any(self.nodes[i]["tag"] in {"script", "style"} for i in self.stack):
            return
        for i in self.stack:
            self.nodes[i]["text"].append(value)

    def text(self, index: int = 0) -> str:
        return " ".join(" ".join(self.nodes[index]["text"]).split())


def parse_page(raw: bytes) -> tuple[DateHTML, str, list[dict]]:
    content, codec = decode_html(raw)
    parser = DateHTML()
    parser.feed(content)
    structured = []
    for key, value in re.findall(r'"(datePublished|dateModified)"\s*:\s*"([^"]+)"', content):
        parsed = normalize_date(value)
        structured.append({"field": key, "date": parsed, "value_parsed": parsed is not None})
    return parser, codec, structured


def normalized_link(value: str) -> tuple[str, str, str, str]:
    parsed = urlsplit(urljoin("https://www.federalreserve.gov/", value))
    return parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.query


def minutes_identity(value: str) -> str | None:
    """Recognize only known Fed minutes HTML/PDF routes, not arbitrary dates."""
    scheme, host, path, query = normalized_link(value)
    if scheme != "https" or host != "www.federalreserve.gov" or query:
        return None
    match = re.fullmatch(r"/monetarypolicy/fomcminutes(\d{8})\.htm", path)
    if match is None:
        match = re.fullmatch(r"/monetarypolicy/files/fomcminutes(\d{8})\.pdf", path)
    if match is None:
        return None
    identifier = match.group(1)
    try:
        date(int(identifier[:4]), int(identifier[4:6]), int(identifier[6:8]))
    except ValueError:
        return None
    return identifier


def linked_release_dates(parser: DateHTML, target_url: str) -> dict:
    document_identity = minutes_identity(target_url)
    if document_identity is None:
        return {"matching_link_count": 0, "status": "unsupported_target_identity", "release_dates": []}
    wanted = normalized_link(target_url)
    matched = [i for i, node in enumerate(parser.nodes) if node["tag"] == "a" and normalized_link(node["attrs"].get("href") or "") == wanted]
    if len(matched) != 1:
        return {"matching_link_count": len(matched), "status": "ambiguous_or_missing_link", "release_dates": []}
    index = parser.nodes[matched[0]]["parent"]
    # A local paragraph or minutes div is allowed; never search a year/page ancestor.
    for _ in range(3):
        if index is None:
            break
        node = parser.nodes[index]
        classes = (node["attrs"].get("class") or "").split()
        if node["tag"] == "p" or "fomc-meeting__minutes" in classes:
            # A unique target link and date are insufficient if another document
            # shares this container. All links must be supported aliases of one
            # minutes identity; HTML/PDF order does not matter.
            container_links = []
            for link_index, candidate in enumerate(parser.nodes):
                if candidate["tag"] != "a":
                    continue
                ancestor = link_index
                while ancestor is not None and ancestor != index:
                    ancestor = parser.nodes[ancestor]["parent"]
                if ancestor == index:
                    container_links.append(candidate["attrs"].get("href") or "")
            identities = [minutes_identity(link) for link in container_links]
            identity_evidence = {"container_link_count": len(container_links), "container_document_identity": document_identity}
            if any(identity is None for identity in identities):
                return {"matching_link_count": 1, "status": "unsupported_container_link_identity", "release_dates": [], **identity_evidence}
            if set(identities) != {document_identity}:
                return {"matching_link_count": 1, "status": "mixed_document_identities", "release_dates": [], **identity_evidence}
            found = [normalize_date(x) for x in RELEASE.findall(parser.text(index))]
            return {"matching_link_count": 1, "status": "local_release_label" if len(found) == 1 else "ambiguous_or_missing_date", "container": "paragraph" if node["tag"] == "p" else "minutes_div", "release_dates": found, **identity_evidence}
        index = node["parent"]
    return {"matching_link_count": 1, "status": "unsupported_link_container", "release_dates": []}


def local_file(base: Path, relative: str) -> Path:
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError("Source reference outside declared root or missing")
    return path


def audit(source_root: Path) -> dict:
    start = time.perf_counter()
    base = source_root.resolve() / "data/raw/expansion_v1/corpora"
    raw = local_file(base, "finance_candidate.jsonl").read_bytes()
    manifest_raw = local_file(base, "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    finance = manifest["finance"]
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if len(rows) < 10:
        raise ValueError("At least ten source records are required")
    for row in rows:
        date.fromisoformat(row["published_at"])
        date.fromisoformat(row["meeting_date"])
    rows.sort(key=lambda row: (row["published_at"], row["text_sha256"]))
    admitted = {row["text_sha256"]: row for row in finance["admitted"]}
    if len(admitted) != len(finance["admitted"]):
        raise ValueError("Duplicate admitted text hashes")
    discoveries = {item["file"]: item for item in finance["discovery_snapshots"]}
    snapshots = {}
    results = []
    for sample_index in range(10):
        rank = sample_index * (len(rows) - 1) // 9
        row = rows[rank]
        admitted_row = admitted[row["text_sha256"]]
        html = local_file(base, admitted_row["html_snapshot"]).read_bytes()
        parser, codec, structured = parse_page(html)
        year = int(row["meeting_date"][:4])
        discovery_name = "source_snapshots/fomc_calendar.html" if year >= 2021 else f"source_snapshots/fomc_history_{year}.html"
        if discovery_name not in snapshots:
            discovery_raw = local_file(base, discovery_name).read_bytes()
            discovery_parser, _, _ = parse_page(discovery_raw)
            snapshots[discovery_name] = (discovery_parser, sha(discovery_raw), discoveries[discovery_name]["sha256"])
        discovery_parser, discovery_hash, declared_discovery_hash = snapshots[discovery_name]
        linked = linked_release_dates(discovery_parser, row["source_url"])
        update_dates = [normalize_date(x) for x in UPDATE.findall(parser.text())]
        direct_release_dates = [normalize_date(x) for x in RELEASE.findall(parser.text())]
        checks = {
            "html_matches_record_and_manifest": sha(html) == row["html_sha256"] == admitted_row["html_sha256"],
            "text_matches_record_and_manifest": sha(row["text"].encode("utf-8")) == row["text_sha256"] == admitted_row["text_sha256"],
            "metadata_record_manifest_agree": all(row[k] == admitted_row[k] for k in ["meeting_date", "published_at"]) and row["source_url"] == admitted_row["url"],
            "discovery_snapshot_hash_matches": discovery_hash == declared_discovery_hash,
            "linked_release_matches_published": linked["status"] == "local_release_label" and linked["release_dates"] == [row["published_at"]],
            "page_update_matches_published": update_dates == [row["published_at"]],
            "published_after_meeting": row["published_at"] > row["meeting_date"],
        }
        results.append({
            "audit_id": f"FOMC-A{sample_index+1:02d}", "sorted_rank_zero_based": rank,
            "meeting_date": row["meeting_date"], "manifest_published_date": row["published_at"],
            "release_lag_days": (date.fromisoformat(row["published_at"]) - date.fromisoformat(row["meeting_date"])).days,
            "retrieved_at_declared": row["retrieved_at"], "html_decode": codec,
            "html_sha256": sha(html), "text_sha256": row["text_sha256"], "discovery_sha256": discovery_hash,
            "html_machine_dates": parser.machine_dates, "html_structured_dates": structured,
            "html_last_update_dates": update_dates, "html_direct_release_dates": direct_release_dates,
            "linked_index_release": linked, "checks": checks,
            "historical_byte_version_proven": False, "release_time_of_day_proven": False,
        })
    return {
        "schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_population": {"records": len(rows), "jsonl_sha256": sha(raw), "manifest_sha256": sha(manifest_raw), "count_matches_manifest": len(rows) == finance["documents"], "bytes_match_manifest": len(raw) == finance["bytes"], "hash_matches_manifest": sha(raw) == finance["sha256"], "published_date_min": rows[0]["published_at"], "published_date_max": rows[-1]["published_at"], "retrieved_at_declared": manifest["retrieved_at"], "candidates_only": manifest["candidates_only"]},
        "selection": {"method": "fixed equally spaced ranks after sorting by published_at,text_sha256", "formula": "rank_i = i*(N-1)//9 for i=0,...,9", "sample_size": 10, "random_sample": False, "population_error_rate_inference": False},
        "records": results,
        "rights_document_fingerprints": [{"source_relative_path": name, "sha256": sha(local_file(source_root, name).read_bytes())} for name in RIGHTS_EVIDENCE_FILES],
        "summary": {"all_selected_checks_pass": all(all(r["checks"].values()) for r in results), "release_matches": sum(r["checks"]["linked_release_matches_published"] for r in results), "page_update_matches": sum(r["checks"]["page_update_matches_published"] for r in results), "machine_date_fields_found": sum(len(r["html_machine_dates"])+len(r["html_structured_dates"]) for r in results), "discovery_snapshots_read": len(snapshots), "historical_version_proofs": 0},
        "limitations": ["Current local declarations only; no historical byte-version proof", "Date resolution does not prove release time or timezone", "Sources and selection collected in 2026; historical selection measurability unknown", "Ten fixed date-spread cases are not a random audit or a population rate estimate", "No source text, title, URL, or individual labels exported; date/hash metadata can still identify public documents"],
        "runtime": {"python": platform.python_version(), "elapsed_seconds": round(time.perf_counter()-start, 6), "peak_memory_measured": False, "network_requests": 0, "training_tokens": 0, "source_sha256": sha(Path(__file__).read_bytes())},
    }


class AuditTests(unittest.TestCase):
    def test_release_is_bound_to_link(self):
        p, _, _ = parse_page(b'<p><a href="/monetarypolicy/fomcminutes20200401.htm">x</a> Released May 01, 2020</p><p><a href="/monetarypolicy/fomcminutes20200402.htm">y</a> Released May 02, 2020</p>')
        self.assertEqual(linked_release_dates(p, "https://www.federalreserve.gov/monetarypolicy/fomcminutes20200401.htm")["release_dates"], ["2020-05-01"])

    def test_no_page_level_fallback(self):
        p, _, _ = parse_page(b'<div><a href="/monetarypolicy/fomcminutes20200401.htm">x</a></div><p>Released May 01, 2020</p>')
        self.assertEqual(linked_release_dates(p, "https://www.federalreserve.gov/monetarypolicy/fomcminutes20200401.htm")["status"], "unsupported_link_container")

    def test_duplicate_link_abstains(self):
        p, _, _ = parse_page(b'<p><a href="/monetarypolicy/fomcminutes20200401.htm">x</a><a href="/monetarypolicy/fomcminutes20200401.htm">x</a>Released May 01, 2020</p>')
        self.assertEqual(linked_release_dates(p, "https://www.federalreserve.gov/monetarypolicy/fomcminutes20200401.htm")["status"], "ambiguous_or_missing_link")

    def test_mixed_minutes_single_date_rejected(self):
        p, _, _ = parse_page(b'<p><a href="/monetarypolicy/fomcminutes20200401.htm">A</a><span><a href="/monetarypolicy/fomcminutes20200402.htm">B</a></span> Released May 02, 2020</p>')
        result = linked_release_dates(p, "https://www.federalreserve.gov/monetarypolicy/fomcminutes20200401.htm")
        self.assertEqual(result["status"], "mixed_document_identities")
        self.assertEqual(result["release_dates"], [])

    def test_same_minutes_html_pdf_aliases_both_orders(self):
        html = '<a href="/monetarypolicy/fomcminutes20200401.htm">HTML</a>'
        pdf = '<a href="/monetarypolicy/files/fomcminutes20200401.pdf">PDF</a>'
        for links in [html + pdf, pdf + html]:
            p, _, _ = parse_page(('<div class="fomc-meeting__minutes">'+links+' Released May 01, 2020</div>').encode())
            result = linked_release_dates(p, "https://www.federalreserve.gov/monetarypolicy/fomcminutes20200401.htm")
            self.assertEqual(result["status"], "local_release_label")
            self.assertEqual(result["container_link_count"], 2)
            self.assertEqual(result["container_document_identity"], "20200401")

    def test_unknown_link_even_with_same_digits_rejected(self):
        for unknown in ["/other/20200401.htm", "/a.htm", "https://elsewhere.example/monetarypolicy/files/fomcminutes20200401.pdf", "/monetarypolicy/files/fomcminutes20200401.pdf?variant=other"]:
            p, _, _ = parse_page(('<p><a href="/monetarypolicy/fomcminutes20200401.htm">A</a><a href="'+unknown+'">B</a> Released May 01, 2020</p>').encode())
            self.assertEqual(linked_release_dates(p, "https://www.federalreserve.gov/monetarypolicy/fomcminutes20200401.htm")["status"], "unsupported_container_link_identity")

    def test_generic_target_is_not_a_minutes_identity(self):
        p, _, _ = parse_page(b'<p><a href="/a.htm">A</a><a href="/b.htm">B</a> Released May 02, 2020</p>')
        self.assertEqual(linked_release_dates(p, "https://www.federalreserve.gov/a.htm")["status"], "unsupported_target_identity")

    def test_two_release_dates_for_one_identity_abstains(self):
        p, _, _ = parse_page(b'<p><a href="/monetarypolicy/fomcminutes20200401.htm">A</a> Released May 01, 2020 Released May 02, 2020</p>')
        self.assertEqual(linked_release_dates(p, "https://www.federalreserve.gov/monetarypolicy/fomcminutes20200401.htm")["status"], "ambiguous_or_missing_date")

    def test_date_channels_are_separate(self):
        p, _, structured = parse_page(b'<meta name="datePublished" content="2020-05-01"><script>{"dateModified":"2021-01-01"}</script><p>Last Update: May 02, 2020</p>')
        self.assertEqual(p.machine_dates[0]["date"], "2020-05-01")
        self.assertEqual(structured[0]["date"], "2021-01-01")
        self.assertEqual([normalize_date(x) for x in UPDATE.findall(p.text())], ["2020-05-02"])
        self.assertNotIn("dateModified", p.text())

    def test_cp1252_and_dates(self):
        self.assertEqual(decode_html(b"legacy \x96 punctuation")[1], "cp1252-fallback")
        self.assertEqual(normalize_date("February 16, 2011"), "2011-02-16")
        self.assertIsNone(normalize_date("not a date"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if args.source_root is None:
        parser.error("--source-root is required for the local audit")
    result = audit(args.source_root)
    output = Path(__file__).resolve().parent / "source_audit.json"
    if output.is_relative_to(args.source_root.resolve()):
        raise ValueError("Output must not be inside the read-only source repository")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"output": output.name, "summary": result["summary"], "runtime": result["runtime"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
