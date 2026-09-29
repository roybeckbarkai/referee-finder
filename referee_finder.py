#!/usr/bin/env python3
"""
referee_finder.py — find candidate referees from who cites your papers, and find
which of them a manuscript fails to cite.

Data source: OpenAlex. Requires a free API key in $OPENALEX_API_KEY.
Nothing here is inferred. Fields that cannot be retrieved are left empty.

  harvest   pull your works, then every work citing them
  rank      aggregate citing authors, apply exclusions, rank
  suggest   which ranked candidates does a manuscript not cite, and where could they go
  status    when did the last run happen and what did it see
  all       harvest then rank

Configure once in config.toml (copy config.example.toml). Then:

  export OPENALEX_API_KEY=...
  python3 referee_finder.py all
  python3 referee_finder.py suggest paper.tex --bib refs.bib

Stdlib only. Python 3.11+ for config.toml; older versions can use config.json.
MIT licensed.
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OA = "https://api.openalex.org"
STATE = "state.json"

DEFAULTS = {
    "author": {"orcid": "", "name": "", "doi_file": "data/author_dois.txt"},
    "exclusions": {
        "home_institutions": [],
        "exclude_recent_coauthors": True,
        "coauthor_window_years": 5,
        "manual_exclusions_file": "data/manual_exclusions.txt",
    },
    "ranking": {"group_papers_include_first_author": False, "top": 30},
}


def _deep_merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _deep_merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def load_config(path=None):
    for cand in ([path] if path else []) + [os.path.join(HERE, "config.toml"),
                                            os.path.join(HERE, "config.json")]:
        if cand and os.path.exists(cand):
            if cand.endswith(".toml"):
                try:
                    import tomllib
                except ModuleNotFoundError:
                    sys.exit("config.toml needs Python 3.11+. Use config.json instead "
                             "(same keys, JSON syntax).")
                with open(cand, "rb") as f:
                    cfg = _deep_merge(DEFAULTS, tomllib.load(f))
            else:
                cfg = _deep_merge(DEFAULTS, json.load(open(cand, encoding="utf8")))
            if not cfg["author"]["orcid"]:
                sys.exit(f"Set author.orcid in {cand} — find yours at https://orcid.org")
            cfg["_path"] = cand
            return cfg
    sys.exit("No config found. Copy config.example.toml to config.toml and fill it in.")


CFG = None          # populated in main()


def _key():
    k = os.environ.get("OPENALEX_API_KEY")
    if not k:
        sys.exit("OPENALEX_API_KEY is not set. OpenAlex rejects keyless calls (409/429).\n"
                 "Get a free key at https://openalex.org and:  export OPENALEX_API_KEY=...")
    return k


def _get(path, params, tries=6):
    params = {**params, "api_key": _key()}
    url = f"{OA}/{path}?" + urllib.parse.urlencode(params)
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Rate limited. Back off hard — a harvest is long and restarting it is
                # worse than waiting. Progress already written to data/ is kept, so a
                # give-up here can be resumed by re-running the same command.
                if n == tries - 1:
                    sys.exit("OpenAlex is rate-limiting this key (HTTP 429). Wait a few "
                             "minutes and re-run the same command — harvesting resumes "
                             "from where it stopped.")
                wait = 15 * (n + 1)
                print(f"  rate limited, waiting {wait}s…", flush=True)
                time.sleep(wait)
            elif e.code in (500, 502, 503, 504) and n < tries - 1:
                time.sleep(3 * (n + 1))
            else:
                raise
        except Exception:
            if n == tries - 1:
                raise
            time.sleep(3 * (n + 1))


def _page(path, params):
    cursor = "*"
    while cursor:
        d = _get(path, {**params, "per-page": 200, "cursor": cursor})
        for r in d.get("results", []):
            yield r
        cursor = d.get("meta", {}).get("next_cursor")
        if not d.get("results"):
            break


def author_ids():
    orcid = CFG["author"]["orcid"]
    res = _get("authors", {"filter": f"orcid:{orcid}", "select": "id,display_name,works_count"})
    ids = [a["id"] for a in res["results"]]
    if not ids:
        sys.exit(f"No OpenAlex author found for ORCID {orcid}")
    return ids


def load_state():
    p = os.path.join(DATA, STATE)
    return json.load(open(p)) if os.path.exists(p) else {}


def save_state(**kw):
    st = load_state()
    st.update(kw)
    json.dump(st, open(os.path.join(DATA, STATE), "w"), indent=1)


def _utc_today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def _cfg_path(rel):
    return rel if os.path.isabs(rel) else os.path.join(HERE, rel)


def read_doi_list():
    """Your publication DOIs, one per line. See the warning in harvest()."""
    p = _cfg_path(CFG["author"]["doi_file"])
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, encoding="utf8"):
        line = line.strip()
        if line.startswith("#PREPRINTS"):
            break                       # preprints below the marker are not harvested
        if line and not line.startswith("#"):
            out.append(line.lower())
    return out


def _window_start(cfg):
    yrs = int(cfg["exclusions"]["coauthor_window_years"] or 0)
    return int(time.strftime("%Y", time.gmtime())) - yrs + 1


def harvest(args):
    os.makedirs(DATA, exist_ok=True)
    me = author_ids()
    print(f"OpenAlex author ids for this ORCID: {me}")

    works, dois = [], read_doi_list()
    if dois and args.source != "orcid":
        # ANCHOR ON YOUR OWN PUBLICATION LIST, not on the OpenAlex author record.
        # OpenAlex disambiguation merges namesakes: for one test author it folded a
        # radio astronomer and a 1970s physicist with the same surname into the same
        # ORCID, adding 60 works that were not his and whose topic mix would have ranked
        # that unrelated field's researchers among his citers.
        # Check your own record once; if it is clean you may prefer --source orcid.
        for i in range(0, len(dois), 40):
            works += _get("works", {"filter": "doi:" + "|".join(dois[i:i + 40]),
                                    "per-page": 200,
                                    "select": "id,doi,title,publication_year,"
                                              "cited_by_count,authorships"})["results"]
            time.sleep(0.15)
        print(f"from your DOI list: {len(works)}/{len(dois)} resolved in OpenAlex")
    else:
        if not dois:
            print("No DOI list found — falling back to the OpenAlex author record.")
        print("WARNING: harvesting by author id. If OpenAlex has merged a namesake into "
              "your record the citation set will be contaminated. Prefer a DOI list.")
        for aid in me:
            works += list(_page("works", {"filter": f"author.id:{aid.rsplit('/', 1)[-1]}",
                                          "select": "id,doi,title,publication_year,"
                                                    "cited_by_count,authorships"}))
    seen = set()
    works = [w for w in works if not (w["id"] in seen or seen.add(w["id"]))]
    print(f"your works: {len(works)}  (total citations {sum(w['cited_by_count'] for w in works)})")
    json.dump(works, open(os.path.join(DATA, "author_works.json"), "w"))

    start = _window_start(CFG)
    collab = {}
    for w in works:
        if (w.get("publication_year") or 0) < start:
            continue
        for a in w.get("authorships", []):
            if a["author"]["id"] in me:
                continue
            c = collab.setdefault(a["author"]["id"],
                                  {"name": a["author"]["display_name"], "years": [],
                                   "institutions": []})
            c["years"].append(w["publication_year"])
            for i in a.get("institutions", []):
                if i["display_name"] not in c["institutions"]:
                    c["institutions"].append(i["display_name"])
    for c in collab.values():
        c["years"] = sorted(set(c["years"]))
    print(f"co-authors since {start}: {len(collab)}")
    json.dump(collab, open(os.path.join(DATA, "coauthors_recent.json"), "w"), indent=1)

    # Citing works, keyed by which of your papers they cite. Incremental by default:
    # only records CREATED in OpenAlex since the last successful harvest are fetched.
    cpath = os.path.join(DATA, "citing_works.json")
    prev = json.load(open(cpath)) if os.path.exists(cpath) else {}
    since = None if args.full else load_state().get("last_harvest_utc")
    print(f"incremental harvest since {since}" if since else "full harvest")

    citing = {k: list(v) for k, v in prev.items()} if since else {}
    added = 0
    for n, w in enumerate(works, 1):
        short = w["id"].rsplit("/", 1)[-1]
        is_new = w["id"] not in prev          # a newly added paper has no history
        flt = {"filter": f"cites:{short}",
               "select": "id,doi,title,publication_year,authorships,topics"}
        if since and not is_new:
            flt["filter"] += f",from_created_date:{since}"
        elif not w["cited_by_count"] and not is_new:
            continue
        got = list(_page("works", flt))
        have = {c["id"] for c in citing.get(w["id"], [])}
        fresh = [c for c in got if c["id"] not in have]
        if fresh:
            citing.setdefault(w["id"], []).extend(fresh)
            added += len(fresh)
            print(f"  [{n}/{len(works)}] {short} +{len(fresh)}", flush=True)
        time.sleep(0.1)

    json.dump(citing, open(cpath, "w"))
    total = sum(len(v) for v in citing.values())
    print(f"citing-work records: {total} total, {added} new this run")
    save_state(last_harvest_utc=_utc_today(),
               last_harvest_mode="incremental" if since else "full",
               author_works=len(works), citing_records=total)


def _short_id(x):
    return (x or "").rstrip("/").split("/")[-1].lower()


def _norm_name(s):
    s = re.sub(r"[{}\\\"'`.]", " ", s or "")
    s = unicodedata.normalize("NFKD", s.lower())
    return " ".join("".join(c for c in s if not unicodedata.combining(c)).split())


def _name_key(display_name):
    t = [x for x in _norm_name(display_name).split() if x]
    return (t[-1], t[0]) if len(t) > 1 else ((t[0], "") if t else ("", ""))


def _split_name(full):
    return _name_key(full)


def _same_person(full_name, sur, fore):
    """Surname must match AND forename initials must agree when both are known."""
    csur, cfore = _name_key(full_name)
    if not csur or csur != sur:
        return False
    if not cfore or not fore:
        return True
    return cfore[0] == fore.split()[0][0]


def read_out_of_scope():
    """DOIs of your papers that are yours but outside the field you want referees for."""
    p = _cfg_path("data/out_of_scope_dois.txt")
    if not os.path.exists(p):
        return set()
    return {_short_id(ln.split("#")[0].strip())
            for ln in open(p, encoding="utf8") if ln.split("#")[0].strip()}


def read_manual_exclusions():
    """{(surname, forename): reason} — conflicts the citation graph cannot see."""
    p = _cfg_path(CFG["exclusions"]["manual_exclusions_file"])
    out = {}
    if not os.path.exists(p):
        return out
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "," not in line:
            continue
        entry, _, reason = line.partition("#")
        sur, _, fore = entry.partition(",")
        out[(_norm_name(sur), _norm_name(fore).split()[0] if fore.strip() else "")] = \
            reason.strip() or "manual exclusion"
    return out


def rank(args):
    works = json.load(open(os.path.join(DATA, "author_works.json")))
    citing = json.load(open(os.path.join(DATA, "citing_works.json")))
    collab = json.load(open(os.path.join(DATA, "coauthors_recent.json")))
    me = set(author_ids())
    home = [h.lower() for h in CFG["exclusions"]["home_institutions"]]
    my_surname = _name_key(CFG["author"]["name"])[0] if CFG["author"]["name"] else ""

    # A GROUP PAPER is one you led as PI, i.e. you are LAST author. Citing those is a
    # far stronger signal than citing a large collaboration you merely joined.
    #
    # First-author papers are excluded by default and that default matters: for an
    # author whose first-author work was done as a student or postdoc, counting it
    # seeds their FORMER SUPERVISOR'S lab as candidates. In testing it put the old
    # postdoc host at rank 72 and pulled eight of that lab into the top 30. If you
    # published first-author work as an independent PI, set
    # ranking.group_papers_include_first_author = true, then read the senior author of
    # each newly admitted paper — anyone else in that slot is a training-lab paper.
    pos = {}
    for w in works:
        p = None
        for a in w.get("authorships", []):
            if a["author"]["id"] in me:
                p = a.get("author_position")
        if p is None and my_surname:
            hits = [a for a in w.get("authorships", [])
                    if _name_key(a["author"]["display_name"])[0] == my_surname]
            if len(hits) == 1:
                p = hits[0].get("author_position")
        pos[w["id"]] = p
    lead = ("last", "first") if (args.group_includes_first or
                                 CFG["ranking"]["group_papers_include_first_author"]) else ("last",)
    oos = read_out_of_scope()
    group_papers = {k for k, v in pos.items() if v in lead and _short_id(k) not in oos}
    print(f"of {len(works)} papers, {len(group_papers)} count as group papers "
          f"({'first or last' if len(lead) > 1 else 'last'} author)")

    coauthor_years = defaultdict(set)
    for w in works:
        for a in w.get("authorships", []):
            if a["author"]["id"] not in me:
                coauthor_years[a["author"]["id"]].add(w.get("publication_year"))

    me_names = {_name_key(a["author"]["display_name"])
                for w in works for a in w.get("authorships", []) if a["author"]["id"] in me}
    start = _window_start(CFG)

    agg = {}
    for work_id, cites in citing.items():
        for c in cites:
            yr = c.get("publication_year") or 0
            for a in c.get("authorships", []):
                nm = a["author"].get("display_name") or ""
                # ~4% of OpenAlex authorship records carry NO author id. Keying on a
                # falsy id collapses all of them into ONE phantom author that
                # accumulates hundreds of people's institutions and citation counts:
                # it both fabricates an absurd row and HIDES everyone inside it. In
                # testing that phantom swallowed 310 real people, one of whom was a
                # leading figure in the field. Fall back to the normalised name.
                aid = a["author"].get("id") or ("name:" + "|".join(_name_key(nm)))
                if aid in me or (not a["author"].get("id") and _name_key(nm) in me_names):
                    continue
                d = agg.setdefault(aid, {
                    "author_id": a["author"].get("id") or "", "name": nm,
                    "orcid": a["author"].get("orcid") or "",
                    "papers": set(), "citing": set(), "recent": set(),
                    "group_papers": set(), "group_citing": set(),
                    "institutions": set(), "topics": defaultdict(int),
                    "positions": set(), "years": set()})
                d["papers"].add(work_id)
                d["citing"].add(c["id"])
                if work_id in group_papers:
                    d["group_papers"].add(work_id)
                    d["group_citing"].add(c["id"])
                if yr >= start:
                    d["recent"].add(c["id"])
                d["years"].add(yr)
                d["positions"].add(a.get("author_position") or "")
                for i in a.get("institutions", []):
                    d["institutions"].add(i["display_name"])
                for t in (c.get("topics") or [])[:3]:
                    d["topics"][t["display_name"]] += 1

    rows = []
    for d in agg.values():
        rows.append({
            "author_id": d["author_id"], "name": d["name"], "orcid": d["orcid"],
            "n_group_papers_cited": len(d["group_papers"]),
            "n_group_citing_papers": len(d["group_citing"]),
            "n_papers_cited": len(d["papers"]),
            "n_citing_papers": len(d["citing"]),
            "n_recent_citing_papers": len(d["recent"]),
            "last_citing_year": max(d["years"]) if d["years"] else "",
            # Senior = first OR last. A PI is first author on their own reviews and on
            # much theory work, so last-only understates the people most worth having.
            "senior_author_share": round(
                sum(1 for p in d["positions"] if p in ("last", "first"))
                / max(1, len(d["positions"])), 2),
            "institutions": "; ".join(sorted(d["institutions"])[:3]),
            "n_institutions": len(d["institutions"]),
            "top_topics": "; ".join(t for t, _ in sorted(d["topics"].items(),
                                                         key=lambda x: -x[1])[:6]),
            "prior_coauthor_years": ",".join(
                str(y) for y in sorted(x for x in coauthor_years.get(d["author_id"], ()) if x)),
            "is_recent_coauthor": d["author_id"] in collab,
            # Name the affiliation that triggered a same-institution exclusion. The
            # institutions column shows only the first three alphabetically, so without
            # this a correct exclusion can look like a bug.
            "matched_home_institution": "; ".join(sorted(
                {i for i in d["institutions"] for h in home if h in i.lower()})),
            "is_home_institution": any(h in i.lower() for i in d["institutions"] for h in home),
        })

    manual = read_manual_exclusions()
    apply_coauthor = CFG["exclusions"]["exclude_recent_coauthors"] and not args.include_coauthors
    for r in rows:
        why = []
        if r["is_recent_coauthor"] and apply_coauthor:
            why.append(f"co-author since {start}")
        if r["is_home_institution"]:
            why.append("same institution")
        m = manual.get(_name_key(r["name"]))
        r["is_manual_exclusion"] = bool(m)
        if m:
            why.append(m)
        r["exclusion_reason"] = "; ".join(why)

    def addrank(field, col):
        for i, r in enumerate(sorted(rows, key=lambda x: -x[field]), 1):
            r[col] = i
    addrank("n_group_papers_cited", "rank_group")
    addrank("n_papers_cited", "rank_breadth")
    addrank("n_citing_papers", "rank_volume")
    addrank("n_recent_citing_papers", "rank_recent")
    for r in rows:
        r["rank_combined"] = round((r["rank_breadth"] + r["rank_volume"] + r["rank_recent"]) / 3, 1)
    rows.sort(key=lambda r: (-r["n_group_papers_cited"], -r["n_group_citing_papers"],
                             r["rank_combined"], -r["n_papers_cited"]))
    for i, r in enumerate(rows, 1):
        r["rank_final"] = i

    cols = ["rank_final", "rank_group", "rank_combined", "rank_breadth", "rank_volume",
            "rank_recent", "name", "n_group_papers_cited", "n_group_citing_papers",
            "n_papers_cited", "n_citing_papers", "n_recent_citing_papers",
            "last_citing_year", "senior_author_share", "institutions", "n_institutions",
            "top_topics", "prior_coauthor_years", "exclusion_reason", "is_recent_coauthor",
            "is_home_institution", "matched_home_institution", "is_manual_exclusion",
            "orcid", "author_id"]

    def write(path, data):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(data)
        return path

    top = args.top or CFG["ranking"]["top"]
    write(os.path.join(DATA, "candidates_ranked.csv"), rows)
    write(os.path.join(DATA, "shortlist_to_verify.csv"),
          [r for r in rows if not r["exclusion_reason"]][:top])
    write(os.path.join(DATA, "excluded.csv"),
          sorted([r for r in rows if r["exclusion_reason"]], key=lambda r: -r["n_citing_papers"]))

    n_co = sum(1 for r in rows if r["is_recent_coauthor"])
    n_home = sum(1 for r in rows if r["is_home_institution"])
    excl = sum(1 for r in rows if r["exclusion_reason"])
    print(f"candidates: {len(rows)}   excluded: {excl}")
    print(f"  recent co-authors: {n_co} "
          f"({'excluded' if apply_coauthor else 'KEPT — co-author filter off'})")
    print(f"  same institution : {n_home} (always excluded)")
    print(f"wrote data/candidates_ranked.csv, data/shortlist_to_verify.csv (top {top}), "
          f"data/excluded.csv")


STOP = set("""the a an and or of in on for to with by from as at is are was were be been
this that these those we our their its it he she they which who whom whose what when where
how why not no nor but if then than so such can could may might will would shall should must
using used use based both each other others more most some any all very much many few also
into over under between within without during before after above below across through here
there about against among along around because being does did done doing due either else
enough even ever every further had has have having however just least less like likely made
make making meanwhile moreover much neither never nevertheless next none only onto otherwise
out perhaps rather same several since still therefore thus too toward towards upon via well
whether while yet""".split())


def _words(text):
    return [w for w in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", (text or "").lower())
            if w not in STOP]


def _read_manuscript(path):
    """Return (full_text, [(section_title, section_text), ...])."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        import zipfile
        with zipfile.ZipFile(path) as z:
            text = re.sub(r"<[^>]+>", " ", z.read("word/document.xml").decode("utf8", "ignore"))
    else:
        text = open(path, encoding="utf8", errors="ignore").read()
    secs = []
    if ext == ".tex":
        text = re.sub(r"(?<!\\)%.*", "", text)              # strip LaTeX comments
        parts = re.split(r"\\(?:sub)*section\*?\{([^}]*)\}", text)
        if len(parts) > 1:
            secs = [("preamble/abstract", parts[0])]
            secs += [(parts[i], parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
    if not secs:
        secs = [(f"block {i+1}", c) for i, c in
                enumerate(c for c in re.split(r"\n\s*\n", text) if len(c.strip()) > 200)]
    return text, secs


def _bib_people(bib_paths):
    """(surname, forename) pairs from the author FIELDS of .bib entries.

    Brace-matched, not regex-scraped over the whole file. Scraping capitalised words
    from titles and cite keys matches on surname alone and reports the WRONG people as
    already cited — one test skipped a candidate because an unrelated person shared his
    surname, and another because a cite key happened to contain it.
    """
    people = []
    for b in bib_paths:
        try:
            raw = open(b, encoding="utf8", errors="ignore").read()
        except OSError:
            continue
        for m in re.finditer(r"\bauthor\s*=\s*\{", raw, re.I):
            i, d = m.end(), 1
            while d and i < len(raw):
                d += (raw[i] == "{") - (raw[i] == "}")
                i += 1
            for a in re.split(r"\s+and\s+", raw[m.end():i - 1]):
                a = " ".join(a.split())
                if not a:
                    continue
                if "," in a:
                    sur, _, fore = a.partition(",")
                else:
                    t = a.split()
                    sur, fore = (t[-1], " ".join(t[:-1])) if t else ("", "")
                if _norm_name(sur):
                    people.append((_norm_name(sur), _norm_name(fore)))
    return people


def suggest(args):
    """Which ranked candidates does this manuscript not cite, and where could they go?"""
    rows = [r for r in csv.DictReader(open(os.path.join(DATA, "candidates_ranked.csv")))]
    if args.include_coauthors:
        # For a PAPER (as opposed to a referee list) citing a close collaborator is
        # normal and often right, so the co-author exclusion is dropped here on request.
        rows = [r for r in rows
                if not [x for x in r["exclusion_reason"].split("; ")
                        if x and not x.startswith("co-author since")]]
    else:
        rows = [r for r in rows if not r["exclusion_reason"]]
    if args.shortlist:
        # Check your VERIFIED list, not a rank window. A --top cutoff silently drops
        # verified candidates below it; in testing it missed 16 of 24 genuine gaps.
        want = {_norm_name(r["name"]) for r in csv.DictReader(open(args.shortlist))}
        rows = [r for r in rows if _norm_name(r["name"]) in want]
        print(f"  checking {len(rows)} verified candidates from {os.path.basename(args.shortlist)}")
    else:
        rows = rows[: args.top]

    citing = json.load(open(os.path.join(DATA, "citing_works.json")))
    papers = defaultdict(list)
    for lst in citing.values():
        for c in lst:
            for a in c.get("authorships", []):
                papers[a["author"].get("id") or
                       ("name:" + "|".join(_name_key(a["author"].get("display_name") or "")))
                       ].append({
                    "title": c.get("title") or "",
                    "doi": (c.get("doi") or "").replace("https://doi.org/", "").lower(),
                    "year": c.get("publication_year") or 0,
                    "pos": a.get("author_position"),
                    "topics": [t["display_name"] for t in (c.get("topics") or [])[:3]],
                    "authors": [x["author"].get("display_name", "")
                                for x in (c.get("authorships") or [])]})

    text, secs = _read_manuscript(args.manuscript)
    bibs = args.bib or []
    blob = text + "".join("\n" + open(b, encoding="utf8", errors="ignore").read()
                          for b in bibs if os.path.exists(b))
    cited_dois = {d.rstrip(".").lower() for d in re.findall(r"10\.\d{4,9}/[^\s,;}\)\"']+", blob)}
    cited_people = _bib_people(bibs)
    sec_words = [(t, set(_words(b))) for t, b in secs]

    out = []
    for r in rows:
        key = r["author_id"] or ("name:" + "|".join(_name_key(r["name"])))
        mine = papers.get(key, [])
        if any(p["doi"] and p["doi"] in cited_dois for p in mine):
            continue
        if any(_same_person(r["name"], s, f) for s, f in cited_people):
            continue
        best, best_score, best_sec = None, 0.0, None
        for p in mine:
            # OpenAlex merges common names, so a high rank can rest on somebody else's
            # papers. Keep only papers whose own author list contains this candidate.
            if p["authors"] and not any(_same_person(r["name"], *_split_name(a))
                                        for a in p["authors"]):
                continue
            pw = set(_words(p["title"] + " " + " ".join(p["topics"])))
            if not pw:
                continue
            for title, sw in sec_words:
                if not sw:
                    continue
                ov = pw & sw
                score = len(ov) / (len(pw) ** 0.5)
                score *= 1.25 if p["pos"] in ("last", "first") else 1.0
                # Prefer the version of record: preprint servers mint their own DOIs, so
                # a paper can appear twice and the preprint outscore its published self.
                if p["doi"].startswith(("10.1101/", "10.21203/", "10.26434/", "10.48550/")):
                    score *= 0.5
                score *= 1.0 + min(p["year"], 2100) / 20000.0
                if score > best_score:
                    best, best_score, best_sec = p, score, (title, sorted(ov)[:6])
        base = {"name": r["name"], "rank_final": r["rank_final"],
                "institutions": r["institutions"],
                "recent_coauthor": r["is_recent_coauthor"]}
        if not best or best_score < args.min_score:
            out.append({**base, "suggestion": "", "doi": "", "section": "",
                        "shared_terms": "", "also_covers": "",
                        "note": "no defensible placement found — do not force a citation"})
        else:
            out.append({**base,
                        "suggestion": " ".join((best["title"] or "").split()),
                        "doi": best["doi"],
                        "section": " ".join(best_sec[0].split())[:70],
                        "shared_terms": ", ".join(best_sec[1]),
                        "also_covers": "",
                        "note": f"score {best_score:.2f}" +
                                (f"; senior author ({best['pos']})"
                                 if best["pos"] in ("last", "first") else "")})

    per_doi = defaultdict(list)
    for o in out:
        if o["doi"]:
            per_doi[o["doi"]].append(o["name"])
    for o in out:
        if o["doi"] and len(per_doi[o["doi"]]) > 1:
            o["also_covers"] = "; ".join(n for n in per_doi[o["doi"]] if n != o["name"])

    dest = args.out or os.path.join(HERE, "citation_gaps.csv")
    cols = ["name", "rank_final", "institutions", "recent_coauthor", "suggestion", "doi",
            "section", "shared_terms", "also_covers", "note"]
    with open(dest, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    placed = sum(1 for o in out if o["doi"])
    print(f"{len(rows)} candidates checked against {os.path.basename(args.manuscript)}")
    print(f"  not cited: {len(out)}   with a defensible placement: {placed}")
    print(f"wrote {dest}")
    for o in out[:12]:
        if o["doi"]:
            print(f"  · {o['name']} -> {o['section']}  [{o['shared_terms']}]")
            print(f"      {o['suggestion'][:88]}  doi:{o['doi']}")


def main():
    global CFG
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None, help="path to config.toml / config.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("harvest", help="pull your works + citing works from OpenAlex")
    h.add_argument("--source", choices=["dois", "orcid"], default="dois")
    h.add_argument("--full", action="store_true",
                   help="ignore the last-run timestamp and re-read every citation")
    h.set_defaults(func=harvest)

    r = sub.add_parser("rank", help="aggregate and rank citing authors")
    r.add_argument("--top", type=int, default=None)
    r.add_argument("--include-coauthors", action="store_true",
                   help="do NOT exclude recent co-authors. Off for referee lists; useful "
                        "when you want the full picture of who engages with your work.")
    r.add_argument("--group-includes-first", action="store_true",
                   help="also count your FIRST-author papers as group papers")
    r.set_defaults(func=rank)

    s = sub.add_parser("suggest", help="which candidates does a manuscript not cite?")
    s.add_argument("manuscript", help=".tex, .md, .txt or .docx")
    s.add_argument("--bib", nargs="*", default=None)
    s.add_argument("--top", type=int, default=30)
    s.add_argument("--shortlist", default=None,
                   help="CSV of verified candidates; overrides --top and is preferred")
    s.add_argument("--include-coauthors", action="store_true",
                   help="include recent co-authors. For a PAPER this is usually what you "
                        "want — citing close collaborators is normal and often correct.")
    s.add_argument("--min-score", type=float, default=1.0)
    s.add_argument("--out", default=None)
    s.set_defaults(func=suggest)

    st = sub.add_parser("status", help="when did the last run happen")
    st.set_defaults(func=lambda a: print(json.dumps(load_state(), indent=1)))

    a = sub.add_parser("all", help="harvest then rank")
    a.add_argument("--top", type=int, default=None)
    a.add_argument("--source", choices=["dois", "orcid"], default="dois")
    a.add_argument("--full", action="store_true")
    a.add_argument("--include-coauthors", action="store_true")
    a.add_argument("--group-includes-first", action="store_true")
    a.set_defaults(func=lambda args: (harvest(args), rank(args)))

    args = ap.parse_args()
    CFG = load_config(args.config)
    args.func(args)


if __name__ == "__main__":
    main()
