#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate README.md and papers.bib from papers.yaml.

Metadata is never hand-written. For each entry we resolve the arXiv ID to an
INSPIRE record and pull authoritative metadata plus BibTeX. Papers with no
INSPIRE record (common for cs.LG-only work) fall back to the arXiv API.

Usage:
    python scripts/build.py            # build
    python scripts/build.py --check    # exit 1 if outputs are stale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "papers.yaml"
CACHE = ROOT / ".cache" / "metadata.json"
README = ROOT / "README.md"
BIB = ROOT / "papers.bib"

INSPIRE_ARXIV = "https://inspirehep.net/api/arxiv/{arxiv}"
INSPIRE_BIB = "https://inspirehep.net/api/literature/{recid}?format=bibtex"
ARXIV_API = "http://export.arxiv.org/api/query?id_list={arxiv}"
ATOM = "{http://www.w3.org/2005/Atom}"

USER_AGENT = "lemurs-calorimeter-papers/1.0 (github.com/Aaheer17/lemurs-calorimeter-papers)"
PAUSE = 1.0  # be polite to both APIs

CODE_MARK = {"available": "yes", "none": "no", "unverified": "?"}

TIER_TITLES = {
    0: ("Tier 0 — The dataset", "The anchor. Everything else is positioned relative to this."),
    1: ("Tier 1 — Trains on LEMURS", "Pre-trains or fine-tunes on the dataset itself."),
    2: ("Tier 2 — Transfer and adaptation, not on LEMURS",
        "Same family of question, different data. Note the transfer axis on each "
        "entry: geometry, material+species and fidelity results are not directly "
        "comparable to one another."),
    3: ("Tier 3 — Direct antecedents of Tier 1-2 work",
        "A Tier 1-2 paper builds on these or benchmarks against them."),
    None: ("Untriaged", "Found but not yet read. `uses_lemurs: unverified` means the tier is a guess."),
}


def best_date(md: dict, arxiv: str) -> str:
    """INSPIRE records don't all carry earliest_date. Walk a fallback chain,
    ending at the arXiv ID itself, which always encodes YYMM."""
    for field in ("earliest_date", "preprint_date", "legacy_creation_date"):
        if md.get(field):
            return md[field]
    for imp in md.get("imprints") or []:
        if imp.get("date"):
            return imp["date"]
    for pub in md.get("publication_info") or []:
        if pub.get("year"):
            return str(pub["year"])
    yy, mm = arxiv[:2], arxiv[2:4]          # 2603.28804 -> 2026-03
    if yy.isdigit() and mm.isdigit():
        return f"20{yy}-{mm}"
    return ""


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def from_inspire(arxiv: str, recid: int | None) -> dict | None:
    """Resolve via INSPIRE. Returns None if the paper has no record."""
    try:
        if recid is None:
            data = json.loads(fetch(INSPIRE_ARXIV.format(arxiv=arxiv)))
            recid = data["metadata"]["control_number"]
        else:
            data = json.loads(fetch(f"https://inspirehep.net/api/literature/{recid}"))
        md = data["metadata"]
        time.sleep(PAUSE)
        bibtex = fetch(INSPIRE_BIB.format(recid=recid)).decode("utf-8").strip()
        return {
            "source": "inspire",
            "recid": recid,
            "title": md["titles"][0]["title"],
            "authors": [a["full_name"] for a in md.get("authors", [])],
            "date": best_date(md, arxiv),
            "bibtex": bibtex,
        }
    except Exception as exc:  # noqa: BLE001 - any failure means fall back
        print(f"    inspire miss for {arxiv}: {exc}", file=sys.stderr)
        return None


def from_arxiv(arxiv: str) -> dict:
    """Fallback for papers with no INSPIRE record."""
    root = ET.fromstring(fetch(ARXIV_API.format(arxiv=arxiv)))
    entry = root.find(f"{ATOM}entry")
    if entry is None:
        raise RuntimeError(f"arXiv returned no entry for {arxiv}")
    title = " ".join(entry.findtext(f"{ATOM}title", "").split())
    authors = [
        a.findtext(f"{ATOM}name", "").strip() for a in entry.findall(f"{ATOM}author")
    ]
    date = entry.findtext(f"{ATOM}published", "")[:10]
    return {
        "source": "arxiv",
        "recid": None,
        "title": title,
        "authors": authors,
        "date": date,
        "bibtex": arxiv_bibtex(arxiv, title, authors, date),
    }


