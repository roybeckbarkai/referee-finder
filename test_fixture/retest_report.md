## Deviations and scope

- Step 11 verified **3 of 30** candidates (ranks 1–3) and step 14 skipped — both by harness instruction, not silent cuts. Step 12 covers those three. I stopped step 11 after three and am saying so here.
- No `ask_user` calls; all answers taken from the stand-in list, as instructed.
- **Forced reduction:** no institutional page was readable. `www.uzh.ch`, `www.fau.de`, `www.embl-hamburg.de` all failed, and `request_network_access(www.uzh.ch)` came back **denied at organisation level** — "managed by your admin and can't be overridden by an approval." Every PI determination below rests on bibliographic records I pulled myself plus search snippets, never a page. Treat all three PI calls as **provisional**.

---

# Report on the seven rewrite targets

## 1. SELECTED publication list — **worked, partially by luck**

I did notice and say it. But I noticed it from the **fixture's own header** ("TEST FIXTURE… Items 1-9 are genuine"), which sits at the top of the file and says `## Selected Peer-Reviewed Publications`. On a real CV that heading might say "Publications" and there would be no fixture note. The instruction says "Tell me if what I gave you is a SELECTED publication list rather than a complete one" — it never says **how** to tell. There's no test given: no "compare the count against their OpenAlex works_count," no "look for the word selected." Here OpenAlex says the ORCID's author records carry far more than nine works; that comparison would have been a reliable detector and the instructions don't ask for it.

The cost explanation did land, and then the cost **materialised in step 13**: Medalia (rank 2) is a co-author of Beck on Biophys J 2017 `10.1016/j.bpj.2016.12.050`, where Beck is last author. That paper is not in the nine-DOI list, so the co-author machinery never saw it, `prior_coauthor_years` is empty, and no flag was raised against him. 2017 is outside the five-year window so he would not have been excluded anyway — but the *flag* Beck needs to declare the relationship is absent. Exactly the predicted failure, observed live.

**Defect not covered:** the instruction says "ask me for the complete one" and then gives you nothing to do when the answer is "there isn't one." I recorded the consequence and proceeded, which seems right, but that path is not written down.

## 2. Preprint with no journal version — **worked, clear**

Item 11 (`10.1101/2026.01.15.000001`) went **above** the `#PREPRINTS` marker. The wording "A preprint with no journal version yet is a real paper and belongs ABOVE that line so that it is harvested; only duplicates of already-published work go below it" is unambiguous and I acted on it without hesitation. My file has 10 DOIs above the line and nothing below.

One rough edge: with nothing to put below it, I still wrote the `#PREPRINTS` line (harmless — `harvest` stops there). Not stated either way.

## 3. Distinct citing works and rank gaps — **worked**

- Tool printed: **878** citing-work records.
- Distinct citing works, computed by me from `citing_works.json`: **808**.
- Overstatement: 70 records, **8.7%**.

I explained the gaps too: the shortlist keeps `rank_final` from the full 3,385-author ranking, so the top-30 ranks run 1, 2, 3, 6, 11, 17, 18, 20, 21, 22, 23, 24, 25, 30–37, 41, 42, 51–54, 57, 59, 65 — the missing numbers are the 126 excluded people.

**Defect in step 9's report spec:** it asks "how many were excluded and under which rule." The tool's console prints only two rules (co-authors 0, same institution 124) and **silently omits the two manual exclusions**, even though 126 is the headline. I only got the full breakdown by reading `excluded.csv`: 124 same institution, 1 "postdoc supervisor" (Safinya), 1 "co-author on postdoc work" (Deek). A non-expert reading the console would report 124 and be short by two. The instruction should say to take the breakdown from `excluded.csv`, not the console.

Rest of the step-9 report, for the record: 9/10 papers resolved, 880 total citations, 3,385 candidates, 5 of 9 are group (last-author) papers, and the ORCID resolved to **two** OpenAlex author ids (`A5015488088`, `A5033185226`) — reported as normal and handled, as instructed.

