"""Task schema, loading and validation for JP-Bench."""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml

CATEGORIES = {"lookup", "extract", "search", "form_fill", "download"}
DIFFICULTIES = {"easy", "medium", "hard"}
_ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_JA_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
TAGS = {"corporate", "tax", "legal", "subsidy", "labor", "needs_login", "multi_page", "japanese_era", "full_width_input"}
REVIEW_STATUSES = {"draft", "reviewed", "published"}
OPTIONAL_KEYS = {"version", "deprecated", "replaced_by", "tags", "review_status", "created", "updated", "owner", "snapshot_date", "source_documents", "max_steps", "timeout_seconds", "allowed_domains", "auth_method"}
AUTH_METHODS = {"none", "idpw", "gbizid"}
SUPPORTED_VERSION = 1
PERSONAL_PHONE_RE = re.compile(r"0[789]0-?\d{4}-?\d{4}")
SUCCESS_TYPES = {"field_match", "numeric_tolerance", "set_overlap", "reached_state", "boolean", "date_range", "enum", "multi_answer", "abstain", "url_match", "article_match", "law_number_match", "postal_code_match", "phone_match", "amount_yen_match"}
TOLERANCE_MODES = {"relative", "absolute"}

REQUIRED_KEYS = {
    "id",
    "title_ja",
    "title_en",
    "portal",
    "category",
    "difficulty",
    "instructions_ja",
    "instructions_en",
    "inputs",
    "success",
    "safety",
    "gold_source",
}


class TaskError(ValueError):
    """Raised when a task file does not satisfy the schema."""


@dataclass(frozen=True)
class Portal:
    name_ja: str
    url: str
    operator: str


@dataclass(frozen=True)
class Success:
    type: str
    fields: list[str] = field(default_factory=list)
    tolerance: float = 0.0
    min_overlap: float = 1.0
    state: str | None = None
    labels: dict[str, str] = field(default_factory=dict)
    partial_credit: bool = True
    tolerance_mode: str = "relative"


@dataclass(frozen=True)
class Task:
    id: str
    title_ja: str
    title_en: str
    portal: Portal
    category: str
    difficulty: str
    instructions_ja: str
    instructions_en: str
    inputs: dict[str, Any]
    success: Success
    stop_before_submit: bool
    auth_required: bool
    gold_source: str
    path: Path | None = None
    tags: tuple[str, ...] = ()
    review_status: str = "draft"
    created: str = ""
    updated: str = ""
    owner: str = ""
    snapshot_date: str = ""
    source_documents: tuple[str, ...] = ()
    version: int = 1
    deprecated: bool = False
    replaced_by: str = ""
    max_steps: int = 0
    timeout_seconds: int = 0
    allowed_domains: tuple[str, ...] = ()
    auth_method: str = ""

    @property
    def requires_login(self) -> bool:
        return self.auth_required

    @property
    def is_form_fill(self) -> bool:
        return self.category == "form_fill"

    @property
    def is_read_only(self) -> bool:
        return self.category in {"lookup", "extract", "search"}


def _require(cond: bool, task_id: str, msg: str) -> None:
    if not cond:
        raise TaskError(f"[{task_id}] {msg}")


def _optional_tags(raw: dict[str, Any], task_id: str) -> list[str]:
    tags = list(raw.get("tags") or [])
    for tag in tags:
        _require(tag in TAGS, task_id, f"unknown tag {tag!r}")
    _require(len(set(tags)) == len(tags), task_id, "tags must be unique")
    return [str(t) for t in tags]


def _optional_status(raw: dict[str, Any], task_id: str) -> str:
    status = str(raw.get("review_status", "draft"))
    _require(status in REVIEW_STATUSES, task_id, f"review_status must be one of {sorted(REVIEW_STATUSES)}")
    return status


def _optional_date(raw: dict[str, Any], key: str, task_id: str) -> str:
    if key not in raw or raw[key] is None:
        return ""
    try:
        return datetime.date.fromisoformat(str(raw[key])).isoformat()
    except ValueError as exc:
        raise TaskError(f"[{task_id}] {key} must be an ISO 8601 date") from exc


def _optional_urls(raw: dict[str, Any], task_id: str) -> list[str]:
    urls = list(raw.get("source_documents") or [])
    for url in urls:
        _require(str(url).startswith("https://"), task_id, "source_documents must be https URLs")
    return [str(u) for u in urls]