def arxiv_bibtex(arxiv: str, title: str, authors: list[str], date: str) -> str:
    surname = re.split(r"[\s,]+", authors[0])[-1].lower() if authors else "anon"
    year = date[:4] or "n.d."
    first_word = re.sub(r"[^a-z]", "", title.split()[0].lower()) if title else "untitled"
    return (
        f"@article{{{surname}:{year}{first_word},\n"
        f'    author        = "{" and ".join(authors)}",\n'
        f'    title         = "{{{title}}}",\n'
        f'    eprint        = "{arxiv}",\n'
        f'    archivePrefix = "arXiv",\n'
        f'    year          = "{year}",\n'
        f"}}"
    )


def load_cache() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {}


def save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=2, sort_keys=True))


def collect(entries: list[dict], cache: dict, refresh: bool) -> dict:
    for e in entries:
        arxiv = e["arxiv"]
        if arxiv in cache and not refresh:
            continue
        print(f"  fetching {arxiv} ({e.get('key', 'background')})")
        md = from_inspire(arxiv, e.get("inspire"))
        if md is None:
            try:
                md = from_arxiv(arxiv)
            except Exception as exc:  # noqa: BLE001
                raise SystemExit(
                    f"\n  Could not fetch metadata for {arxiv} ({e.get('key', 'background')}).\n"
                    f"  INSPIRE returned nothing and the arXiv fallback failed: {exc}\n\n"
                    f"  Check the ID at https://arxiv.org/abs/{arxiv}, then confirm you\n"
                    f"  can reach inspirehep.net and export.arxiv.org. Cached entries in\n"
                    f"  .cache/metadata.json are reused, so a partial run is not lost."
                ) from exc
        cache[arxiv] = md
        save_cache(cache)   # checkpoint, so a mid-run failure keeps prior work
        time.sleep(PAUSE)
    return cache


def authors_str(authors: list[str], limit: int = 4) -> str:
    if not authors:
        return "—"
    if len(authors) <= limit:
        return ", ".join(authors)
    return ", ".join(authors[:limit]) + f", *et al.* ({len(authors)} authors)"


def render_entry(e: dict, md: dict) -> str:
    arxiv = e["arxiv"]
    lines = [f"### {md['title']}", ""]
    lines.append(f"**{authors_str(md['authors'])}** · {md['date'] or 'n.d.'}")
    if e.get("venue"):
        lines.append(f"  \n*{e['venue']}*")
    lines.append("")

    links = [f"[arXiv:{arxiv}](https://arxiv.org/abs/{arxiv})",
             f"[PDF](https://arxiv.org/pdf/{arxiv})"]
    if md.get("recid"):
        links.append(f"[INSPIRE](https://inspirehep.net/literature/{md['recid']})")
    for r in e.get("resources") or []:
        host = urllib.parse.urlparse(r["url"]).netloc.removeprefix("www.")
        links.append(f"[{r['kind']}: {host}]({r['url']})")
    lines.append(" · ".join(links))
    lines.append("")

    facts = []
    lemurs = {True: "yes", False: "no", "unverified": "unverified"}[e["uses_lemurs"]]
    facts.append(f"**Uses LEMURS:** {lemurs}")
    if e.get("axis"):
        facts.append(f"**Transfer axis:** {e['axis']}")
    if e.get("pretrain"):
        facts.append(f"**Pre-train:** {e['pretrain']}")
    if e.get("target"):
        facts.append(f"**Target:** {e['target']}")
    if e.get("repr"):
        facts.append(f"**Representation:** {e['repr']}")
    facts.append(f"**Code:** {e.get('code', 'unverified')}")
    if e.get("geometries"):
        facts.append(f"**Geometries:** {', '.join(e['geometries'])}")
    lines.append(" · ".join(facts))
    lines.append("")
    lines.append(" ".join(e["note"].split()))
    lines.append("")
    return "\n".join(lines)