## 4. Phantom-author check, max + threshold six — **worked; this is a real fix**

Answerable and decisive. **Maximum `n_institutions` = 7.** Full distribution: 1→2140, 2→743, 3→277, 4→94, 0→75, 5→33, 6→14, 7→9. Twenty-three rows at ≥6.

Because a number came back, I could tell "clean" from "check broken" — the old "far above 3" phrasing would have been useless here since 23 rows clear it. I then had to decide the fused-vs-multi-post question, and for all 23 the answer is **multi-post, not fused**: each has exactly one OpenAlex author id and zero null-id authorships, and the inflated counts come from OpenAlex attaching 6–7 institutions to a *single* authorship record (Zetterberg, Blennow, Shuyu Liu all have one paper carrying seven affiliations). None of them is in the top 30 — the highest is Borisov at rank 89.

**Two problems the instruction doesn't anticipate:**

- The `institutions` column is **truncated to the first three alphabetically** (source line 423). You cannot answer "does this look like one person or several fused" from the CSV at all. I had to re-aggregate the full affiliation sets from `citing_works.json` myself. The instruction asks a question its named data source cannot answer, and nothing warns you.
- Even with full sets, "one person with several posts" vs "several people fused" is a judgement call the instruction gives no criterion for. The reliable test — count distinct `author_id`s and null-id authorships under one normalised name — is described in CLAUDE.md's *code-modification* section, not in the user-facing check. `Hui Wang` (Amherst College + US Army Chemical Biological Center + East China Normal + Second Military Medical University) *looks* fused and isn't.

Other step-10 results: the only matched home-institution string is **`Tel Aviv University`** (124 rows, none with an empty matched string) — no over-broad matching. Unresolved own paper: the invented preprint `10.1101/2026.01.15.000001` only. Pre-verification flags: two shortlisted candidates with **no institution at all** (Priti Sharma rank 51, Aditi Giri rank 52); **twelve** with `senior_author_share = 0.0` including rank 3 Mertens; **one** stale citer (Frans Leermakers, rank 11, last cited 2020).

**Ambiguity:** "anyone who has not cited me for several years" has no threshold — the exact defect the rewrite just fixed for `n_institutions`, left unfixed one sentence later. I picked ≤2021 arbitrarily.

## 5. Evidence grading under a blocked web — **worked, and it saved the step**

This is the strongest part of the rewrite. Institutional pages were unreachable and the access request was refused above my level — precisely the scenario the wording anticipates. Applied literally, the old "confirm from a current institutional page" rule would have excluded all three and handed back nothing. The graded scheme produced a **usable list: 2 includes, 1 exclude**, with the basis stated against each name.

Headline as requested: **0 of 3 rest on a page read; 3 of 3 do not.**

The three graded records, quoted from the artifacts:

> **Harald O. Herrmann — rank 1 — verification_basis: record+snippet — is_current_pi: uncertain — include, flagged weak.** "No institutional page readable (fau.de blocked, request denied). OpenAlex record: last author on a 2026 chapter with affiliation 'Friedrich-Alexander University Erlangen-Nürnberg, Department of Physics'. ResearchGate profile heading gives his title as 'Senior Scientist … FAU … Department of Physics'. A long-standing DKFZ group leader … now listed as senior scientist inside another department: consistent with an independent senior researcher OR with a guest/senior scientist embedded in someone else's group. Not resolvable without the page." Email: empty.

> **Ohad Medalia — rank 2 — verification_basis: record+snippet — is_current_pi: yes.** "Named group at UZH Biochemistry ('Research Groups » Medalia', with its own People and Publications pages); snippet of the group page reads 'Prof. Ohad Medalia, Winterthurerstr. 190, CH-8057 Zurich'. … Independently corroborated by the record: last author AND flagged corresponding on four 2025-2026 papers with a UZH Biochemistry address." Email `omedalia@bioc.uzh.ch`, source: "Corresponding-author address inside the raw affiliation string of his own 2026 paper, retrieved by me from OpenAlex (W7124910394, doi 10.1007/978-3-032-05273-5_6) … Checked against the whole harvested corpus: it appears against no other candidate."

