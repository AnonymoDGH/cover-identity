"""Command-line interface for the Cover Identity Generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import export_json, export_markdown, generate, quiz


def cmd_new(args: argparse.Namespace) -> None:
    ident = generate(locale=args.locale, seed=args.seed)
    if args.format == "json":
        text = export_json(ident)
    elif args.format == "markdown":
        text = export_markdown(ident)
    else:
        text = (
            f"{ident['name']} · {ident['age']} · {ident['date_of_birth']}\n"
            f"{ident['address']}\n"
            f"{ident['phone']} · {ident['email']}\n"
            f"{ident['occupation']} at {ident['employer']}\n"
        )
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"[+] Legend written to {args.out}")
    else:
        print(text)


def cmd_memorize(args: argparse.Namespace) -> None:
    ident = generate(locale=args.locale, seed=args.seed)
    questions = quiz(ident)
    print("[*] Cover drill — answer from memory. Fail one, and you're burned.")
    for i, item in enumerate(questions, 1):
        ans = input(f"  {i}. {item['q']}: ").strip().lower()
        good = item["a"].lower()
        if ans == good:
            print("     ✓")
        else:
            print(f"     ✗  ({item['a']})")
    print("[*] Drill complete. Stay in character.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="coverid",
        description="Generate fictional, internally consistent cover identities.",
        epilog="Example: coverid new --locale es_ES --seed 7 --format markdown --out legend.md",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="generate an identity")
    p_new.add_argument("--locale", default="en_US", help="Faker locale")
    p_new.add_argument("--seed", type=int, default=None, help="deterministic identity")
    p_new.add_argument("--format", default="plain", choices=["plain", "json", "markdown"])
    p_new.add_argument("--out", default=None, help="write to file")
    p_new.set_defaults(fn=cmd_new)

    p_mem = sub.add_parser("memorize", help="drill yourself on an identity")
    p_mem.add_argument("--locale", default="en_US")
    p_mem.add_argument("--seed", type=int, default=None)
    p_mem.set_defaults(fn=cmd_memorize)

    args = p.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
