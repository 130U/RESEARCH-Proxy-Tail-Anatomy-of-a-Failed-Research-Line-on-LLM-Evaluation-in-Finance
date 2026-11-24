"""Find review candidates, not confirmed same-fact duplicates.

Requires overlapping rounding intervals, differing precision, and a shared
metric word. Unit hints may be ambiguous. No estimate of duplicate prevalence
or answer determinacy is produced.
"""
from pathlib import Path
from decimal import Decimal
import csv
import html
import json
import re

HERE = Path(__file__).resolve().parent
SCALES = {"billion": Decimal(10)**9, "million": Decimal(10)**6, "thousand": Decimal(10)**3}
STOP = {"total", "net", "other", "and", "the", "for", "of", "in", "to", "at", "as", "a", "s", "year", "years", "december", "january", "balance"}
TEXT_NUM = re.compile(r"(?<![\w.])(?P<num>\d[\d,]*(?:\.\d+)?)\s+(?P<unit>billion|million|thousand)s?\b")

def words(s):
    return {t for t in re.findall(r"[a-z]+", s.lower()) if len(t)>2 and t not in STOP}

def num(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).strip().replace(",", "").replace("$", "").strip()
    if not re.fullmatch(r"\d+(?:\.\d+)?", s):
        return None
    value = Decimal(s)
    half = Decimal(5) * (Decimal(10) ** (-(len(s.split('.')[1]) if '.' in s else 0)-1))
    return value, half

def main():
    seen = set()
    candidates = []
    datasets = {split: json.loads((HERE / "data" / "finqa" / f"{split}.json").read_text(encoding="utf-8")) for split in ["dev", "test", "train"]}
    page_questions = {}
    for data in datasets.values():
        for item in data:
            page_questions.setdefault(item["filename"], []).append(item)
    for split in ["dev", "test", "train"]:
        data = datasets[split]
        for item in data:
            filename = item["filename"]
            if filename in seen:
                continue
            seen.add(filename)
            table = item["table_ori"]
            texts = [("pre_text", i, t) for i, t in enumerate(item["pre_text"])] + [("post_text", i, t) for i, t in enumerate(item["post_text"])]
            table_hints = [(unit, f"table_ori[{r}][{c}]: {cell}") for r,row in enumerate(table) for c,cell in enumerate(row) for unit in SCALES if re.search(r"\b"+unit+r"s?\b",cell.lower())]
            # Narrative hints only nominate a scale, never establish the table unit.
            if not table_hints:
                table_hints = [(unit, f"{section}[{i}]: {text[:140]}") for section,i,text in texts for unit in SCALES if re.search(r"\bin "+unit+r"s?\b", text.lower())]
            if not table_hints:
                continue
            table_hints = list(dict.fromkeys(table_hints))
            mentions = []
            for section,ti,text in texts:
                for match in TEXT_NUM.finditer(text):
                    n = num(match.group("num"))
                    if n:
                        unit = match.group("unit")
                        mentions.append((section,ti,text,match.group(0),n[0]*SCALES[unit],n[1]*SCALES[unit]))
            for ri,row in enumerate(table[1:], 1):
                label = row[0]
                tokens = words(label)
                if not tokens:
                    continue
                for ci,cell in enumerate(row[1:], 1):
                    n = num(cell)
                    if not n or n[0]<=0:
                        continue
                    related = []
                    for q in page_questions[filename]:
                        p=q["qa"]["program"]
                        literals=[Decimal(v) for v in re.findall(r"(?<![#\w.])\d+(?:\.\d+)?(?![\w.])",p.replace("const_", ""))]
                        if n[0] in literals or ("table_" in p and label.lower() in p.lower()):
                            related.append(q["id"])
                    for unit,hint in table_hints:
                        value,half=n[0]*SCALES[unit],n[1]*SCALES[unit]
                        for section,ti,text,mention,pvalue,phalf in mentions:
                            overlap=tokens & words(text)
                            if not overlap or half == phalf or abs(value-pvalue) > half+phalf:
                                continue
                            candidates.append({"split":split,"example_id":item["id"],"filename":filename,"row":ri,"column":ci,"row_label":label,"table_value":cell,"table_unit_candidate":unit,"table_unit_hint":hint,"text_location":f"{section}[{ti}]","text_mention":mention,"text":text,"shared_words":" ".join(sorted(overlap)),"table_base_value":str(value),"text_base_value":str(pvalue),"table_base_halfunit":str(half),"text_base_halfunit":str(phalf),"operand_value_match_ids":";".join(related),"status":"candidate_not_confirmed"})
    # One best candidate per source location pair, then varied reports.
    candidates.sort(key=lambda x:(not bool(x["operand_value_match_ids"]), -len(x["shared_words"].split()), x["filename"], x["row"], x["column"]))
    test_candidates=[]
    test_keys=set()
    for c in candidates:
        if c["split"]!="test":
            continue
        key=(c["filename"],c["row"],c["column"],c["text_location"],c["text_mention"],c["table_unit_candidate"])
        if key not in test_keys:
            test_keys.add(key)
            test_candidates.append(c)
    test_candidates.sort(key=lambda c:(c["filename"],c["row"],c["column"],c["text_location"],c["text_mention"]))
    test_path=HERE / "duplicate_precision_test_candidates.csv"
    with test_path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(test_candidates[0]) if test_candidates else ["status"],lineterminator="\n")
        writer.writeheader()
        writer.writerows(test_candidates)
    print(f"Complete test scan: {len(test_candidates)} candidate location pairs; {len({c['filename'] for c in test_candidates})} pages; {len({(c['filename'],c['row'],c['column']) for c in test_candidates})} table cells. Heuristic candidates only.")
    unique=[]
    keys=set()
    perdoc={}
    for c in candidates:
        key=(c["filename"],c["row"],c["column"],c["text_location"],c["text_mention"])
        if key in keys or perdoc.get(c["filename"],0)>=3:
            continue
        keys.add(key)
        perdoc[c["filename"]]=perdoc.get(c["filename"],0)+1
        unique.append(c)
        if len(unique)==100:
            break
    path=HERE / "duplicate_precision_candidates.csv"
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(unique[0]) if unique else ["status"],lineterminator="\n")
        writer.writeheader()
        writer.writerows(unique)
    print(f"Saved {len(unique)} deliberately capped candidates from {len(perdoc)} pages; not a prevalence estimate.")
    for c in unique[:18]:
        print(c["example_id"],c["row_label"],c["table_value"],c["table_unit_candidate"],c["text_location"],c["text_mention"],c["text"][:350])

if __name__ == "__main__":
    main()
