# Notes for an AI assistant driving this tool

You are probably here because a researcher asked you to set up referee-finder for them.
They may not be a programmer. Read this before touching anything; it is short, and every
warning in it comes from a real failure.

## Ground rule

**Never invent bibliographic or contact data.** No DOI you have not seen in their
documents, no email constructed from a name and an institution's domain, no affiliation
inferred from a surname, no "probably at" anything. Empty is correct; plausible is not.
If a page does not load, say so — do not substitute a search-engine snippet for a page
you could not read, and if you do rely on snippets, say that is what you did.

## Setup, in order

1. `pip` installs nothing — standard library, Python 3.11+. On 3.10 or older, convert
   `config.example.toml` to `config.json` (same keys) because `tomllib` will be missing.
2. `OPENALEX_API_KEY` must be set. Keyless calls fail with 409/429. Do not retry
   keylessly; ask the user for their key.
3. Copy `config.example.toml` → `config.toml`. Fill in `author.orcid`, `author.name`,
   `exclusions.home_institutions`.
4. Build `data/author_dois.txt` from their CV or publication list.
5. `python3 referee_finder.py all`

## Building the DOI list — the step that decides everything

Extract DOIs from their CV or publication list. Then **show them the count and the list
and ask them to check it against their CV.** A missing paper is a missing community.

- Bare DOIs, one per line, no `https://doi.org/` prefix, lowercase.
- Strip tracking junk. Copied DOIs frequently carry `?utm_source=...` or
  `?sharing_token=...` appended; these produce 404s and the paper silently vanishes.
  Two of 79 in one real CV had this.
- Preprints of papers that are also published are duplicates. Put them below the
  `#PREPRINTS` marker, which `harvest` stops at.
- If a DOI does not resolve in OpenAlex, do not fix it by guessing. Check
  `https://doi.org/<doi>` and ask.
- Do **not** offer to skip this step and harvest by ORCID instead. OpenAlex merges
  namesakes: on one real record it had folded two unrelated researchers sharing a
  surname into one ORCID, adding 60 works that were not theirs and pulling people from a
  field the author had never worked in into the candidate list. If the
  user has no publication list at all, `--source orcid` is the fallback — then check
  `data/author_works.json` with them and confirm every title is actually theirs.

## `home_institutions` — get this right or exclusions look like bugs

Lowercase substrings matched against affiliation strings. Include former names of the
institution, the attached hospital or medical school, and any institute formally part of
it. Keep entries distinctive: `york university` also matches `New York University`.

When a user says "this person was excluded as same-institution but they are not",
look at `matched_home_institution` in `data/excluded.csv` — it names the affiliation
that fired. Usually the entry is too broad. Occasionally it is a genuine second
affiliation the user did not know about.

## The co-author rule is a switch, not a law

`exclusions.exclude_recent_coauthors` (default true, five years) is right for referee
nominations and wrong for almost everything else.

- **Referee list** → leave it on. Set `coauthor_window_years` to what the target funder
  or journal actually requires.
- **Citation gaps in a paper** → pass `--include-coauthors` to `suggest`. Citing close
  collaborators in a paper is normal and rarely questioned; reference lists are not
  screened for co-authorship the way referee nominations are. Recommend this.
- **Mapping a field, speakers, letter writers** → `rank --include-coauthors`.

Kept co-authors stay flagged (`recent_coauthor`, `prior_coauthor_years`). Surface the
flag in anything you show the user; do not hide it because the filter is off.

## Verification — do not skip, do not fake

The shortlist is unverified by construction. When asked to verify candidates:

- Confirm from a **current institutional page** that the person is an independent PI
  with an active group. Emeritus without a group, staff scientist, senior postdoc → out.
  The single largest error class is group members of people already on the list: in one
  test round 15 of 22 fresh candidates were postdocs or students in the labs of
  candidates ranked above them.
- **Emails only from a page or record that actually shows one.** Matching a surname and
  initial against a literature database returns the wrong person often enough to be
  useless — it did, repeatedly, in testing. Matching within the candidate's *own* papers
  works. And an address that turns up for more than one candidate is the corresponding
  author's, not theirs; drop it.
- If a rendered page mangles an address, leave it empty. Do not reconstruct it.
- Record the page URL you used, and say plainly if you could only see a search snippet
  rather than the page itself.

## Reading the output

| file | use |
|---|---|
| `data/candidates_ranked.csv` | everything, with flags |
| `data/shortlist_to_verify.csv` | top N after exclusions — the working list |
| `data/excluded.csv` | who was removed and why |

Sorted by group papers cited (the user's last-author work) first, then a combined
breadth/volume/recency rank. `senior_author_share` near 1.0 suggests a PI; near 0
suggests a student. `n_institutions` far above 3 on one person means name-merging —
treat that row as suspect and tell the user.

## `suggest`

```
python3 referee_finder.py suggest paper.tex --bib refs.bib --shortlist verified.csv --include-coauthors
```

Prefer `--shortlist` over `--top`. A rank cutoff drops verified people below it; in
testing `--top 30` missed 16 of 24 real gaps.

Then **read the suggestions before passing them on.** The match is lexical overlap
between a candidate's paper and a section of the manuscript. Your job is to judge
whether the citation is warranted, in that section, on the merits. Rows with an empty
suggestion mean no defensible placement was found — say so and stop. Never advise
padding a reference list; a referee can tell, and it costs more than the omission did.

Check `also_covers`: one citation often closes several gaps.

## Privacy

`data/` holds the user's publication list, collaboration network, conflict list and
third-party contact details; `config.toml` holds their identity. Both are git-ignored
and must stay so. Never commit them, never paste them into an issue, never include them
in a shared artifact. If the user wants to share the tool, they share the repo, not
their working directory.

## If you are modifying the code

The comments in `referee_finder.py` marked with reasoning ("in testing…", "WARNING")
document bugs that were found the hard way. Two in particular:

- Roughly 4% of OpenAlex authorship records have **no author id**. Keying aggregation on
  that falsy id collapses them into one phantom author that swallows hundreds of real
  people — 310 in the case that exposed it, including a leading figure in the field, and
  it inherits all their institutions so it also trips the same-institution exclusion. The
  fallback to a normalised name key is load-bearing.
- `.bib` author extraction is brace-matched on the `author = {...}` field. A regex over
  the whole file matches surnames appearing in titles and cite keys and reports the wrong
  people as already cited.
