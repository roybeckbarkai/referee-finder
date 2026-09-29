# referee-finder in Claude Science: the full route, step by step

Nine prompts, in order. Paste each one, read what comes back, then move on. You never
touch a terminal and you never write code. Total time is roughly an hour, most of it
waiting during step 5.

**The prompts below are written out in full, as a worked example.** They are filled in
for a fictional researcher, Dana Levi, a chemist at the University of Copenhagen with
ORCID `0000-0002-1825-0097`. Swap in your own ORCID, your own institution and your own
conflicts wherever hers appear. Everything else you can paste exactly as it stands.

At the end you will have:

- `referees_shortlist.md` and `.csv`: your verified candidate referees, split into two
  tiers, each with position, institution, official page, email where one genuinely
  exists, research keywords, techniques, and the most recent paper of theirs that cites
  you.
- `referees_excluded.md`: everyone dropped, with the reason, so you can argue with it.
- `citation_gaps.csv`: which of those people your current draft fails to cite, and
  where each one would go.

**What the assistant is doing and what it is not.** The tool itself is plain Python with
no LLM inside it: it queries OpenAlex, aggregates and sorts. The assistant does the
three jobs the tool cannot: reading your CV, reading institutional web pages, and
judging. Step 5 is entirely assistant work and it is the step that decides whether the
output is any good.

---

## Step 0. One-time setup

Left sidebar, **Customize** → **Credentials** → **Add Credential**. Choose OpenAlex and
paste a free key from https://openalex.org. You do this once, ever.

Then start a new session and **attach your CV** to your first message.

---

## Step 1. Get the tool and build your publication list

> Download `referee_finder.py` and `config.example.toml` from
> `https://raw.githubusercontent.com/roybeckbarkai/referee-finder/main/`, and read
> `CLAUDE.md` from the same place before doing anything else: it is written for you and
> it lists the traps. Use a plain HTTP fetch, not `git clone`, which does not work in
> this sandbox.
>
> My CV is attached. Extract every DOI of my own papers into `data/author_dois.txt`, one
> bare DOI per line, no `https://doi.org/` prefix. Strip any tracking parameters, so
> everything from a `?` onwards. Put preprints of papers that are also published below a
> `#PREPRINTS` line rather than deleting them.
>
> Then show me the count and the full list so I can check it against my CV before
> anything runs. Tell me about any entry in my CV you could not find a DOI for.

**Check this carefully.** The DOI list is the anchor for everything downstream. A
missing paper is a missing community. Count the lines against your CV yourself.

---

## Step 2. Tell it who you are and who you cannot propose

The example below is Dana's. Your conflicts will be different, and the reasons matter:
they get copied into the excluded file so you can defend each one later.

> Copy `config.example.toml` to `config.toml` and set:
>
> - `orcid` to `0000-0002-1825-0097`
> - `name` to `Dana Levi`
> - `home_institutions` to `["university of copenhagen", "københavns universitet",
>   "rigshospitalet"]`
>
> I have included the Danish name of the university and the university hospital,
> because affiliations are written both ways and the hospital is formally part of us.
> Tell me if you think I have missed a variant, or if any of those strings looks broad
> enough to match a different institution by accident.
>
> Then create `data/manual_exclusions.txt` with these, one per line, as
> `Surname, Forename   # reason`. These are conflicts the citation graph cannot see:
>
> ```
> Weiss, Daniel      # co-PI, Horizon grant 101098765
> Okonkwo, Amara     # partner on a pending Synergy proposal
> Tanaka, Hiroshi    # my PhD supervisor
> Brandt, Lise       # examiner on my student's defence, 2025
> ```
>
> Show me both files when you are done.

`home_institutions` matters more than it looks. It is a plain substring match, so
`york university` would also match `New York University`. Keep the entries distinctive,
and include former names, the attached hospital or medical school, and any institute
formally part of you.

---

## Step 3. Harvest and rank

