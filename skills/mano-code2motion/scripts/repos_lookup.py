#!/usr/bin/env python3
"""Lookup tool for references/repos-18.json.

Stdlib only, Python 3.8+. Read-only: never writes to the repo.

Usage:
    python scripts/repos_lookup.py --tag timing
    python scripts/repos_lookup.py --query captions
    python scripts/repos_lookup.py --repo pmndrs/react-postprocessing
    python scripts/repos_lookup.py --list-tags
    python scripts/repos_lookup.py --all --format json

The agent should read only the matching repos, not the whole file.
Do not copy code, prompts, media, fonts or models from these repos;
distill rules only, and check each repo license before reusing anything.
"""
import argparse
import json
import os
import sys


def load_library():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "references", "repos-18.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def show(repo, verbose=False):
    print(repo["id"] + "  " + repo["repo"] + "  [" + repo["license"] + "]")
    print("  " + repo["url"])
    print("  " + repo["description"])
    print("  tags: " + ", ".join(repo.get("tags", [])))
    if verbose:
        print("  mechanism: " + repo["mechanism"])
        print("  use_when: " + repo["use_when"])
        print("  not_when: " + repo["not_when"])
        print("  call_how: " + repo["call_how"])
        for t in repo.get("techniques", []):
            print("  - " + t)
        for u in repo.get("unverified", []):
            print("  unverified: " + u)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search the repos-18 library.")
    parser.add_argument("--tag", help="match a tag, e.g. timing, captions, particles")
    parser.add_argument("--query", help="case-insensitive word in id/repo/description/tags/techniques")
    parser.add_argument("--repo", help="exact owner/name, e.g. librosa/librosa")
    parser.add_argument("--list-tags", action="store_true", help="list lookup_by_task map and all tags")
    parser.add_argument("--all", action="store_true", help="list all 18 repos (short form)")
    parser.add_argument("--verbose", action="store_true", help="print mechanism, techniques and unverified notes")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    lib = load_library()
    repos = lib["repos"]

    if args.list_tags:
        print("lookup_by_task:")
        for task, ids in lib.get("lookup_by_task", {}).items():
            print("  " + task + ": " + ", ".join(ids))
        tags = sorted({t for r in repos for t in r.get("tags", [])})
        print("tags: " + ", ".join(tags))
        return 0

    matched = repos
    if args.repo:
        matched = [r for r in repos if r["repo"] == args.repo]
    elif args.tag:
        needle = args.tag.lower()
        matched = [r for r in repos if needle in [t.lower() for t in r.get("tags", [])]]
    elif args.query:
        needle = args.query.lower()
        matched = []
        for r in repos:
            hay = " ".join([r["id"], r["repo"], r["description"]] + r.get("tags", []) + r.get("techniques", [])).lower()
            if needle in hay:
                matched.append(r)
    elif not args.all:
        parser.error("give --tag, --query, --repo, --all or --list-tags")

    if not matched:
        print("no match", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(matched, ensure_ascii=False, indent=2))
        return 0

    for r in matched:
        show(r, verbose=args.verbose)
        print()
    print("matched %d of %d (checked %s)" % (len(matched), len(repos), lib.get("checked", "?")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
