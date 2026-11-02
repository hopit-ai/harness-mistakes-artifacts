"""The BFCL plan helpers the analysis needs (trimmed copy of the kit's ``slh.xp.bfcl.plan``):
content seals and the lesson-pool format. Building hand-off plans is not part of this release
(the built plans are in the private experiment kits, available on request)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

POOL_SCHEMA = "xp-bfcl-pool-v1"
POOL_MAX = 8                     # candidate lessons per pool entering F'


class PlanRefused(ValueError):
    pass


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def seal(body: dict[str, Any]) -> dict[str, Any]:
    body = {k: v for k, v in body.items() if k != "sha256"}
    return {**body, "sha256": sha_text(_canon(body))}


def check_seal(obj: dict[str, Any], what: str) -> dict[str, Any]:
    if seal(obj)["sha256"] != obj.get("sha256"):
        raise PlanRefused(f"{what}: content differs from its sha256")
    return obj


def make_pool(name: str, lessons: list[str], *, provenance: dict[str, Any]) -> dict[str, Any]:
    if name not in ("U", "S"):
        raise PlanRefused("pool is U (evidence) or S (no-evidence search)")
    if not 2 <= len(lessons) <= POOL_MAX:
        raise PlanRefused(f"a pool holds 2..{POOL_MAX} lessons, got {len(lessons)}")
    rows = [{"id": f"{name}{k + 1:02d}", "text": t, "sha256": sha_text(t), "intent": "bfcl",
             "tools": ["any"]} for k, t in enumerate(lessons)]
    return seal({"schema": POOL_SCHEMA, "pool": name, "lessons": rows,
                 "provenance": provenance})


def verify_pool(pool: dict[str, Any]) -> dict[str, Any]:
    if pool.get("schema") != POOL_SCHEMA:
        raise PlanRefused("pool: unknown schema")
    check_seal(pool, "pool")
    for les in pool["lessons"]:
        if sha_text(les["text"]) != les["sha256"]:
            raise PlanRefused(f"pool: {les['id']} text differs from its sha256")
    return pool