def render_readme(entries: list[dict], cache: dict,
                  background: list[dict] | None = None) -> str:
    out: list[str] = []
    out.append("<!-- GENERATED FILE — edit papers.yaml, then run scripts/build.py -->")
    out.append("")
    out.append("# LEMURS Calorimeter Papers")
    out.append("")
    out.append(
        "Papers that use or relate to the "
        "[LEMURS](https://arxiv.org/abs/2509.05108) multi-detector "
        "electromagnetic calorimeter shower dataset."
    )
    out.append("")
    out.append(
        "Tracked monthly. The organising question is narrower than "
        "\"fast calorimeter simulation\": **does this work actually train on "
        "LEMURS?** Citing the dataset in related work is not the same thing, and "
        "the tiers keep that distinction visible."
    )
    out.append("")

    out.append("## Tiers")
    out.append("")
    out.append("| Tier | Meaning |")
    out.append("|------|---------|")
    for t in (0, 1, 2, 3):
        out.append(f"| **{t}** | {TIER_TITLES[t][0].split('— ', 1)[1]} |")
    out.append("")

    out.append("## Index")
    out.append("")
    out.append("| Paper | Tier | LEMURS | Repr. | Code |")
    out.append("|-------|------|--------|-------|------|")
    for e in entries:
        md = cache[e["arxiv"]]
        title = md["title"]
        short = title if len(title) <= 60 else title[:57].rstrip() + "…"
        tier = e["tier"] if e["tier"] is not None else "—"
        lemurs = {True: "yes", False: "no", "unverified": "?"}[e["uses_lemurs"]]
        out.append(
            f"| [{short}](https://arxiv.org/abs/{e['arxiv']}) | {tier} "
            f"| {lemurs} | {e.get('repr', '—')} | {CODE_MARK[e.get('code', 'unverified')]} |"
        )
    out.append("")

    for tier in (0, 1, 2, 3, None):
        group = [e for e in entries if e["tier"] == tier]
        if not group:
            continue
        heading, blurb = TIER_TITLES[tier]
        out.append(f"## {heading}")
        out.append("")
        out.append(f"*{blurb}*")
        out.append("")
        for e in group:
            out.append(render_entry(e, cache[e["arxiv"]]))

    if background:
        out.append("## Background")
        out.append("")
        out.append(
            "Widely cited work with no traceable link to LEMURS. Listed so it is "
            "findable and citable, but deliberately untiered — everything above "
            "would be pointless if LEMURS did not exist, and these would not."
        )
        out.append("")
        for e in background:
            md = cache[e["arxiv"]]
            first = md["authors"][0].split(",")[0] if md["authors"] else "—"
            more = " et al." if len(md["authors"]) > 1 else ""
            out.append(
                f"- [{md['title']}](https://arxiv.org/abs/{e['arxiv']}) — "
                f"{first}{more}, {md['date'][:4] or 'n.d.'}. {e['why']}"
            )
        out.append("")

    out.append("---")
    out.append("")
    out.append("## How this is maintained")
    out.append("")
    out.append(
        "`papers.yaml` is the only file edited by hand. `README.md` and "
        "`papers.bib` are generated from it by `scripts/build.py`, which pulls "
        "titles, authors, dates and BibTeX from INSPIRE — falling back to the "
        "arXiv API for papers with no INSPIRE record."
    )
    out.append("")
    out.append(
        "Suggestions welcome: open an issue with the arXiv ID. Papers that use "
        "LEMURS but aren't listed are especially useful, since the citation "
        "watchers under-cover work filed outside the physics categories."
    )
    out.append("")
    out.append("## License")
    out.append("")
    out.append("Code in `scripts/` is MIT — see [LICENSE](LICENSE).  ")
    out.append(
        "The paper list and annotations are CC BY 4.0 — see "
        "[LICENSE-CONTENT](LICENSE-CONTENT)."
    )
    out.append("")
    out.append(
        "Bibliographic metadata (titles, authors, identifiers) are facts and are "
        "not claimed under either license. Summaries are paraphrases written for "
        "this repo, not publisher abstracts."
    )
    out.append("")
    return "\n".join(out)


