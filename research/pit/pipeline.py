"""Deterministic historical pipeline reference; no model training or network.

The guarantee concerns the supplied knowledge-time log, not true public access.
Only canonical_history reads the full log. All later stages receive a cutoff-
bound historical state. Operational full-log fingerprints belong elsewhere.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
import re
import unicodedata


def canonical_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _integer(value, field: str) -> None:
    if type(value) is not int:
        raise ValueError(field + " must be an integer, not bool")


def normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\w+", normalized(text), flags=re.UNICODE))


@dataclass(frozen=True)
class Document:
    document_id: str
    event_id: str
    knowledge_time: int
    record_time: int
    content_sha256: str
    text: str
    source: str
    core: bool
    label: str | int | None
    metadata_json: str
    tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class HistoricalSnapshot:
    cutoff: int
    visible_history_bytes: bytes
    documents: tuple[Document, ...]


@dataclass(frozen=True)
class State:
    cutoff: int
    historical_hash: str
    documents: tuple[Document, ...]


@dataclass(frozen=True)
class FrozenConfig:
    allowed_sources: tuple[str, ...] = ("fixture", "synthetic-world")
    require_core: bool = False
    stopwords: tuple[str, ...] = ("a", "of", "the")
    lexical_threshold: tuple[int, int] = (4, 5)
    sample_limit: int = 1000
    development_fraction: tuple[int, int] = (1, 5)
    # Candidate order is frozen; it also resolves ties and the empty-dev case.
    tokenizer_candidates: tuple[tuple[int, int], ...] = ((4, 1), (8, 1), (8, 2))
    capacity_penalty: tuple[int, int] = (1, 1000)

    def validate(self) -> None:
        if type(self.require_core) is not bool:
            raise ValueError("require_core must be bool")
        for values in (self.allowed_sources, self.stopwords):
            if not isinstance(values, tuple) or not all(isinstance(x, str) and x for x in values) or len(set(values)) != len(values):
                raise ValueError("Source/stopword rules must be fixed distinct tuples")
        if any(normalized(x) != x for x in self.stopwords):
            raise ValueError("Stopwords must be externally normalized")
        _integer(self.sample_limit, "sample_limit")
        if self.sample_limit < 0:
            raise ValueError("sample_limit must be nonnegative")
        for name, value in [("lexical_threshold", self.lexical_threshold), ("development_fraction", self.development_fraction), ("capacity_penalty", self.capacity_penalty)]:
            if not isinstance(value, tuple) or len(value) != 2 or any(type(x) is not int for x in value) or value[1] <= 0:
                raise ValueError(name + " must be a rational integer pair")
        if not 0 < Fraction(*self.lexical_threshold) <= 1 or not 0 <= Fraction(*self.development_fraction) <= 1 or Fraction(*self.capacity_penalty) < 0:
            raise ValueError("Invalid fixed rational configuration")
        if type(self.tokenizer_candidates) is not tuple or not self.tokenizer_candidates or any(type(candidate) is not tuple for candidate in self.tokenizer_candidates) or len(set(self.tokenizer_candidates)) != len(self.tokenizer_candidates):
            raise ValueError("Candidates must be a nonempty fixed distinct sequence")
        for candidate in self.tokenizer_candidates:
            if not isinstance(candidate, tuple) or len(candidate) != 2 or any(type(x) is not int or x <= 0 for x in candidate):
                raise ValueError("Each tokenizer candidate is (positive capacity, positive min_frequency)")


def upsert(document_id: str, event_id: str, knowledge_time: int, text: str, *, record_time: int | None = None, source: str = "fixture", core: bool = False, label=None, metadata=None) -> dict:
    return {"document_id": document_id, "event_id": event_id, "knowledge_time": knowledge_time,
            "record_time": knowledge_time if record_time is None else record_time, "operation": "upsert",
            "payload": {"text": text, "content_sha256": sha256(text.encode("utf-8")), "source": source, "core": core, "label": label, "metadata": {} if metadata is None else metadata}}


def tombstone(document_id: str, event_id: str, knowledge_time: int, *, record_time: int | None = None) -> dict:
    return {"document_id": document_id, "event_id": event_id, "knowledge_time": knowledge_time,
            "record_time": knowledge_time if record_time is None else record_time, "operation": "tombstone", "payload": None}


def canonical_history(events, *, cutoff: int) -> HistoricalSnapshot:
    """Project by knowledge_time before body validation or latest-version choice.

    Domain: list/tuple of dictionaries with globally valid event/document IDs
    and integer knowledge_time. IDs need only be unique among visible events.
    Future body fields are opaque. At a visible time, full event schema, text
    hash, and the declared record_time<=knowledge_time convention are checked.
    None of those checks prove either time is truthful or the log is complete.
    """
    _integer(cutoff, "cutoff")
    if not isinstance(events, (list, tuple)):
        raise ValueError("Expected a finite event sequence")
    visible = []
    for event in events:
        if type(event) is not dict:
            raise ValueError("Every event needs a valid header dictionary")
        for field in ("event_id", "document_id"):
            if not isinstance(event.get(field), str) or not event[field]:
                raise ValueError("Every event needs a nonempty header identifier")
        _integer(event.get("knowledge_time"), "knowledge_time")
        if event["knowledge_time"] <= cutoff:
            visible.append(event)
    seen = set()
    checked = []
    latest = {}
    for event in sorted(visible, key=lambda e: (e["knowledge_time"], e["event_id"])):
        if set(event) != {"event_id", "document_id", "knowledge_time", "record_time", "operation", "payload"}:
            raise ValueError("Invalid visible event fields")
        if event["event_id"] in seen:
            raise ValueError("Visible event IDs must be unique")
        seen.add(event["event_id"])
        _integer(event["record_time"], "record_time")
        if event["record_time"] > event["knowledge_time"]:
            raise ValueError("Visible declared record_time cannot exceed knowledge_time")
        if event["operation"] == "tombstone":
            if event["payload"] is not None:
                raise ValueError("Visible tombstone has no payload")
            document = None
        elif event["operation"] == "upsert":
            payload = event["payload"]
            if not isinstance(payload, dict) or set(payload) != {"text", "content_sha256", "source", "core", "label", "metadata"}:
                raise ValueError("Invalid visible full-state payload")
            if not isinstance(payload["text"], str) or not isinstance(payload["source"], str) or not payload["source"] or type(payload["core"]) is not bool:
                raise ValueError("Invalid visible text/source/core")
            if payload["content_sha256"] != sha256(payload["text"].encode("utf-8")):
                raise ValueError("Visible content hash mismatch")
            if payload["label"] is not None and type(payload["label"]) not in {str, int}:
                raise ValueError("Visible label must be str/int/null")
            if not isinstance(payload["metadata"], dict):
                raise ValueError("Visible metadata must be a JSON object")
            metadata_json = canonical_bytes(payload["metadata"]).decode("utf-8")
            document = Document(event["document_id"], event["event_id"], event["knowledge_time"], event["record_time"], payload["content_sha256"], payload["text"], payload["source"], payload["core"], payload["label"], metadata_json)
        else:
            raise ValueError("Unknown visible operation")
        # Copy only validated visible events; never serialize any future payload.
        checked.append(json.loads(canonical_bytes(event)))
        latest[event["document_id"]] = document
    documents = tuple(latest[key] for key in sorted(latest) if latest[key] is not None)
    return HistoricalSnapshot(cutoff, canonical_bytes(checked), documents)


def _validate_snapshot(snapshot: HistoricalSnapshot, cutoff: int) -> None:
    _integer(cutoff, "cutoff")
    if type(snapshot) is not HistoricalSnapshot:
        raise ValueError("Expected a HistoricalSnapshot")
    _integer(snapshot.cutoff, "snapshot cutoff")
    if snapshot.cutoff != cutoff:
        raise ValueError("Snapshot/caller cutoff mismatch")
    if type(snapshot.visible_history_bytes) is not bytes or type(snapshot.documents) is not tuple:
        raise ValueError("Snapshot storage must be immutable bytes and a document tuple")
    for doc in snapshot.documents:
        _validate_document_types(doc)
    rebuilt = canonical_history(json.loads(snapshot.visible_history_bytes), cutoff=cutoff)
    # Python dataclass equality equates False/0 and True/1. It is not a
    # canonical JSON consistency check; compare exact serialized field types.
    if rebuilt.visible_history_bytes != snapshot.visible_history_bytes or canonical_bytes([asdict(doc) for doc in rebuilt.documents]) != canonical_bytes([asdict(doc) for doc in snapshot.documents]):
        raise ValueError("Snapshot is not a consistent canonical historical projection")


def _validate_document_types(doc: Document) -> None:
    if type(doc) is not Document:
        raise ValueError("Expected an immutable Document")
    for field in ("document_id", "event_id", "content_sha256", "text", "source", "metadata_json"):
        if type(getattr(doc, field)) is not str:
            raise ValueError("Invalid document string field")
    _integer(doc.knowledge_time, "document knowledge_time")
    _integer(doc.record_time, "document record_time")
    if type(doc.core) is not bool or (doc.label is not None and type(doc.label) not in {str, int}):
        raise ValueError("Invalid document core/label type")
    if type(doc.tokens) is not tuple or any(type(token) is not str for token in doc.tokens):
        raise ValueError("Document tokens must be an immutable string tuple")


def _check_state(state: State, cutoff: int) -> None:
    _integer(cutoff, "cutoff")
    if type(state) is not State:
        raise ValueError("Expected a State")
    _integer(state.cutoff, "state cutoff")
    if type(state.documents) is not tuple or type(state.historical_hash) is not str:
        raise ValueError("Invalid state storage types")
    for doc in state.documents:
        _validate_document_types(doc)
    if state.cutoff != cutoff or any(doc.knowledge_time > cutoff for doc in state.documents):
        raise ValueError("Stage/caller cutoff mismatch or future document")


def _stage_payload(state: State, details=None) -> dict:
    return {"cutoff": state.cutoff, "historical_hash": state.historical_hash, "documents": [asdict(doc) for doc in state.documents], "details": {} if details is None else details}


def filter_documents(snapshot: HistoricalSnapshot, config: FrozenConfig, *, cutoff: int) -> State:
    _validate_snapshot(snapshot, cutoff)
    config.validate()
    from dataclasses import replace
    docs = []
    for doc in snapshot.documents:
        if doc.source not in config.allowed_sources or (config.require_core and not doc.core):
            continue
        docs.append(replace(doc, tokens=tuple(token for token in tokens(doc.text) if token not in config.stopwords)))
    return State(cutoff, sha256(snapshot.visible_history_bytes), tuple(docs))


def deduplicate(state: State, config: FrozenConfig, *, cutoff: int) -> tuple[State, dict]:
    _check_state(state, cutoff)
    config.validate()
    docs = state.documents
    parent = list(range(len(docs)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)
    sets = [set(doc.tokens) for doc in docs]
    numerator, denominator = config.lexical_threshold
    edges = []
    for i in range(len(docs)):
        for j in range(i):
            exact = normalized(docs[i].text) == normalized(docs[j].text)
            lexical = bool(sets[i] and sets[j]) and denominator * len(sets[i] & sets[j]) >= numerator * len(sets[i] | sets[j])
            if exact or lexical:
                union(i, j)
                edges.append([docs[j].document_id, docs[i].document_id])
    groups = defaultdict(list)
    for i, doc in enumerate(docs):
        groups[find(i)].append(doc)
    representatives, detail = [], []
    for members in groups.values():
        representative = min(members, key=lambda d: (d.knowledge_time, d.document_id, d.event_id))
        representatives.append(representative)
        detail.append({"representative": representative.document_id, "members": sorted(d.document_id for d in members)})
    representatives.sort(key=lambda d: d.document_id)
    detail.sort(key=lambda d: d["representative"])
    return State(cutoff, state.historical_hash, tuple(representatives)), {"components": detail, "exact_or_lexical_edges": edges}


def _rank(namespace: str, seed: int, document_id: str) -> int:
    return int(sha256(canonical_bytes([namespace, seed, document_id])), 16)


def sample_documents(state: State, config: FrozenConfig, *, cutoff: int, seed: int) -> State:
    _check_state(state, cutoff)
    _integer(seed, "seed")
    config.validate()
    selected = sorted(state.documents, key=lambda d: (_rank("sample", seed, d.document_id), d.document_id))[:config.sample_limit]
    return State(cutoff, state.historical_hash, tuple(sorted(selected, key=lambda d: d.document_id)))


def split_documents(state: State, config: FrozenConfig, *, cutoff: int, seed: int) -> tuple[State, State]:
    _check_state(state, cutoff)
    _integer(seed, "seed")
    config.validate()
    numerator, denominator = config.development_fraction
    train, development = [], []
    for doc in state.documents:
        is_development = _rank("development", seed, doc.document_id) * denominator < numerator * (1 << 256)
        (development if is_development else train).append(doc)
    return State(cutoff, state.historical_hash, tuple(train)), State(cutoff, state.historical_hash, tuple(development))


def fit_tokenizer(train: State, candidate: tuple[int, int], *, cutoff: int) -> dict:
    _check_state(train, cutoff)
    if not isinstance(candidate, tuple) or len(candidate) != 2 or any(type(x) is not int or x <= 0 for x in candidate):
        raise ValueError("Invalid fixed tokenizer candidate")
    capacity, minimum_frequency = candidate
    counts = Counter(token for doc in train.documents for token in doc.tokens)
    eligible = sorted((token for token in counts if counts[token] >= minimum_frequency), key=lambda token: (-counts[token], token))
    vocabulary = eligible[:capacity]
    return {"cutoff": cutoff, "historical_hash": train.historical_hash, "capacity": capacity, "minimum_frequency": minimum_frequency,
            "train_document_ids": [doc.document_id for doc in train.documents], "train_token_count": sum(counts.values()),
            "reserved_ids": {"unknown": 0, "padding": 1}, "vocabulary": [{"token": token, "id": i+2, "train_count": counts[token]} for i, token in enumerate(vocabulary)]}


def select_tokenizer(train: State, development: State, config: FrozenConfig, *, cutoff: int) -> tuple[dict, dict]:
    _check_state(train, cutoff)
    _check_state(development, cutoff)
    config.validate()
    if train.historical_hash != development.historical_hash or set(d.document_id for d in train.documents) & set(d.document_id for d in development.documents):
        raise ValueError("Train/development provenance differs or documents overlap")
    dev_tokens = [token for doc in development.documents for token in doc.tokens]
    candidates, scores, fitted = [], [], []
    for index, candidate in enumerate(config.tokenizer_candidates):
        tokenizer = fit_tokenizer(train, candidate, cutoff=cutoff)
        vocabulary = {entry["token"] for entry in tokenizer["vocabulary"]}
        unknown = sum(token not in vocabulary for token in dev_tokens)
        oov = Fraction(unknown, len(dev_tokens)) if dev_tokens else Fraction(0)
        penalty = Fraction(*config.capacity_penalty) * candidate[0]
        objective = oov + penalty
        candidates.append({"index": index, "candidate": list(candidate), "development_token_count": len(dev_tokens), "unknown_count": unknown,
                           "oov": [oov.numerator, oov.denominator], "capacity_cost": [penalty.numerator, penalty.denominator], "objective": [objective.numerator, objective.denominator], "tokenizer": tokenizer})
        scores.append(objective)
        fitted.append(tokenizer)
    selected_index = min(range(len(scores)), key=lambda i: (scores[i], i)) if dev_tokens else 0
    selection = {"cutoff": cutoff, "historical_hash": train.historical_hash, "candidates": candidates, "selected_index": selected_index,
                 "reason": "minimum_exact_dev_objective_then_frozen_order" if dev_tokens else "no_development_tokens_use_frozen_first_candidate",
                 "development_document_ids": [doc.document_id for doc in development.documents]}
    return fitted[selected_index], selection


def run_pipeline(snapshot: HistoricalSnapshot, *, cutoff: int, config: FrozenConfig, seed: int) -> dict[str, bytes]:
    _validate_snapshot(snapshot, cutoff)
    config.validate()
    _integer(seed, "seed")
    artifacts = {
        "configuration.json": canonical_bytes({"algorithm": "pit-reference-v1", "cutoff": cutoff, "config": asdict(config), "seed": seed}),
        "history.json": snapshot.visible_history_bytes,
        "snapshot.json": canonical_bytes({"cutoff": cutoff, "documents": [asdict(doc) for doc in snapshot.documents]}),
    }
    filtered = filter_documents(snapshot, config, cutoff=cutoff)
    artifacts["filter.json"] = canonical_bytes(_stage_payload(filtered))
    deduped, dedupe_details = deduplicate(filtered, config, cutoff=cutoff)
    artifacts["deduplicate.json"] = canonical_bytes(_stage_payload(deduped, dedupe_details))
    sampled = sample_documents(deduped, config, cutoff=cutoff, seed=seed)
    artifacts["sample.json"] = canonical_bytes(_stage_payload(sampled))
    train, development = split_documents(sampled, config, cutoff=cutoff, seed=seed)
    artifacts["split.json"] = canonical_bytes({"cutoff": cutoff, "historical_hash": sampled.historical_hash, "train": _stage_payload(train), "development": _stage_payload(development)})
    tokenizer, selection = select_tokenizer(train, development, config, cutoff=cutoff)
    artifacts["tokenizer_candidates.json"] = canonical_bytes(selection)
    artifacts["selected_tokenizer.json"] = canonical_bytes(tokenizer)
    artifacts["artifact_hashes.json"] = canonical_bytes({name: sha256(value) for name, value in sorted(artifacts.items())})
    return artifacts


def build_at_cutoff(events, *, cutoff: int, config: FrozenConfig = FrozenConfig(), seed: int = 130) -> dict[str, bytes]:
    return run_pipeline(canonical_history(events, cutoff=cutoff), cutoff=cutoff, config=config, seed=seed)


def world_adapter(rows) -> list[dict]:
    """Only id/recorded_time/text are read; no latent availability or truth.

    Setting knowledge_time=recorded_time is a declared synthetic convention,
    not detection of corrupted record times or certification of real history.
    """
    return [upsert(row["id"], "world:" + row["id"], row["recorded_time"], row["text"], source="synthetic-world", core=False) for row in rows]


def naive_full_log_vocabulary_then_filter(events, cutoff: int) -> tuple[str, ...]:
    """Intentionally wrong counterexample; never called by the real pipeline."""
    vocabulary = sorted({token for event in events if event["operation"] == "upsert" for token in tokens(event["payload"]["text"])})
    return tuple(vocabulary)


def naive_full_log_latest_duplicate_then_filter(events, cutoff: int) -> tuple[str, ...]:
    """Wrong: future duplicate can erase an old representative before filtering."""
    latest = {}
    for event in sorted(events, key=lambda e: (e["knowledge_time"], e["event_id"])):
        if event["operation"] == "upsert":
            latest[normalized(event["payload"]["text"])] = event
    return tuple(sorted(event["document_id"] for event in latest.values() if event["knowledge_time"] <= cutoff))


def naive_full_log_size_selects_historical(events, cutoff: int) -> str | None:
    """Wrong: all selected documents are old, but selection uses future length."""
    historical = sorted(event["document_id"] for event in events if event["knowledge_time"] <= cutoff and event["operation"] == "upsert")
    return historical[len(events) % len(historical)] if historical else None
