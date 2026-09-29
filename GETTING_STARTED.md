# Getting started — no programming required

This guide assumes you have never opened a terminal and do not intend to start now. You
will use an AI assistant (Claude, ChatGPT, Copilot, Gemini — any of them that can run
code or edit files on your computer) and it will do the work. Your job is to supply your
CV and answer three questions.

Total time: about fifteen minutes, most of it waiting.

---

## What you will get out of it

**A ranked list of people who could review your papers and grants.** They are ranked by
how much of your work they cite, with the people who cite the papers *you led* at the
top. Each row gives their institution, their research topics, and the most recent paper
of theirs that cites you. People you cannot propose — recent co-authors, your own
colleagues, anyone you name as a conflict — are removed to a separate file that records
*why* each one went.

**A list of people your next paper or grant fails to cite.** Give it your manuscript and
its bibliography and it tells you which of those same researchers are missing from your
reference list, which of their papers is the relevant one, and which section of your
draft it belongs in. Referees notice when they are missing from a reference list. This is
the part most people end up using every week.

**A picture of who is reading your work.** With one setting changed, the same ranking
includes your collaborators and becomes a map of your research community — useful for
organising a session, inviting authors to a special issue, or suggesting external
letter writers.

**Something you can re-run.** Each run remembers when it happened and asks only for what
is new, so monthly updates take a minute.

---

## Step 1 — Get a free API key (2 minutes)

The tool reads [OpenAlex](https://openalex.org), an open database of papers and
citations. It is free, but it needs a key.

Go to **https://openalex.org**, request an API key, and keep the email it sends you. It
is a string of letters and numbers. You will paste it once.

## Step 2 — Make a folder and put your CV in it

Make a new folder anywhere — call it `referees`. Inside it, put:

- your **CV** (PDF, Word, whatever you have), and/or
- your **publication list** — a Word file, a text file, a PDF, even a screenshot-free
  copy-paste from Google Scholar.

Either is enough. Both is better. The assistant will read them and extract your DOIs
(the `10.xxxx/...` identifiers that uniquely name each paper).

You do not need to clean the file up. Do not reformat anything.

## Step 3 — Know your ORCID

Your ORCID looks like `0000-0002-1825-0097`. If you do not have one, get one at
**https://orcid.org** — it takes two minutes and you will need it for the rest of your
career anyway.

## Step 4 — Ask the assistant to do it

Open your AI assistant *in that folder* (in VS Code with Claude Code or Copilot, in
Cursor, or in any assistant that can work with local files). Paste this, replacing the
three bracketed items:

> Please set up the referee-finder tool for me.
>
> 1. Clone `https://github.com/roybeckbarkai/referee-finder.git` into this folder.
> 2. Read its `README.md` and `CLAUDE.md` first — `CLAUDE.md` tells you exactly how to
>    set it up and what the traps are.
> 3. My CV and publication list are in this folder. Extract every DOI of my own papers
>    from them and write them to `data/author_dois.txt`, one per line. Tell me how many
>    you found and show me the list so I can check it against my CV.
> 4. My ORCID is `<YOUR ORCID>`. My institution is `<YOUR INSTITUTION>`. Copy
>    `config.example.toml` to `config.toml` and fill those in.
> 5. My OpenAlex API key is in the `OPENALEX_API_KEY` environment variable — ask me if
>    it is not set.
> 6. Then run `python3 referee_finder.py all` and show me the top 30 candidates in a
>    readable table.
>
> Ask me before guessing anything. Do not invent DOIs, email addresses or affiliations.

The assistant will ask you a couple of things (does this DOI list look right? is this
your institution's name as it appears on papers?). Answer them. Then it will run for
five to twenty minutes depending on how much you have published.

## Step 5 — Read the shortlist, and check it yourself

You will get `data/shortlist_to_verify.csv`. The name is not decoration.

**The tool cannot tell a professor from their own postdoc.** Citation counts do not
distinguish them, and students appear on every paper alongside their supervisors. In one
real test round, 15 of 22 fresh candidates turned out to be group members of people
already on the list. For each name you intend to propose, open their current
institutional page and confirm they are an independent group leader, the affiliation is
current, and you have no conflict with them.

Then ask the assistant:

> Go through `data/shortlist_to_verify.csv`. For each person, find their official
> institutional page and tell me: are they an independent PI with their own group? Is
> the affiliation current? Is there an email address shown on that page? Do not
> construct an email from their name — only report one you actually see. Leave it blank
> otherwise. Put the results in a table and flag anyone who looks like a student,
> postdoc or emeritus without an active group.

Keep the names that survive in a file of your own — `my_verified_referees.csv`. That is
the list you will reuse.

## Step 6 — Check a manuscript before you submit it

This is the part you will come back to. With your manuscript and bibliography in the
folder:

> Run `python3 referee_finder.py suggest my_paper.tex --bib refs.bib --shortlist
> my_verified_referees.csv --include-coauthors` and show me the results. For each gap,
> tell me whether the suggested paper genuinely belongs in that section — do not
> recommend a citation that is not warranted.

You get a table: who is missing, which of their papers is the relevant one, where in
your draft it fits, and the terms the two have in common. Where two people share one
relevant paper, it says so — one citation can close both gaps.

Add the ones that genuinely belong. Ignore the rest. A padded reference list is worse
than an incomplete one, and a referee can tell.

---

## The one setting worth understanding

Funders and journals normally bar anyone you have published with in the last three to
five years from reviewing your work. The tool applies a five-year rule by default, and
for a **referee list** that is what you want.

**For a paper's reference list it is the wrong rule, which is why it can be switched
off.** Citing your close collaborators is normal, usually correct, and rarely questioned
— reference lists are not screened for co-authorship the way referee nominations are.
So when you are looking for citation gaps, add `--include-coauthors` (as in Step 6
above) and you will see the collaborators your draft has overlooked. That is often where
the real gaps are.

The same applies when you are not choosing referees at all — mapping your field,
picking speakers, suggesting letter writers. Turn it off; it has no bearing.

To change the window itself (some funders say three years, some say ten), edit
`coauthor_window_years` in `config.toml`. Set it to `0` to switch the rule off
everywhere.

---

## Things that go wrong, and what they mean

**"Only 40 of my 90 papers were found."** Your DOI list has typos, or OpenAlex has
genuinely not indexed some of them. Ask the assistant to list the DOIs that did not
resolve and check them by hand at `https://doi.org/<the doi>`.

**"The top of my list is full of people from a field I do not work in."** OpenAlex has
merged a namesake into your record, and you are harvesting by ORCID rather than by DOI
list. Use the DOI list — this is exactly why it is the default.

**"Someone was excluded for being at my institution, but they are not."** Your
`home_institutions` entry is matching too broadly. The `matched_home_institution` column
in `data/excluded.csv` names the affiliation that triggered it, so you can see which
string is at fault. Make the entry more specific.

**"Someone I have never met was excluded as a co-author."** Check
`prior_coauthor_years`. Large consortium papers make co-authors of hundreds of people.

**"A name in the list looks absurd — hundreds of institutions."** Report it. That
pattern indicates the name-matching has merged distinct people, and it hides everyone
inside it. A bug of exactly this kind was found once already, by a user reading a row
that did not make sense.

**It asks for your key every time.** The key lives in an environment variable. Ask your
assistant to add `export OPENALEX_API_KEY=...` to your shell profile so it persists.

---

## Where to go next

`README.md` has the full command reference, the ranking method, and the reasoning behind
each default. `CLAUDE.md` is written for the AI assistant rather than for you, but it is
short and it lists the traps.
