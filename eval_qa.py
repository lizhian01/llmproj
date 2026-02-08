import argparse
import json
from pathlib import Path
from typing import Dict, List

from app.rag import (
    build_index,
    generate_answer,
    load_index,
    retrieve,
    should_refuse,
)


def load_eval_data(path: str) -> List[Dict]:
    items: List[Dict] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            items.append(json.loads(line))
    return items


def _normalize(text: str) -> str:
    return text.lower()


def eval_one(
    question: str,
    expected_keywords: List[str],
    expected_doc: str,
    should_refuse_flag: bool,
    chunks: Dict,
    embeddings: Dict,
    topk: int,
    threshold: float,
    embedding_model: str,
    answer_model: str,
) -> Dict:
    retrieved = retrieve(
        question=question,
        chunks=chunks,
        embeddings=embeddings,
        topk=topk,
        embedding_model=embedding_model,
    )
    refused = should_refuse(retrieved, threshold=threshold)

    evidence_text = "\n".join([r.chunk.text for r in retrieved])
    evidence_norm = _normalize(evidence_text)

    retrieval_hit = False
    if expected_doc:
        for r in retrieved:
            if r.chunk.source_file.endswith(expected_doc):
                retrieval_hit = True
                break
    if expected_keywords:
        for kw in expected_keywords:
            if _normalize(kw) in evidence_norm:
                retrieval_hit = True
                break

    answer = ""
    answer_keyword_hit = False
    if (not refused) and expected_keywords:
        answer = generate_answer(question=question, retrieved=retrieved, model=answer_model)
        ans_norm = _normalize(answer)
        for kw in expected_keywords:
            if _normalize(kw) in ans_norm:
                answer_keyword_hit = True
                break

    return {
        "question": question,
        "retrieval_hit": retrieval_hit,
        "answer_keyword_hit": answer_keyword_hit,
        "should_refuse": should_refuse_flag,
        "refused": refused,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG eval")
    parser.add_argument("--kb", required=True, help="KB directory")
    parser.add_argument("--eval-path", default="data/eval_qa.jsonl", help="Eval QA JSONL")
    parser.add_argument("--index-dir", default="data/index", help="Index dir")
    parser.add_argument("--chunks-path", default="data/chunks.json", help="Chunks JSON")
    parser.add_argument("--embedding-model", default="text-embedding-3-small", help="Embedding model")
    parser.add_argument("--answer-model", default="gpt-4o-mini", help="Answer model")
    parser.add_argument("--topk", type=int, default=5, help="Top-K")
    parser.add_argument("--threshold", type=float, default=0.35, help="Refusal threshold")
    parser.add_argument("--reindex", action="store_true", help="Force rebuild index")
    args = parser.parse_args()

    index_dir = Path(args.index_dir)
    chunks_path = Path(args.chunks_path)
    if args.reindex or (not index_dir.exists()) or (not chunks_path.exists()):
        build_index(
            kb_dir=args.kb,
            index_dir=args.index_dir,
            chunks_path=args.chunks_path,
            embedding_model=args.embedding_model,
        )

    chunks, embeddings = load_index(index_dir=args.index_dir, chunks_path=args.chunks_path)
    items = load_eval_data(args.eval_path)

    total = 0
    retrieval_total = 0
    retrieval_hit = 0
    answer_total = 0
    answer_hit = 0
    refusal_total = 0
    refusal_hit = 0

    for item in items:
        question = item.get("question", "")
        expected_keywords = item.get("expected_keywords", []) or []
        expected_doc = item.get("expected_doc", "") or ""
        should_refuse_flag = bool(item.get("should_refuse", False))

        result = eval_one(
            question=question,
            expected_keywords=expected_keywords,
            expected_doc=expected_doc,
            should_refuse_flag=should_refuse_flag,
            chunks=chunks,
            embeddings=embeddings,
            topk=args.topk,
            threshold=args.threshold,
            embedding_model=args.embedding_model,
            answer_model=args.answer_model,
        )

        total += 1
        if expected_keywords or expected_doc:
            retrieval_total += 1
            if result["retrieval_hit"]:
                retrieval_hit += 1

        if expected_keywords:
            answer_total += 1
            if result["answer_keyword_hit"]:
                answer_hit += 1

        if should_refuse_flag:
            refusal_total += 1
            if result["refused"]:
                refusal_hit += 1

    summary = {
        "total": total,
        "retrieval_hit_rate": (retrieval_hit / retrieval_total) if retrieval_total else 0.0,
        "answer_keyword_hit_rate": (answer_hit / answer_total) if answer_total else 0.0,
        "refusal_accuracy": (refusal_hit / refusal_total) if refusal_total else 0.0,
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
