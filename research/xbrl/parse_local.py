"""Bounded offline inline-XBRL XML reader, NOT an XBRL conformance validator.

Only nonFraction facts with unformatted decimal text, simple unit and explicit
instant/duration contexts. Unsupported facts abstain; raw text is never guessed.
No network, taxonomy resolution, acceptance-time certification or HTML recovery.
"""
from __future__ import annotations
import argparse
from datetime import date
from decimal import Decimal, localcontext
import hashlib
from io import StringIO
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

IX = "http://www.xbrl.org/2013/inlineXBRL"
XBRLI = "http://www.xbrl.org/2003/instance"
DECIMAL = re.compile(r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z")
INTEGER = re.compile(r"-?(?:0|[1-9][0-9]*)\Z")


def _date(text):
    if text is None or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text):
        raise ValueError("period_requires_ISO_date")
    return date.fromisoformat(text)


def _bounded_integer(text, minimum=-18, maximum=18):
    if not INTEGER.fullmatch(text):
        raise ValueError("invalid_integer")
    value = int(text)
    if not minimum <= value <= maximum:
        raise ValueError("integer_outside_supported_domain")
    return value


def parse_document(raw: bytes):
    if len(raw) > 1_000_000:
        raise ValueError("document_exceeds_offline_fixture_budget")
    text = raw.decode("utf-8-sig")
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("DTD_and_entities_unsupported")
    namespaces = {}
    for _, (prefix, uri) in ET.iterparse(StringIO(text), events=("start-ns",)):
        if prefix in namespaces and namespaces[prefix] != uri:
            raise ValueError("namespace_rebinding_unsupported")
        namespaces[prefix] = uri
    root = ET.fromstring(text)

    def qname(value):
        if value.count(":") != 1:
            raise ValueError("explicit_namespace_prefix_required")
        prefix, local = value.split(":")
        if prefix not in namespaces or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", local):
            raise ValueError("unknown_or_invalid_QName")
        return "{" + namespaces[prefix] + "}" + local

    ids = {}
    for node in root.iter():
        if node.get("id"):
            identity = node.get("id")
            if identity in ids:
                raise ValueError("duplicate_XML_id")
            ids[identity] = node

    def context(identity):
        node = ids.get(identity)
        if node is None or node.tag != f"{{{XBRLI}}}context":
            raise ValueError("missing_context")
        if len(node.findall(f"{{{XBRLI}}}entity")) != 1 or len(node.findall(f"{{{XBRLI}}}period")) != 1:
            raise ValueError("context_needs_one_entity_and_period")
        if len(node) != 2:
            raise ValueError("context_dimensions_or_scenario_unsupported")
        entity = node.find(f"{{{XBRLI}}}entity")
        if len(entity) != 1 or entity[0].tag != f"{{{XBRLI}}}identifier":
            raise ValueError("entity_segment_or_missing_identifier_unsupported")
        identifier = entity[0]
        if not identifier.get("scheme") or not (identifier.text or "").strip():
            raise ValueError("incomplete_entity_identifier")
        period = node.find(f"{{{XBRLI}}}period")
        if len(period) == 1 and period[0].tag == f"{{{XBRLI}}}instant":
            dates = {"instant": _date(period[0].text).isoformat()}
        elif len(period) == 2 and [e.tag for e in period] == [f"{{{XBRLI}}}startDate", f"{{{XBRLI}}}endDate"]:
            start, end = _date(period[0].text), _date(period[1].text)
            if start > end:
                raise ValueError("reversed_duration")
            dates = {"start": start.isoformat(), "end": end.isoformat()}
        else:
            raise ValueError("unknown_or_ambiguous_period")
        return {"entity_identifier": identifier.text.strip(), "entity_scheme": identifier.get("scheme"), "period": dates}

    def unit(identity):
        node = ids.get(identity)
        if node is None or node.tag != f"{{{XBRLI}}}unit":
            raise ValueError("missing_unit")
        if len(node) != 1 or node[0].tag != f"{{{XBRLI}}}measure":
            raise ValueError("compound_unit_unsupported")
        return qname((node[0].text or "").strip())

    facts, rejected = [], []
    for index, node in enumerate(root.iter(f"{{{IX}}}nonFraction")):
        identifier = node.get("id", f"anonymous-{index}")
        try:
            if node.get("format") is not None:
                raise ValueError("transformation_registry_not_implemented")
            if node.get("continuedAt") is not None or node.get("escape") is not None or len(node):
                raise ValueError("continuation_or_nested_content_unsupported")
            if node.get("{http://www.w3.org/2001/XMLSchema-instance}nil") is not None:
                raise ValueError("nil_fact_unsupported")
            lexical = (node.text or "").strip()
            if len(lexical) > 100 or not DECIMAL.fullmatch(lexical):
                raise ValueError("unsupported_decimal_lexeme")
            scale = _bounded_integer(node.get("scale", "0"))
            sign = node.get("sign")
            if sign not in (None, "-"):
                raise ValueError("unsupported_sign")
            decimals = node.get("decimals")
            if decimals is None:
                raise ValueError("missing_decimals")
            precision = None if decimals == "INF" else _bounded_integer(decimals)
            if node.get("precision") is not None:
                raise ValueError("precision_attribute_unsupported")
            expanded_name = qname(node.get("name", ""))
            fact_context = context(node.get("contextRef"))
            fact_unit = unit(node.get("unitRef"))
            with localcontext() as ctx:
                ctx.prec = 160
                value = Decimal(lexical).scaleb(scale)
                if sign == "-":
                    value = -value
                radius = Decimal(0) if precision is None else Decimal(5).scaleb(-precision - 1)
                facts.append({"id": identifier, "name": expanded_name, "value": str(value),
                              "unit": fact_unit, "scale": scale, "sign": sign, "decimals": decimals,
                              "declared_rounding_enclosure": [str(value - radius), str(value + radius)],
                              "context": fact_context})
        except (ValueError, TypeError) as error:
            rejected.append({"id": identifier, "reason": str(error)})
    unsupported = sum(1 for n in root.iter() if n.tag in (f"{{{IX}}}fraction", f"{{{IX}}}nonNumeric"))
    return {"scope": "synthetic/offline restricted XML nonFraction parser",
            "document_sha256": hashlib.sha256(raw).hexdigest(), "facts": facts, "rejections": rejected,
            "unsupported_other_fact_elements": unsupported,
            "status": "partial" if rejected or unsupported else "parsed" if facts else "abstain",
            "timestamp_certificate": None,
            "warning": "Decoded declared values are not evidence of correctness, publication time or XBRL conformance."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    result = parse_document(args.input.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
