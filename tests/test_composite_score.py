import math
import time

import pytest

from agentvectordb.collection import AgentMemoryCollection


def test_similarity_from_distance():
    assert AgentMemoryCollection._similarity_from_distance(0) == 1.0
    assert AgentMemoryCollection._similarity_from_distance(1) == 0.5
    assert 0 < AgentMemoryCollection._similarity_from_distance(10) < 0.1


def test_recency_score_half_life():
    now = 1_000_000.0
    half = 100.0
    assert AgentMemoryCollection._recency_score(now, now, half) == pytest.approx(1.0)
    assert AgentMemoryCollection._recency_score(now - half, now, half) == pytest.approx(0.5)
    assert AgentMemoryCollection._recency_score(now - 2 * half, now, half) == pytest.approx(0.25)


def test_rerank_prefers_importance_and_recency(monkeypatch):
    # Build a minimal fake collection instance without __init__
    col = object.__new__(AgentMemoryCollection)
    now = time.time()
    results = [
        {
            "id": "old_important",
            "_distance": 0.5,
            "importance_score": 1.0,
            "last_accessed_at": now - 10,
            "content": "a",
        },
        {
            "id": "close_trivial",
            "_distance": 0.01,
            "importance_score": 0.0,
            "last_accessed_at": now - 10 * 86400,
            "content": "b",
        },
    ]
    ranked = AgentMemoryCollection._rerank_composite(
        col,
        results,
        k=2,
        similarity_weight=0.2,
        recency_weight=0.3,
        importance_weight=0.5,
        recency_half_life_seconds=86400.0,
    )
    assert ranked[0]["id"] == "old_important"
    assert "composite_score" in ranked[0]
    assert ranked[0]["composite_score"] >= ranked[1]["composite_score"]


def test_query_composite_integration(sync_collection):
    now = time.time()
    sync_collection.add_batch(
        [
            {
                "content": "user likes dark mode UI",
                "type": "preference",
                "importance_score": 0.95,
                "created_at": now,
                "last_accessed_at": now,
            },
            {
                "content": "random note about weather tomorrow",
                "type": "note",
                "importance_score": 0.05,
                "created_at": now - 7 * 86400,
                "last_accessed_at": now - 7 * 86400,
            },
            {
                "content": "user prefers dark themes in apps",
                "type": "preference",
                "importance_score": 0.9,
                "created_at": now,
                "last_accessed_at": now,
            },
            {
                "content": "meeting notes from last spring",
                "type": "note",
                "importance_score": 0.1,
                "created_at": now - 30 * 86400,
                "last_accessed_at": now - 30 * 86400,
            },
            {
                "content": "dark mode accessibility tip",
                "type": "fact",
                "importance_score": 0.4,
                "created_at": now - 2 * 86400,
                "last_accessed_at": now - 2 * 86400,
            },
            {
                "content": "unrelated grocery list",
                "type": "note",
                "importance_score": 0.0,
                "created_at": now - 3 * 86400,
                "last_accessed_at": now - 3 * 86400,
            },
            {
                "content": "another filler memory alpha",
                "type": "note",
                "importance_score": 0.0,
                "created_at": now,
                "last_accessed_at": now,
            },
            {
                "content": "another filler memory beta",
                "type": "note",
                "importance_score": 0.0,
                "created_at": now,
                "last_accessed_at": now,
            },
        ]
    )
    results = sync_collection.query(
        query_text="dark mode preference",
        k=2,
        use_composite_score=True,
        similarity_weight=0.4,
        recency_weight=0.2,
        importance_weight=0.4,
        candidate_multiplier=4,
    )
    assert len(results) == 2
    assert all("composite_score" in r for r in results)
    # Top hits should be preference-like / dark-mode related
    top_types = {r.get("type") for r in results}
    assert "preference" in top_types or any("dark" in (r.get("content") or "").lower() for r in results)