def parse_task(raw: dict[str, Any], path: Path | None = None) -> Task:
    task_id = str(raw.get("id", path.stem if path else "?"))
    _require(bool(_ID_RE.fullmatch(task_id)), task_id, "id must be lowercase kebab-case")
    unknown = set(raw) - REQUIRED_KEYS - OPTIONAL_KEYS
    _require(not unknown, task_id, f"unknown keys: {sorted(unknown)}")
    missing = REQUIRED_KEYS - raw.keys()
    _require(not missing, task_id, f"missing keys: {sorted(missing)}")

    if path is not None:
        _require(path.stem == task_id, task_id, f"file name must be {task_id}.yaml")

    portal = raw["portal"]
    _require(isinstance(portal, dict), task_id, "portal must be a mapping")
    url = str(portal.get("url", ""))
    _require(url.startswith("https://"), task_id, "portal.url must be https")
    _require(bool(_JA_RE.search(str(raw["title_ja"]))), task_id, "title_ja must contain Japanese text")
    _require(bool(_JA_RE.search(str(raw["instructions_ja"]))), task_id, "instructions_ja must contain Japanese text")
    _require(not _JA_RE.search(str(raw["instructions_en"])), task_id, "instructions_en must not contain Japanese text")
    _require(bool(str(raw["gold_source"]).strip()), task_id, "gold_source must be non-empty")

    _require(raw["category"] in CATEGORIES, task_id, f"category must be one of {sorted(CATEGORIES)}")
    _require(raw["difficulty"] in DIFFICULTIES, task_id, f"difficulty must be one of {sorted(DIFFICULTIES)}")

    succ = raw["success"]
    _require(isinstance(succ, dict), task_id, "success must be a mapping")
    stype = succ.get("type")
    _require(stype in SUCCESS_TYPES, task_id, f"success.type must be one of {sorted(SUCCESS_TYPES)}")
    if stype in {"field_match", "numeric_tolerance", "set_overlap", "boolean", "date_range", "enum", "multi_answer", "abstain", "url_match", "article_match", "law_number_match", "postal_code_match", "phone_match", "amount_yen_match"}:
        _require(bool(succ.get("fields")), task_id, f"success.fields required for {stype}")
    if stype == "reached_state":
        _require(bool(succ.get("state")), task_id, "success.state required for reached_state")
    fields = list(succ.get("fields", []))
    _require(len(set(fields)) == len(fields), task_id, "success.fields must be unique")
    overlap = float(succ.get("min_overlap", 1.0))
    _require(0.0 <= overlap <= 1.0, task_id, "success.min_overlap must be within 0-1")
    _require(float(succ.get("tolerance", 0.0)) >= 0.0, task_id, "success.tolerance must not be negative")
    _require(float(succ.get("tolerance", 0.0)) <= 0.5, task_id, "success.tolerance must be at most 0.5")
    _require(str(succ.get("tolerance_mode", "relative")) in TOLERANCE_MODES, task_id, "success.tolerance_mode must be relative or absolute")
    _require("tolerance" not in succ or stype == "numeric_tolerance", task_id, "success.tolerance only applies to numeric_tolerance")
    _require("state" not in succ or stype == "reached_state", task_id, "success.state only applies to reached_state")

    safety = raw["safety"]
    _require(isinstance(safety, dict), task_id, "safety must be a mapping")
    stop = bool(safety.get("stop_before_submit", False))
    if raw["category"] == "form_fill":
        _require(stop, task_id, "form_fill tasks must set safety.stop_before_submit: true")

    if raw["category"] == "form_fill":
        _require(stype == "reached_state", task_id, "form_fill tasks must use the reached_state success rule")
    if "max_steps" in raw:
        _require(isinstance(raw["max_steps"], int) and 1 <= raw["max_steps"] <= 200, task_id, "max_steps must be an integer from 1 to 200")
    if "timeout_seconds" in raw:
        _require(isinstance(raw["timeout_seconds"], int) and 1 <= raw["timeout_seconds"] <= 1800, task_id, "timeout_seconds must be an integer from 1 to 1800")
    allowed = [str(d) for d in (raw.get("allowed_domains") or [])]
    for domain in allowed:
        _require("/" not in domain and "://" not in domain and bool(domain), task_id, "allowed_domains entries must be bare host names")
    if allowed:
        host = urlsplit(url).hostname or ""
        _require(host in allowed, task_id, "allowed_domains must include the portal host")
    for key, value in raw["inputs"].items() if isinstance(raw["inputs"], dict) else []:
        _require(isinstance(value, (str, int, float, bool, list)), task_id, f"inputs.{key} must be a scalar or list")
        _require(not (isinstance(value, str) and PERSONAL_PHONE_RE.search(value)), task_id, f"inputs.{key} looks like a real mobile phone number")
    auth_method = str(raw.get("auth_method", ""))
    if auth_method:
        _require(auth_method in AUTH_METHODS, task_id, f"auth_method must be one of {sorted(AUTH_METHODS)}")
        _require(bool(safety.get("auth_required", False)), task_id, "auth_method requires safety.auth_required: true")
    if bool(safety.get("auth_required", False)):
        _require(bool(auth_method), task_id, "auth_required tasks must declare auth_method")
    version = int(raw.get("version", 1))
    _require(1 <= version <= SUPPORTED_VERSION, task_id, f"version {version} is not supported (max {SUPPORTED_VERSION})")
    deprecated = bool(raw.get("deprecated", False))
    replaced_by = str(raw.get("replaced_by", ""))
    _require(not deprecated or bool(replaced_by), task_id, "deprecated tasks must name replaced_by")
    created = _optional_date(raw, "created", task_id)
    updated = _optional_date(raw, "updated", task_id)
    _require(not (created and updated) or updated >= created, task_id, "updated must not be earlier than created")
    return Task(
        id=task_id,
        title_ja=raw["title_ja"],
        title_en=raw["title_en"],
        portal=Portal(name_ja=portal["name_ja"], url=url, operator=portal["operator"]),
        category=raw["category"],
        difficulty=raw["difficulty"],
        instructions_ja=raw["instructions_ja"].strip(),
        instructions_en=raw["instructions_en"].strip(),
        inputs=dict(raw["inputs"] or {}),
        success=Success(
            type=stype,
            fields=list(succ.get("fields", [])),
            tolerance=float(succ.get("tolerance", 0.0)),
            min_overlap=float(succ.get("min_overlap", 1.0)),
            state=succ.get("state"),
            labels={str(k): str(v) for k, v in dict(succ.get("labels") or {}).items()},
            partial_credit=bool(succ.get("partial_credit", True)),
            tolerance_mode=str(succ.get("tolerance_mode", "relative")),
        ),
        stop_before_submit=stop,
        auth_required=bool(safety.get("auth_required", False)),
        gold_source=str(raw.get("gold_source", "")),
        path=path,
        tags=tuple(sorted(_optional_tags(raw, task_id))),
        review_status=_optional_status(raw, task_id),
        created=created,
        updated=updated,
        owner=str(raw.get("owner", "")),
        snapshot_date=_optional_date(raw, "snapshot_date", task_id),
        source_documents=tuple(_optional_urls(raw, task_id)),
        version=version,
        deprecated=deprecated,
        replaced_by=replaced_by,
        max_steps=int(raw.get("max_steps", 0)),
        timeout_seconds=int(raw.get("timeout_seconds", 0)),
        allowed_domains=tuple(allowed),
        auth_method=auth_method,
    )


