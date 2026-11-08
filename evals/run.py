import argparse
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app import db
from app.ingest import add_document
from app.search import keyword_chunks

HERE = Path(__file__).resolve().parent


def norm(text: str) -> str:
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return " ".join(text.split())


def load_cases() -> list[dict]:
    lines = (HERE / "cases.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def evaluate(case: dict, limit: int) -> dict:
    db.reset_container(case["container"])
    for index, text in enumerate(case["setup"]):
        add_document(case["container"], text, custom_id=f"{case['id']}-{index}")

    hits = keyword_chunks(case["container"], case["query"], limit)
    found = 0
    first_rank = None

    for expected in case["expected"]:
        for rank, hit in enumerate(hits, start=1):
            if norm(expected) in norm(hit["content"]):
                found += 1
                if first_rank is None or rank < first_rank:
                    first_rank = rank
                break

    return {
        "id": case["id"],
        "kind": case["kind"],
        "hit": found > 0,
        "recall": found / len(case["expected"]) if case["expected"] else 0.0,
        "mrr": 1.0 / first_rank if first_rank else 0.0,
        "returned": len(hits),
    }


def summarize(results: list[dict]) -> dict:
    total = len(results)
    hits = sum(1 for result in results if result["hit"])
    recall = sum(result["recall"] for result in results) / total if total else 0.0
    mrr = sum(result["mrr"] for result in results) / total if total else 0.0
    return {"cases": total, "hit": hits / total if total else 0.0, "recall": recall, "mrr": mrr}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="evals")
    parser.add_argument("--mode", choices=["keyword"], default="keyword")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)

    cases = load_cases()
    with tempfile.TemporaryDirectory() as tmp:
        db.connect(Path(tmp) / "eval.db")
        results = [evaluate(case, args.limit) for case in cases]
        db.close()

    print(f"mode={args.mode} limit={args.limit}\n")
    for result in results:
        mark = "ok" if result["hit"] else "miss"
        print(f"{result['id']:<4} {result['kind']:<14} {mark:<4} recall={result['recall']:.2f} mrr={result['mrr']:.2f}")

    print()
    for kind in sorted({result["kind"] for result in results}):
        subset = [result for result in results if result["kind"] == kind]
        summary = summarize(subset)
        print(f"{kind:<14} hit={summary['hit']:.2f} recall={summary['recall']:.2f} mrr={summary['mrr']:.2f}")

    summary = summarize(results)
    print(f"{'overall':<14} hit={summary['hit']:.2f} recall={summary['recall']:.2f} mrr={summary['mrr']:.2f}")

    reports = HERE / "reports"
    reports.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (reports / f"{args.mode}-{stamp}.json").write_text(
        json.dumps({"mode": args.mode, "summary": summary, "results": results}, indent=2)
    )


if __name__ == "__main__":
    main()