> **Haydyn D. T. Mertens — rank 3 — verification_basis: record+snippet — EXCLUDE.** "Google Scholar profile heading reads 'Former Senior Technical Officer, EMBL; Currently Medical Student (University of Wollongong, AU)'. An EMBL BioSAXS group slide lists the group as 'Group leader: D. Svergun / Staff: … H.Mertens …'. Record evidence agrees: every one of his 2024-2025 works is MIDDLE author, senior_author_share = 0.00 … He is also a group member of another candidate on the same shortlist (Dmitri Svergun, rank 57) — the exact error class CLAUDE.md flags."

The "exclude only on positive evidence" rule did real work: Mertens went out on two independent positive statements plus corroborating authorship data, not on an unreachable page. And the flag-your-weak-includes instruction caught Herrmann, which I would otherwise have shipped as a clean rank-1.

**Gaps:**
- The four grades assume one grade per person. Mine are all **record + snippet** — a combination the scheme has no slot for. I invented `record+snippet`, which breaks the "tell me the counts" arithmetic.
- The instruction says "try one institutional page. If it fails, use request_network_access." It does not distinguish a *user-grantable* block from an **org-level block that no approval can lift**. I burned an approval prompt discovering that. It also never says whether a search-engine snippet is even available to you — I have a `web_search` tool, but nothing in the instructions mentions one, and a reader without it would find grade `snippet` unreachable.
- "their research keywords and techniques" cannot be sourced from any record or snippet. I filled `techniques` from OpenAlex topics plus domain knowledge — i.e. I **inferred** it. The ground rule forbids inventing bibliographic, contact and affiliation data but is silent on this field, so the instruction is asking for something it also implicitly forbids.

## 6. CSV columns — **followed exactly; three columns underspecified**

All 25 columns present, in the stated order, no additions. Verified by reading the file back.

Columns I could not fill or had to guess:
- `official_url` — **empty for Herrmann** (nothing readable). For Medalia I put the URL *with an explicit "NOT opened — snippet only"* note inside the cell, because the column has no companion field for "URL I know of but did not read" and `verification_basis` alone would let a reader assume it was opened.
- `email` / `email_source` — **empty for Herrmann**, correct per the no-invention rule. Filled for Medalia from a genuine sighting.
- `recent` — undefined. I used `n_recent_citing_papers`. Could as easily mean the latest citing year.
- `citing_papers` — undefined as count-or-list, and it sits next to `n_group_citing_papers` (clearly a count) and `my_papers_cited` (clearly a list). I used the count. Two people running this will not produce comparable files, which defeats the stated purpose of fixing the columns.
- `prior_coauthor_years` — empty for both, and for Medalia that emptiness is **wrong** (see §1). The column is correct with respect to the input and misleading with respect to reality.

## 7. "Is this my own paper?" check — **fired, on one of two rows**

Ran `suggest test_manuscript.tex --bib test_refs.bib --shortlist verified.csv --include-coauthors`. Two verified candidates checked, two gaps, both with a placement.

- **Ohad Medalia → `10.1016/j.bpj.2016.12.050`** — *Phosphorylation-Induced Mechanical Regulation of Intrinsically Disordered Neurofilament Proteins*, Biophys J 2017. Author list: Malka-Gibor (first), Kornreich, Laser-Azogui, Doron, Zingerman-Koladko, Harapin, Medalia, **Beck (last)**. **This is Beck's own paper and he led it.** The check fired exactly as written. Reframed: this is a paper of his he has failed to cite in his own manuscript, not a gap attributable to Medalia, and citing it does nothing about Medalia. Medalia is a middle author, which is the co-author conflict from §1.
- **Harald Herrmann → `10.1007/978-3-032-05273-5_7`** — *Intermediate Filaments: Structure-Mechanics Crosstalk*, 2026. Authors: Sarah Köster (first), Harald Herrmann (last). Beck is not an author. Genuine gap.

