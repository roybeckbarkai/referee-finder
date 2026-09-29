# referee-finder

Find candidate referees for your papers and grants from the people who actually read
your work — and find which of them your next manuscript forgets to cite.

The premise is simple. The researchers best placed to review your work are the ones who
cite it, and the ones who cite the papers *you led* are better placed still. Those people
are all in the open citation graph. This tool pulls them out, removes the ones you cannot
propose, ranks the rest, and hands you a shortlist to check by hand.

**New here? Read [GETTING_STARTED.md](GETTING_STARTED.md) instead** — it assumes no
command line and no programming, and walks you through asking an AI assistant to do the
whole thing for you.

Python 3.11+, standard library only. No installation. One free API key.

---

## What it can do

**1. Rank potential referees.** Every author who has ever cited you, scored on how much
of your work they cite, how many of *your group's* papers they cite, how recently, and
whether they cite you as a senior author. You get a ranked table with institutions,
research topics, their latest paper citing you, and a shortlist sized for hand-checking.

**2. Filter out the people you cannot propose.** Recent co-authors, everyone at your own
institution, and a hand-written list of conflicts the citation graph cannot see (grant
partners, your PhD supervisor, a pending proposal). Every exclusion is written to a
separate file with its reason, so you can audit the decision instead of trusting it.

**3. Find reference gaps in a paper or grant.** Point it at a manuscript and its
bibliography and it reports which ranked candidates you do not cite — and for each one,
their most relevant paper, the section of your manuscript where it fits, and the
terms the two share. This is the most immediately useful mode: a reference list that
covers the people likely to review it is a reference list that argues for itself.

**4. Map your field.** Turn the co-author filter off and the same ranking becomes a
picture of who engages with your work, collaborators included — useful for choosing a
session to organise, a special issue's authors, or a hiring committee's external letters.

**5. Stay current.** Re-run it any time. Harvesting is incremental: it records when it
last ran and asks only for citations added since, so a monthly update takes a minute
rather than an hour.

## What it does not do

