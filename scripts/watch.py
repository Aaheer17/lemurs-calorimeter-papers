#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Find papers that should probably be on the list, and report each one once.

Three independent sources, because no single one covers the field:

  INSPIRE   citations of the anchor papers. Authoritative for HEP, but only
            counts citations from records inside INSPIRE, so cs-venue work is
            invisible to it.
  arXiv     keyword search, deliberately WITHOUT a category filter. "calorimeter"
            is specific enough that filtering by category costs recall and buys
            no precision -- and category filtering is exactly what would miss a
            cs.LG-only paper.
  S2        Semantic Scholar citations. Spans both worlds, so it covers the gap
            between the other two.

Each source is wrapped so one dead API cannot kill the run.

The script never edits papers.yaml. Tier and uses_lemurs require reading the
paper; this only tells you a paper exists.

Usage:
    python scripts/watch.py                 # report, update the seen ledger
    python scripts/watch.py --dry-run       # report, change nothing
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "papers.yaml"
SEEN = ROOT / ".watch-seen.json"
ATOM = "{http://www.w3.org/2005/Atom}"

USER_AGENT = "lemurs-calorimeter-papers/1.0 (github.com/Aaheer17/lemurs-calorimeter-papers)"
PAUSE = 1.0
# \b fails against a version suffix (…08v2), so bound on digits instead.
ARXIV_RE = re.compile(r"(?<!\d)(\d{4}\.\d{4,5})(?!\d)")


@dataclass
class Candidate:
    arxiv: str
    title: str = ""
    authors: str = ""
    date: str = ""
    found_via: set[str] = field(default_factory=set)


def norm(arxiv: str | None) -> str | None:
    """Strip version suffixes and any surrounding noise: arXiv:2509.05108v2 -> 2509.05108"""
    if not arxiv:
        return None
    m = ARXIV_RE.search(str(arxiv))
    return m.group(1) if m else None


def fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def guarded(name: str):
    """A failing source should degrade the run, not end it."""
    def deco(fn):
        def wrapper(*a, **kw):
            try:
                found = fn(*a, **kw)
                print(f"  {name}: {len(found)} results")
                return found
            except Exception as exc:  # noqa: BLE001
                print(f"  {name}: FAILED ({exc}) — continuing", file=sys.stderr)
                return []
        return wrapper
    return deco


# --------------------------------------------------------------------------
# sources
# --------------------------------------------------------------------------

@guarded("inspire")
def watch_inspire(anchor_ids: list[str]) -> list[Candidate]:
    out: list[Candidate] = []
    for arxiv in anchor_ids:
        try:
            rec = json.loads(fetch(f"https://inspirehep.net/api/arxiv/{arxiv}"))
            recid = rec["metadata"]["control_number"]
        except Exception:  # noqa: BLE001 - anchor may not be in INSPIRE
            print(f"    no INSPIRE record for anchor {arxiv}, skipping")
            continue
        time.sleep(PAUSE)

        q = urllib.parse.urlencode({
            "q": f"refersto recid:{recid}",
            "fields": "titles,authors,arxiv_eprints,earliest_date",
            "size": 100,
            "sort": "mostrecent",
        })
        data = json.loads(fetch(f"https://inspirehep.net/api/literature?{q}"))
        for hit in data.get("hits", {}).get("hits", []):
            md = hit.get("metadata", {})
            eprints = md.get("arxiv_eprints") or []
            aid = norm(eprints[0].get("value")) if eprints else None
            if not aid:
                continue
            authors = [a.get("full_name", "") for a in md.get("authors", [])]
            out.append(Candidate(
                arxiv=aid,
                title=(md.get("titles") or [{}])[0].get("title", ""),
                authors=", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
                date=md.get("earliest_date", ""),
                found_via={f"cites {arxiv}"},
            ))
        time.sleep(PAUSE)
    return out


@guarded("arxiv")
def watch_arxiv(queries: list[str]) -> list[Candidate]:
    out: list[Candidate] = []
    for query in queries:
        q = urllib.parse.urlencode({
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 50,
        })
        root = ET.fromstring(fetch(f"http://export.arxiv.org/api/query?{q}"))
        for entry in root.findall(f"{ATOM}entry"):
            aid = norm(entry.findtext(f"{ATOM}id", ""))
            if not aid:
                continue
            authors = [a.findtext(f"{ATOM}name", "") for a in entry.findall(f"{ATOM}author")]
            out.append(Candidate(
                arxiv=aid,
                title=" ".join(entry.findtext(f"{ATOM}title", "").split()),
                authors=", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
                date=entry.findtext(f"{ATOM}published", "")[:10],
                found_via={"arxiv keyword"},
            ))
        time.sleep(PAUSE * 3)  # arXiv asks for a slower cadence
    return out