On the merits, row by row as instructed: the Herrmann placement in **Introduction** is defensible — shared terms `filaments, interactions, intermediate`, and the section is literally about intermediate filament networks and tail-mediated interfilament interactions, which is what that chapter reviews. Herrmann is senior author on it. I would cite it. The Medalia row is void as a gap once reframed; the underlying paper (`bpj.2016.12.050`) is arguably worth citing in the Introduction on the merits, but as self-citation, not as closing a gap on a candidate.

`also_covers` is **empty for both rows** — which, with only two candidates, is the expected "no two candidates shared a best-matching paper" case, exactly as the instruction says. That said, with n=2 this column was not meaningfully exercised; flagging it as untested rather than passed.

---

# Everything else

**Errored:** nothing in the tool. The `suggest` run returned exit 1 in my shell, but that was my own `[ -f … ]` test, not the tool.

**A bug the instructions never ask about, found by accident.** `Roy W. Beck` appears in the candidate list at **rank 58** — Tel Aviv University affiliation, 4 of Beck's papers cited, ORCID `0000-0002-5194-8446` (not his). Whether that is the user under a second OpenAlex record or a namesake, he was removed **only** by the home-institution rule. Nothing in the tool or the instructions filters the user out of his own referee list. Had `home_institutions` been slightly off — or had the user moved institution and put only the new name in — he would have shipped at rank 58 of his own shortlist. Step 10 should ask "is the user themselves in the list, and what removed them."

**`suggest` writes its output outside `data/`.** It wrote `citation_gaps.csv` next to the script, not into `data/`, while everything else goes to `data/`. Step 12/13 never name the output path, and the closing "look at what is already in `data/` and resume" line will therefore miss it.

**Things a non-expert would be stuck on:**
- Step 2 says "run every later command from the directory that holds referee_finder.py" but never mentions `export OPENALEX_API_KEY`. CLAUDE.md does; the user-facing instructions don't, and step 9's "declare the OpenAlex credential on the cells that need it" is platform jargon, not a shell command.
- Step 5 asks for "any former name of that same university." A researcher who doesn't know whether their university was renamed has no way to check, and the instruction offers no source.
- Step 10's fused-vs-multi-post judgement (see §4) is beyond a non-programmer entirely: the data needed isn't in the CSV.
- Step 11's "record" grade requires querying OpenAlex by author id and reading `raw_affiliation_strings` / `is_corresponding`. That is a real skill and the instruction names the grade without naming the method.

**Things I needed that the instructions never mention:**
- That `data/out_of_scope_dois.txt` is read from a **fixed** path with no config key — if the user renames it, it is silently ignored and nothing warns.
- That `--shortlist` expects a CSV with a `name` column. I had to read the source to find out. A user handing it `referees_shortlist.csv` would be fine by accident, but nothing says so.
- Where `citation_gaps.csv` lands.
- Whether the `#PREPRINTS` marker must be present when nothing goes below it.

**The instruction's own framing is untestable as written.** It opens by demanding a one-question-at-a-time interview, then delivers fourteen steps each containing between two and six distinct questions (step 7 asks two explicitly; step 11 asks for nine fields per candidate). Following the framing and following the sequence are in tension, and a real assistant will resolve it by batching — which is what the framing exists to prevent.

---

[referees_shortlist.md]({{artifact:10c3fb44-08b1-4a23-8d6f-a6ac2e2a3ecd}}) — the two survivors with graded evidence and the Medalia conflict flagged
[referees_shortlist.csv]({{artifact:5f9d8f14-6726-463a-aef1-8651473e9232}}) — the 25 specified columns, in order
[referees_excluded.md]({{artifact:a48ee5b8-f576-4010-aebc-6f70299844cc}}) — Mertens, with the evidence so the call can be reversed
[citation_gaps.csv]({{artifact:cbccdf68-ec2c-4f1a-b841-ad3c8bd764eb}}) — raw tool output for step 13, before my own-paper reframing