It does not decide anything for you, and it does not guess. It never invents an email
address from a name and a domain, never infers an affiliation, and leaves a field empty
rather than filling it with something plausible. **The shortlist is a starting point for
your own verification, not a list to paste into a submission form** — see
[Verifying the shortlist](#verifying-the-shortlist).

---

## Setup

### 1. Get an OpenAlex API key

[OpenAlex](https://openalex.org) is the open bibliographic database this runs on. It is
free; keyless requests are rejected.

```bash
export OPENALEX_API_KEY=your_key_here
```

### 2. Configure

```bash
cp config.example.toml config.toml
```

Edit `config.toml`: your ORCID, your name, and — importantly — your institution's name
under `home_institutions`, so that colleagues who could review for you anyway are
dropped.

### 3. Build your DOI list

Put one DOI per line in `data/author_dois.txt` (see `data/author_dois.txt.example`).
Easiest route: drop your CV into `input/` and ask an AI assistant to extract the DOIs.
Then check the count against your CV.

### Why a DOI list, and not just your ORCID

The tool can harvest from your OpenAlex author record (`--source orcid`), but it defaults
to your own list of DOIs, because author disambiguation fails in ways that quietly ruin
the output. In testing on a real record, OpenAlex had merged two unrelated researchers
who shared a surname — a radio astronomer and a 1970s condensed-matter physicist — into
one ORCID. That added 60 works that were not the author's, and pulled that unrelated
field into the topic mix and the candidate list.

Your CV is the authoritative record of what you wrote. Check your OpenAlex record once;
if it is clean, `--source orcid` saves you the trouble.

---

## Running it

```bash
python3 referee_finder.py all          # harvest, then rank
python3 referee_finder.py status       # when did this last run, what did it see
```

Results land in `data/`:

| file | what it is |
|---|---|
| `candidates_ranked.csv` | every citing author, ranked, with exclusion flags |
| `shortlist_to_verify.csv` | top N after exclusions — **this is your working list** |
| `excluded.csv` | everyone removed, each with the reason |

### Finding reference gaps

```bash
python3 referee_finder.py suggest paper.tex --bib refs.bib
python3 referee_finder.py suggest grant.docx --bib refs.bib --include-coauthors
```

Accepts `.tex`, `.md`, `.txt`, `.docx`. For LaTeX it splits on `\section`, so the
"where does this fit" column names a real section of your manuscript. Output is
`citation_gaps.csv`.

Once you have verified a shortlist, check against *that* rather than a rank window:

```bash
python3 referee_finder.py suggest paper.tex --bib refs.bib --shortlist my_verified.csv
```

A `--top 30` cutoff silently skips verified people who rank below it. In testing that
missed 16 of 24 genuine gaps.

Where two candidates share one relevant paper, the `also_covers` column says so — one
added citation can close several gaps at once. Where no honest placement exists, the row
says so and suggests nothing. Do not force a citation to satisfy a table.

---

## Turning the co-author rule off

Most funders and journals bar anyone you have published with in the last three to five
years from reviewing your work. That rule is on by default (`exclude_recent_coauthors`,
five years) — for a referee list you want it.

**It is not the right default everywhere, and it is a config switch, not a law.**

*Writing a paper.* Citing your close collaborators is normal, often correct, and rarely
questioned: reference lists are not screened for co-authorship the way referee
nominations are. Use `suggest --include-coauthors` and you will see the collaborators
your draft has overlooked, which is frequently where the real gaps are.

*Mapping a field, or picking speakers, panellists or letter writers.* The rule has no
bearing at all. Use `rank --include-coauthors`.

*Different funder, different window.* Set `coauthor_window_years` to whatever your target
actually requires — three, five, ten. Setting it to `0` disables the filter.

Candidates kept by `--include-coauthors` are still flagged (`recent_coauthor`,
`prior_coauthor_years`), so you always know who they are. The window is calculated in
whole calendar years: five years in 2026 means publications from 2022 onward.

---

## How the ranking works

Candidates are sorted first by how many of **your group's papers** they cite — the ones
where you are last author — then by a combined rank over three measures:

- **breadth** — how many distinct papers of yours they cite
- **volume** — how many papers they have written that cite you
- **recency** — how many of those fall inside the co-author window

Group-first ordering is the change that matters most. Sorting by raw citation count puts
whoever belongs to the biggest consortium on top. Sorting by engagement with the work you
led surfaces the people who actually follow your line of research. In testing it replaced
most of the top twenty and brought forward an entire sub-community that raw counts had
buried under large multi-author collaborations.

Also reported per candidate: `senior_author_share` (how often they appear as first or
last author — a proxy for being a PI rather than a student), `n_institutions`,
`last_citing_year`, and their top research topics.

### Verifying the shortlist

**Do this. The ranking cannot.** For each name on the shortlist, confirm from a current
institutional page that they are an independent PI with an active group, that the
affiliation is current, and that they have no conflict with you. Take the email address
only from a page that actually shows it.

Two failure modes to watch for. Citation counts do not distinguish a professor from their
own postdoc, and students appear alongside their supervisors on every paper — in one
test round, 15 of 22 candidates turned out to be group members of people already on the
list. And where an email is concerned, an address that appears for more than one
candidate is the *corresponding author's* address, not theirs.

Keep your verified list as its own CSV and feed it back with `--shortlist`.

---

## Keeping it up to date

`harvest` records the date of each successful run in `data/state.json` and then asks
OpenAlex only for citing records created since. Newly added papers of your own are
detected and fully harvested the first time they appear. Use `--full` to force a complete
re-read — worth doing occasionally, since OpenAlex backfills.

A sensible rhythm: `all` monthly, `--full` twice a year, and `suggest` before every
submission.

---

## Privacy

`data/` holds your publication list, your collaboration network, your conflict list and
third-party contact details. It is git-ignored and must stay that way. `config.toml` is
git-ignored too. Before sharing a shortlist outside your group, remember it contains
other people's names, affiliations and sometimes emails, gathered for your internal
decision.

## Limitations

- OpenAlex coverage is good but not complete, and its author disambiguation both merges
  distinct people and splits single ones. Roughly 4% of authorship records carry no
  author id at all; those are matched by name instead, which is imperfect in both
  directions.
- Citation counts measure attention, not suitability. A prolific citer may be a
  competitor, a former student, or someone who cites everything.
- The tool has no view of grant panels, editorial boards, institutional ties beyond
  affiliation strings, or personal history. That is what
  `data/manual_exclusions.txt` is for.
- `suggest` matches on shared vocabulary between a candidate's paper and a section of
  yours. It proposes; it cannot tell you whether a citation is warranted.

## License

MIT.