> The OpenAlex key is in my stored credential, so declare it on the cells that need it.
> Run `python3 referee_finder.py all`.
>
> When it finishes, tell me: how many of my papers resolved in OpenAlex out of how many
> I gave you, the total citation count, how many citing authors were found, how many
> were excluded and under which rule, and how many of my papers count as group papers.
>
> Then show me the top 30 from `data/shortlist_to_verify.csv` as a readable table with
> name, institution, group papers cited, total papers cited, and top topics.

Five to twenty minutes depending on how much you have published. Re-runs later are
incremental and take about a minute.

The ranking sorts on your **last-author** papers first rather than raw citation count.
That is the design decision that matters: it surfaces the people following your line of
work instead of whoever happened to be on the biggest consortium paper.

---

## Step 4. Sanity checks before you trust any of it

> Before we verify anyone, run three checks on `data/candidates_ranked.csv` and report
> the results:
>
> 1. Any candidate whose `n_institutions` is far above 3. That pattern means OpenAlex
>    name-merging has fused several real people into one row, which both invents a
>    nonsense entry and hides everyone inside it.
> 2. Every row flagged `is_home_institution` should have a non-empty
>    `matched_home_institution`. Tell me if any are empty, and show me the distinct
>    matched strings so I can see whether my institution name is matching too broadly.
> 3. How many of my own papers failed to resolve in OpenAlex, and which ones.

Do not skip this. Both of the worst bugs found so far surfaced exactly here: one phantom
row that had absorbed 310 separate people, and an exclusion firing on the wrong
institution because the matched affiliation was invisible in the output.

---

## Step 5. Verify the shortlist

This is the long step and the one that decides the quality of everything else. The
ranking cannot tell a professor from their own postdoc, because citation counts do not
distinguish them and students appear on every paper alongside their supervisors. In one
round of this, 15 of 22 fresh candidates turned out to be group members of people
already on the list.

> Verify all 30 candidates in `data/shortlist_to_verify.csv`. Work through them in
> batches, or fan out sub-agents if you can, but do every one.
>
> For each person, find their official institutional page and record:
>
> - `position`: their exact title
> - `institution`: department and university as given on that page
> - `official_url`: the institutional page you actually used
> - `email` and `email_source`: only an address you genuinely saw, either on that page
>   or in the correspondence line of one of their own papers. Say exactly where it came
>   from. If you did not see one, leave it empty.
> - `research_keywords` and `techniques`: what they work on and what they work with
> - `latest_paper`, `latest_paper_year`, `latest_paper_url`, `latest_paper_senior`: the
>   most recent paper of theirs that cites me, and whether they are first or last author
>   on it
> - `your_paper_cited` and `your_paper_url`: which of my papers that one cited
> - `is_current_pi` and `pi_evidence`: whether they lead their own group right now, and
>   the sentence from the page that establishes it
> - `verdict`: include or exclude, with the reason
>
> Rules, and I mean these literally:
>
> - **Independent PIs only.** A postdoc, a PhD student, a staff scientist without their
>   own group, or an emeritus with no active group is an exclude. If you cannot confirm
>   independent PI status from a current page, exclude and say why.
> - **Never construct an email** from a name plus an institutional domain. Never take
>   one from a contact aggregator. Never reconstruct one that a page rendered badly.
> - If an address turns up for more than one candidate, it is the corresponding author's
>   address on a shared paper, not theirs. Drop it.
> - Do not search using a guessed address as the query. Confirming a guess is not a
>   sighting.
> - If a page will not load, say so plainly. Do not substitute a search-engine snippet
>   for a page you could not read, and if you rely on snippets, say that is what you did.
>
> Give me the results as a table, and list separately anyone you excluded and why.

Some institutions block automated access, and some organisations block university
domains outright. If that happens, the assistant should tell you it worked from search
snapshots rather than live pages. That is a weaker basis, and worth writing into the
report rather than hiding.