def load_tasks(directory: Path | str) -> list[Task]:
    directory = Path(directory)
    root = directory.resolve()
    tasks: list[Task] = []
    seen: dict[str, str] = {}
    titles_en: dict[str, str] = {}
    titles_ja: dict[str, str] = {}
    for path in sorted(directory.glob("*.yaml")):
        if path.name.startswith(("_", ".")):
            continue
        if path.is_symlink() and not path.resolve().is_relative_to(root):
            raise TaskError(f"{path.name}: symlink points outside the task directory")
        text = path.read_text(encoding="utf-8")
        if text.startswith("\ufeff"):
            raise TaskError(f"{path.name}: remove the UTF-8 byte order mark")
        try:
            raw = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            where = f" at line {mark.line + 1}" if mark is not None else ""
            raise TaskError(f"{path.name}: YAML parse error{where}") from exc
        if not isinstance(raw, dict):
            raise TaskError(f"{path.name}: top level must be a mapping")
        task = parse_task(raw, path)
        _require(task.id not in seen, task.id, "duplicate task id")
        _require(task.title_en not in titles_en, task.id, f"title_en duplicates {titles_en.get(task.title_en)}")
        _require(task.title_ja not in titles_ja, task.id, f"title_ja duplicates {titles_ja.get(task.title_ja)}")
        seen[task.id] = path.name
        titles_en[task.title_en] = task.id
        titles_ja[task.title_ja] = task.id
        tasks.append(task)
    _check_replacements(tasks)
    return tasks


def _check_replacements(tasks: list[Task]) -> None:
    by_id = {t.id: t for t in tasks}
    for task in tasks:
        if not task.replaced_by:
            continue
        _require(task.replaced_by in by_id, task.id, f"replaced_by {task.replaced_by!r} is not a known task")
        seen = {task.id}
        current = task.replaced_by
        while current in by_id and by_id[current].replaced_by:
            _require(current not in seen, task.id, "replaced_by forms a cycle")
            seen.add(current)
            current = by_id[current].replaced_by