@guarded("semantic scholar")
def watch_s2(anchor_ids: list[str]) -> list[Candidate]:
    out: list[Candidate] = []
    for arxiv in anchor_ids:
        url = (f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv}"
               f"/citations?fields=title,externalIds,year,authors&limit=100")
        data = json.loads(fetch(url))
        for item in data.get("data", []):
            paper = item.get("citingPaper") or {}
            aid = norm((paper.get("externalIds") or {}).get("ArXiv"))
            if not aid:
                continue
            authors = [a.get("name", "") for a in paper.get("authors") or []]
            out.append(Candidate(
                arxiv=aid,
                title=paper.get("title", ""),
                authors=", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
                date=str(paper.get("year") or ""),
                found_via={f"S2 cites {arxiv}"},
            ))
        time.sleep(PAUSE)
    return out


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

def merge(batches: list[list[Candidate]]) -> dict[str, Candidate]:
    """One entry per arXiv ID, but keep every route that found it — a paper
    surfaced by all three sources is a stronger signal than one from keywords."""
    merged: dict[str, Candidate] = {}
    for batch in batches:
        for c in batch:
            if c.arxiv in merged:
                merged[c.arxiv].found_via |= c.found_via
                if not merged[c.arxiv].title:
                    merged[c.arxiv].title = c.title
            else:
                merged[c.arxiv] = c
    return merged


def render(new: list[Candidate]) -> str:
    lines = [
        f"{len(new)} paper(s) turned up that aren't in `papers.yaml`.",
        "",
        "Triage each one: does it **train on LEMURS**, or merely cite it? "
        "Citing is not using — that distinction is what the tiers exist for.",
        "",
    ]
    for c in sorted(new, key=lambda x: x.date, reverse=True):
        routes = ", ".join(sorted(c.found_via))
        lines += [
            f"### [{c.title or c.arxiv}](https://arxiv.org/abs/{c.arxiv})",
            f"`{c.arxiv}` · {c.authors or '—'} · {c.date or 'n.d.'}",
            f"<sub>found via: {routes}</sub>",
            "",
            "```yaml",
            f'  - key: CHANGEME',
            f'    arxiv: "{c.arxiv}"',
            "    inspire: null",
            "    tier: null          # 0-3, or leave null until read",
            "    uses_lemurs: unverified",
            "    code: unverified",
            "    resources: []",
            "    note: >",
            "      TODO",
            "```",
            "",
        ]
    lines += [
        "---",
        "*Each ID is reported once. Closing this issue without acting means "
        "these will not resurface — drop anything out of scope into "
        "`background:` if it is worth keeping findable.*",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="do not update the ledger")
    args = ap.parse_args()

    data = yaml.safe_load(PAPERS.read_text())
    papers = data["papers"]
    background = data.get("background") or []
    watchers = data.get("watchers") or {}

    known = {norm(p["arxiv"]) for p in papers} | {norm(b["arxiv"]) for b in background}
    seen = set(json.loads(SEEN.read_text())) if SEEN.exists() else set()
    print(f"{len(known)} on the list, {len(seen)} previously reported")

    by_key = {p["key"]: p["arxiv"] for p in papers}
    def anchors(cfg) -> list[str]:
        return [by_key[k] for k in (cfg or {}).get("anchors", []) if k in by_key]

    found = merge([
        watch_inspire(anchors(watchers.get("inspire"))),
        watch_arxiv((watchers.get("arxiv") or {}).get("queries", [])),
        watch_s2(anchors(watchers.get("semantic_scholar"))),
    ])

    new = [c for aid, c in found.items() if aid not in known and aid not in seen]
    print(f"{len(found)} unique found, {len(new)} new")

    if not new:
        print("nothing new")
        return 0

    body = render(new)
    (ROOT / ".watch-report.md").write_text(body)

    if not args.dry_run:
        SEEN.write_text(json.dumps(sorted(seen | {c.arxiv for c in new}), indent=2))

    # tells the workflow whether to open an issue
    if gh := os.environ.get("GITHUB_OUTPUT"):
        with open(gh, "a") as fh:
            fh.write(f"new_count={len(new)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
