import argparse

from app import db
from app.ingest import add_document
from app.search import keyword_chunks


def _add(args: argparse.Namespace) -> None:
    print(args)
    result = add_document(args.container, " ".join(args.content))
    state = "created" if result["created"] else "exists"
    print(f"{result['id'][:8]}  {result['status']}  {result['chunks']} chunks  {state}")


def _ls(args: argparse.Namespace) -> None:
    docs = db.list_documents(args.container)
    if not docs:
        print("no documents")
        return
    for doc in docs:
        preview = " ".join(doc.content.split())[:70]
        print(f"{doc.id[:8]}  {doc.status:<6}  {doc.created_at[:10]}  {preview}")


def _search(args: argparse.Namespace) -> None:
    hits = keyword_chunks(args.container, " ".join(args.query), args.limit)
    if not hits:
        print("no matches")
        return
    for index, hit in enumerate(hits, start=1):
        text = " ".join(hit["content"].split())[:140]
        print(f"{index}. [{hit['score']:.3f}] {text}")


def _reset(args: argparse.Namespace) -> None:
    db.reset_container(args.container)
    print(f"reset {args.container}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="memoryx")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add")
    add.add_argument("container")
    add.add_argument("content", nargs="+")
    add.set_defaults(func=_add)

    ls = sub.add_parser("ls")
    ls.add_argument("container")
    ls.set_defaults(func=_ls)

    search = sub.add_parser("search")
    search.add_argument("container")
    search.add_argument("query", nargs="+")
    search.add_argument("--limit", type=int, default=5)
    search.set_defaults(func=_search)

    reset = sub.add_parser("reset")
    reset.add_argument("container")
    reset.set_defaults(func=_reset)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
