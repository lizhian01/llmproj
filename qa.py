import argparse
import json
from pathlib import Path

from app.rag import (
    build_index,
    format_citations,
    generate_answer,
    load_index,
    retrieve,
    should_refuse,
)


def _refusal_payload(question: str) -> dict:
    return {
        "question": question,
        "refused": True,
        "answer": "知识库未覆盖或无法确认。",
        "need_more_info": [
            "请提供更具体的关键词或术语",
            "请说明相关文档名称或章节",
            "请提供时间范围、版本或背景",
        ],
        "citations": [],
    }


def cmd_index(args: argparse.Namespace) -> None:
    stats = build_index(
        kb_dir=args.kb,
        index_dir=args.index_dir,
        chunks_path=args.chunks_path,
        embedding_model=args.embedding_model,
        max_len=args.max_len,
        overlap=args.overlap,
        batch_size=args.batch_size,
    )
    print(json.dumps({"ok": True, "stats": stats}, ensure_ascii=False, indent=2))


def cmd_ask(args: argparse.Namespace) -> None:
    chunks, embeddings = load_index(
        index_dir=args.index_dir,
        chunks_path=args.chunks_path,
    )
    retrieved = retrieve(
        question=args.question,
        chunks=chunks,
        embeddings=embeddings,
        topk=args.topk,
        embedding_model=args.embedding_model,
    )

    if should_refuse(retrieved, threshold=args.threshold):
        print(json.dumps(_refusal_payload(args.question), ensure_ascii=False, indent=2))
        return

    answer = generate_answer(
        question=args.question,
        retrieved=retrieved,
        model=args.model,
    )

    result = {
        "question": args.question,
        "refused": False,
        "answer": answer,
        "top_score": retrieved[0].score if retrieved else None,
        "threshold": args.threshold,
        "citations": format_citations(retrieved),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Local KB QA (RAG)")
    sub = p.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="Build KB index")
    p_index.add_argument("--kb", required=True, help="KB directory")
    p_index.add_argument("--index-dir", default="data/index", help="Index output dir")
    p_index.add_argument("--chunks-path", default="data/chunks.json", help="Chunks JSON path")
    p_index.add_argument("--embedding-model", default="text-embedding-3-small", help="Embedding model")
    p_index.add_argument("--max-len", type=int, default=800, help="Max chunk length")
    p_index.add_argument("--overlap", type=int, default=120, help="Chunk overlap length")
    p_index.add_argument("--batch-size", type=int, default=16, help="Embedding batch size")
    p_index.set_defaults(func=cmd_index)

    p_ask = sub.add_parser("ask", help="Ask question")
    p_ask.add_argument("--question", required=True, help="Question text")
    p_ask.add_argument("--topk", type=int, default=5, help="Top-K retrieval")
    p_ask.add_argument("--threshold", type=float, default=0.35, help="Refusal threshold")
    p_ask.add_argument("--index-dir", default="data/index", help="Index dir")
    p_ask.add_argument("--chunks-path", default="data/chunks.json", help="Chunks JSON path")
    p_ask.add_argument("--embedding-model", default="text-embedding-3-small", help="Embedding model")
    p_ask.add_argument("--model", default="gpt-4o-mini", help="Answer model")
    p_ask.set_defaults(func=cmd_ask)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