A useful follow-up once the table is in front of you, since the assistant will often
have been more certain than the evidence warrants:

> Go back over the ones you marked include. For any where the PI evidence is a single
> ambiguous sentence, or where the person might be a co-leader rather than running their
> own group, tell me now rather than leaving it in the report. I would rather lose a
> name than defend a weak one.

---

## Step 6. Build the report

> Now write up the verified candidates.
>
> Split them into two tiers:
>
> - **Tier A**: cites at least one of my group papers, meaning papers where I am last
>   author.
> - **Tier B**: cites none of them, ranked by overall engagement with my work.
>
> Within each tier, order by number of distinct group papers cited, then by total
> citing papers.
>
> Produce `referees_shortlist.md` with one section per person carrying position,
> institution, official page as a link, email with its source, research keywords,
> techniques, their latest paper citing me as a link, which of my papers it cited as a
> link, and the PI evidence. Flag anyone who has ever co-authored with me, with the
> years, as advisory information.
>
> Also produce `referees_shortlist.csv` with exactly these columns, so it stays
> comparable across runs:
>
> `tier, rank_final, name, position, institution, official_url, email, email_source,
> research_keywords, techniques, n_group_papers_cited, n_group_citing_papers,
> my_papers_cited, citing_papers, recent, prior_coauthor_years, latest_paper,
> latest_paper_year, latest_paper_url, latest_paper_senior, my_paper_cited,
> my_paper_url, is_current_pi, pi_evidence`
>
> And `referees_excluded.md`: everyone dropped at verification, with the evidence, so I
> can reverse any call I disagree with.
>
> At the top of the markdown file, state how the order was set and note any limitation
> in how the verification was done. Save all three as artifacts.

---

## Step 7. Reference gaps in something you are writing

The part most people end up using every week. Attach the manuscript or grant you are
drafting and its `.bib`. Dana's are `levi_crystallisation_2026.tex` and `refs.bib`; use
your own filenames.

> Run:
>
> `python3 referee_finder.py suggest levi_crystallisation_2026.tex --bib refs.bib --shortlist referees_shortlist.csv --include-coauthors`
>
> Use `--shortlist` rather than a rank cutoff: a `--top` window silently skips verified
> people who rank below it, which in one test missed 16 of 24 real gaps.
>
> Use `--include-coauthors` because this is a bibliography, not a referee list. The
> five-year co-author rule is what funders apply to referee nominations. Editors do not
> screen reference lists for co-authorship, and citing close collaborators in a paper is
> normal and usually correct.
>
> Then go through `citation_gaps.csv` with me. For each row, tell me whether the
> suggested paper genuinely belongs in the section it proposes, on the merits. Say
> plainly where it does not. Do not recommend a citation that is not warranted, and
> flag the rows where `also_covers` means one added reference would close several gaps
> at once.

The matching underneath is word overlap between their paper title and your section
text. It has no idea what your paper argues. It proposes; you and the assistant judge.
A padded reference list is worse than an incomplete one and a referee can tell.

---

## Step 8. Later runs

Come back in a month, attach nothing, and say:

> Re-run `python3 referee_finder.py all`. Tell me which names are new since the last
> run, then verify only those against the rules we used before and add them to
> `referees_shortlist.md` in the right tier.

Harvesting is incremental: it records the date of each run and asks OpenAlex only for
citing records added since. A monthly update takes about a minute plus verification of
whatever is new. Once or twice a year, add `--full` to force a complete re-read, because
OpenAlex backfills.

When you add a paper to your CV, add its DOI to `data/author_dois.txt` first. The tool
detects a newly added paper and harvests its full citation history.

---

## Two things that will bite

**Verify before you propose.** `shortlist_to_verify.csv` is named that for a reason, and
step 5 exists because of it.

**Read the excluded file.** A correct-looking shortlist can hide a wrong exclusion, and
a wrongly excluded person is invisible unless you go looking.
