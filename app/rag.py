import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from client import get_client
from app.prompt_loader import load_prompt, render_prompt



@dataclass
class Chunk:
    chunk_id: str
    source_file: str
    section_id: int
    text: str


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_kb_files(kb_dir: str) -> List[Tuple[Path, str]]:
    root = Path(kb_dir)
    if not root.exists():
        raise FileNotFoundError(f"KB dir not found: {kb_dir}")

    files: List[Tuple[Path, str]] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".md", ".txt"}:
            continue
        files.append((p, _read_text(p)))
    return files


def split_sections(text: str) -> List[str]:
    lines = text.splitlines()
    sections: List[str] = []
    buf: List[str] = []

    def flush() -> None:
        nonlocal buf
        if not buf:
            return
        s = "\n".join(buf).strip()
        if s:
            sections.append(s)
        buf = []

    for line in lines:
        if not line.strip():
            flush()
            continue
        if line.lstrip().startswith("#"):
            flush()
            buf.append(line)
            continue
        buf.append(line)

    flush()
    return sections


def split_with_overlap(text: str, max_len: int, overlap: int) -> List[str]:
    if max_len <= 0:
        raise ValueError("max_len must be positive")
    if overlap < 0:
        overlap = 0
    if overlap >= max_len:
        overlap = max_len - 1

    out: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_len, n)
        chunk = text[start:end].strip()
        if chunk:
            out.append(chunk)
        if end >= n:
            break
        start = end - overlap
    return out


def build_chunks(kb_dir: str, max_len: int, overlap: int) -> List[Chunk]:
    chunks: List[Chunk] = []
    files = load_kb_files(kb_dir)

    idx = 0
    for path, text in files:
        rel = path.relative_to(kb_dir).as_posix()
        sections = split_sections(text)
        for section_id, section in enumerate(sections):
            pieces = split_with_overlap(section, max_len=max_len, overlap=overlap)
            for piece in pieces:
                chunk_id = f"chunk_{idx:06d}"
                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    source_file=rel,
                    section_id=section_id,
                    text=piece,
                ))
                idx += 1
    return chunks


def _embed_texts(texts: List[str], model: str) -> List[List[float]]:
    client = get_client()
    resp = client.embeddings.create(model=model, input=texts)
    # Keep input order
    return [item.embedding for item in resp.data]


def build_index(
    kb_dir: str,
    index_dir: str = "data/index",
    chunks_path: str = "data/chunks.json",
    embedding_model: str = "text-embedding-3-small",
    max_len: int = 800,
    overlap: int = 120,
    batch_size: int = 16,
) -> Dict[str, int]:
    chunks = build_chunks(kb_dir=kb_dir, max_len=max_len, overlap=overlap)

    index_path = Path(index_dir)
    index_path.mkdir(parents=True, exist_ok=True)

    chunks_out = [
        {
            "chunk_id": c.chunk_id,
            "source_file": c.source_file,
            "section_id": c.section_id,
            "text": c.text,
        }
        for c in chunks
    ]
    Path(chunks_path).write_text(
        json.dumps(chunks_out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    emb_path = index_path / "embeddings.jsonl"
    with emb_path.open("w", encoding="utf-8") as f:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c.text for c in batch]
            embeddings = _embed_texts(texts, model=embedding_model)
            for c, emb in zip(batch, embeddings):
                row = {"chunk_id": c.chunk_id, "embedding": emb}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {"chunks": len(chunks)}


def load_index(
    index_dir: str = "data/index",
    chunks_path: str = "data/chunks.json",
) -> Tuple[Dict[str, Chunk], Dict[str, List[float]]]:
    chunks_text = Path(chunks_path).read_text(encoding="utf-8")
    chunk_rows = json.loads(chunks_text)
    chunks: Dict[str, Chunk] = {}
    for row in chunk_rows:
        c = Chunk(
            chunk_id=row["chunk_id"],
            source_file=row["source_file"],
            section_id=row.get("section_id", 0),
            text=row["text"],
        )
        chunks[c.chunk_id] = c

    emb_path = Path(index_dir) / "embeddings.jsonl"
    embeddings: Dict[str, List[float]] = {}
    with emb_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            embeddings[row["chunk_id"]] = row["embedding"]

    return chunks, embeddings


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    denom = math.sqrt(norm_a) * math.sqrt(norm_b)
    if denom == 0.0:
        return 0.0
    return dot / denom


def retrieve(
    question: str,
    chunks: Dict[str, Chunk],
    embeddings: Dict[str, List[float]],
    topk: int,
    embedding_model: str,
) -> List[RetrievedChunk]:
    q_emb = _embed_texts([question], model=embedding_model)[0]

    scored: List[RetrievedChunk] = []
    for chunk_id, emb in embeddings.items():
        c = chunks.get(chunk_id)
        if not c:
            continue
        score = _cosine_similarity(q_emb, emb)
        scored.append(RetrievedChunk(chunk=c, score=score))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:max(1, topk)]


def should_refuse(retrieved: List[RetrievedChunk], threshold: float) -> bool:
    if not retrieved:
        return True
    return retrieved[0].score < threshold


def format_citations(retrieved: List[RetrievedChunk], preview_len: int = 80) -> List[Dict[str, str]]:
    citations = []
    for r in retrieved:
        preview = r.chunk.text.replace("\n", " ").strip()[:preview_len]
        citations.append({
            "source_file": r.chunk.source_file,
            "chunk_id": r.chunk.chunk_id,
            "chunk_preview": preview,
        })
    return citations


def build_evidence_block(retrieved: List[RetrievedChunk]) -> str:
    lines: List[str] = []
    for r in retrieved:
        lines.append("---")
        lines.append(f"chunk_id: {r.chunk.chunk_id}")
        lines.append(f"source_file: {r.chunk.source_file}")
        lines.append(r.chunk.text)
    return "\n".join(lines)


def generate_answer(question: str, retrieved: List[RetrievedChunk], model: str) -> str:
    tpl = load_prompt("rag_answer.md")
    evidence = build_evidence_block(retrieved)
    prompt = render_prompt(tpl, QUESTION=question, EVIDENCE=evidence)

    client = get_client()
    resp = client.responses.create(
        model=model,
        input=prompt,
    )
    return (resp.output_text or "").strip()
