from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException

from datetime import datetime, timezone

from app.rag import build_index, generate_answer, load_index, load_kb_files, retrieve, should_refuse
from server.services.kb_store import get_kb_dir, get_kb_index_paths
from server.services.manifest import ensure_manifest, find_kb, save_manifest
from server.services.paths import BASE_DIR


def _relative_to_base(path: Path) -> str:
    try:
        return path.resolve().relative_to(BASE_DIR.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_index_for_kb(
    kb_id: str,
    embedding_model: str = "text-embedding-3-small",
    max_len: int = 800,
    overlap: int = 120,
    batch_size: int = 16,
) -> Dict:
    kb_dir = get_kb_dir(kb_id)
    if not kb_dir.exists():
        raise HTTPException(status_code=404, detail="KB not found")

    if not load_kb_files(str(kb_dir)):
        raise HTTPException(status_code=400, detail="KB has no valid files")

    index_dir, chunks_path = get_kb_index_paths(kb_id)
    stats = build_index(
        kb_dir=str(kb_dir),
        index_dir=str(index_dir),
        chunks_path=str(chunks_path),
        embedding_model=embedding_model,
        max_len=max_len,
        overlap=overlap,
        batch_size=batch_size,
    )

    manifest = ensure_manifest()
    kb = find_kb(manifest, kb_id)
    if kb is None:
        kb = {"kb_id": kb_id, "name": kb_id, "files": []}
        manifest.setdefault("kbs", []).append(kb)

    kb["updated_at"] = _now_iso()
    kb["index"] = {
        "built": True,
        "chunks": stats.get("chunks"),
        "index_dir": _relative_to_base(index_dir),
        "chunks_path": _relative_to_base(chunks_path),
        "updated_at": _now_iso(),
    }
    save_manifest(manifest)

    return stats


def _format_citations(retrieved, preview_len: int = 80) -> List[Dict]:
    citations: List[Dict] = []
    for r in retrieved:
        preview = r.chunk.text.replace("\n", " ").strip()[:preview_len]
        citations.append({
            "source_file": r.chunk.source_file,
            "chunk_id": r.chunk.chunk_id,
            "chunk_preview": preview,
            "score": r.score,
        })
    return citations


def ask_kb(
    kb_id: str,
    question: str,
    topk: int = 5,
    threshold: float = 0.35,
    embedding_model: str = "text-embedding-3-small",
    model: str = "gpt-4o-mini",
) -> Dict:
    index_dir, chunks_path = get_kb_index_paths(kb_id)

    if not chunks_path.exists() or not index_dir.exists():
        raise HTTPException(status_code=404, detail="Index not found")

    chunks, embeddings = load_index(
        index_dir=str(index_dir),
        chunks_path=str(chunks_path),
    )

    retrieved = retrieve(
        question=question,
        chunks=chunks,
        embeddings=embeddings,
        topk=topk,
        embedding_model=embedding_model,
    )

    top_score: Optional[float] = retrieved[0].score if retrieved else None

    if not retrieved:
        return {
            "question": question,
            "refused": True,
            "answer": "知识库未覆盖或无法确认。",
            "top_score": None,
            "threshold": threshold,
            "citations": [],
            "reason": "no_retrieval",
        }

    if should_refuse(retrieved, threshold=threshold):
        return {
            "question": question,
            "refused": True,
            "answer": "知识库未覆盖或无法确认。",
            "top_score": top_score,
            "threshold": threshold,
            "citations": [],
            "reason": "below_threshold",
        }

    answer = generate_answer(
        question=question,
        retrieved=retrieved,
        model=model,
    )

    return {
        "question": question,
        "refused": False,
        "answer": answer,
        "top_score": top_score,
        "threshold": threshold,
        "citations": _format_citations(retrieved),
    }