def render_bib(entries: list[dict], cache: dict,
               background: list[dict] | None = None) -> str:
    out = [
        "% GENERATED FILE — edit papers.yaml, then run scripts/build.py",
        "% Source: INSPIRE-HEP, with arXiv fallback for records INSPIRE lacks.",
        "",
    ]
    for e in entries:
        md = cache[e["arxiv"]]
        out.append(f"% {e['key']} — tier {e['tier']} — {md['source']}")
        out.append(md["bibtex"])
        out.append("")
    for e in background or []:
        md = cache[e["arxiv"]]
        out.append(f"% background — {md['source']}")
        out.append(md["bibtex"])
        out.append("")
    return "\n".join(out)


def validate(entries: list[dict]) -> list[str]:
    """tier 1 is *defined* as training on LEMURS. Keep the two fields in step."""
    problems = []
    seen = set()
    for e in entries:
        k, uses = e["key"], e["uses_lemurs"]
        if k in seen:
            problems.append(f"{k}: duplicate key")
        seen.add(k)
        if e["tier"] == 1 and uses is not True:
            problems.append(f"{k}: tier 1 but uses_lemurs is {uses!r}")
        if uses is True and e["tier"] not in (0, 1):
            problems.append(f"{k}: uses_lemurs true but tier {e['tier']}")
        if uses == "unverified" and e["tier"] is not None:
            problems.append(f"{k}: tier {e['tier']} assigned while uses_lemurs unverified")
        if e["tier"] == 2 and not e.get("axis"):
            problems.append(f"{k}: tier 2 needs an `axis` (geometry | material+species | fidelity)")
        if e.get("axis") and e["tier"] != 2:
            problems.append(f"{k}: `axis` is a tier 2 field")
        if e.get("axis") and e["axis"] not in {"geometry", "material+species", "fidelity"}:
            problems.append(f"{k}: axis {e['axis']!r} not recognised")
        if e.get("code") not in CODE_MARK:
            problems.append(f"{k}: code must be one of {sorted(CODE_MARK)}")
        for r in e.get("resources") or []:
            if not str(r.get("url", "")).startswith("http"):
                problems.append(f"{k}: resource url must be absolute")
            if r.get("kind") not in {"code", "data", "model", "page"}:
                problems.append(f"{k}: resource kind {r.get('kind')!r} not recognised")
    return problems


def validate_background(background: list[dict]) -> list[str]:
    problems = []
    for e in background:
        if not e.get("arxiv"):
            problems.append("background entry missing arxiv")
        if not e.get("why"):
            problems.append(f"background {e.get('arxiv')}: needs a `why`")
        for field in ("tier", "uses_lemurs", "code", "note"):
            if field in e:
                problems.append(
                    f"background {e.get('arxiv')}: has `{field}` — background is "
                    f"untiered by design; promote it to papers: or drop the field"
                )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if outputs are stale")
    ap.add_argument("--refresh", action="store_true", help="ignore the metadata cache")
    args = ap.parse_args()

    data = yaml.safe_load(PAPERS.read_text())
    entries = data["papers"]
    print(f"{len(entries)} entries in papers.yaml")

    problems = validate(entries) + validate_background(data.get("background") or [])
    if problems:
        for p in problems:
            print(f"  ! {p}", file=sys.stderr)
        return 1

    pending = {
        "uses_lemurs": sum(1 for e in entries if e["uses_lemurs"] == "unverified"),
        "code": sum(1 for e in entries if e.get("code") == "unverified"),
    }
    for field, n in pending.items():
        if n:
            print(f"  {n} entries unverified on {field} — resolve when you read them")

    background = data.get("background") or []
    cache = collect(entries + background, load_cache(), args.refresh)
    save_cache(cache)

    readme = render_readme(entries, cache, background)
    bib = render_bib(entries, cache, background)

    if args.check:
        stale = []
        if not README.exists() or README.read_text() != readme:
            stale.append("README.md")
        if not BIB.exists() or BIB.read_text() != bib:
            stale.append("papers.bib")
        if stale:
            print(f"stale: {', '.join(stale)} — run scripts/build.py", file=sys.stderr)
            return 1
        print("outputs up to date")
        return 0

    README.write_text(readme)
    BIB.write_text(bib)
    print(f"wrote {README.name} and {BIB.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())