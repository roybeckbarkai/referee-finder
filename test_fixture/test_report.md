Test complete through step 13. Here is the report.

---

# Test report: referee-finder guided-session prompt

**Deviations from the task as given (declared):** Step 11 verified 2 of 30 candidates, as instructed by the test scope — stopped after two and said so. Step 12 therefore covers only those two. Step 14 skipped as instructed. No other reductions. One consequence to flag: **every count in step 11/12 below rests on n=2 and is provisional.**

## Bottom line

Steps 1–10 and 13 work essentially as written; the tool matches its documentation. **Step 11 is impossible in this sandbox** and, applied literally, produces an empty shortlist. Step 13 surfaced a conflict-detection failure that steps 3–8 actively conceal from the user. And the prompt's 14-step interview structure collides with its own "resume from data/" instruction.

## Step-by-step

| Step | Worked as written? |
|---|---|
| 1 credential check | Yes. Credential named `OpenAlex` found. The walkthrough branch was untested. |
| 2 fetch tool | Yes. All three files HTTP 200. `curl` fine; `git clone` is indeed blocked (coarse-mode git protection). |
| 3 DOI list | Mostly. Two ambiguities, below. |
| 4 ORCID | Yes, but see the two-author-ids problem. |
| 5 home_institutions | Yes. |
| 6 manual exclusions | Yes. Both names fired. |
| 7 first-author / out-of-scope | Yes. Defaults already correct; nothing to change. |
| 8 co-author window | Yes mechanically, **wrong in effect** — see finding 12. |
| 9 harvest + rank | Yes. 15 s wall. Numbers mostly consist; two are not. |
| 10 three checks | Yes. All three runnable, all three clean. |
| 11 verify 30 | **No. Structurally impossible.** |
| 12 write-up | Yes, but degenerate: zero survivors under the rule as written. |
| 13 suggest | Yes, and it exposed a real bug in the upstream steps. |

## 1. Ambiguous, had to interpret, or guessed

**1. The CV's name is not the user's name.** The CV header says "Dana Levi"; the stand-in answer for "name as it appears on papers" is "R. Beck"; the ORCID belongs to Beck and the papers are Beck's. Nothing in the instructions says what to do when the CV identity and the stated identity disagree. I used "R. Beck" because config.example.toml says the field is a fallback for matching authorship records. A real user with a mismatch here would get silently wrong group-paper detection.

**2. Standalone preprints.** Step 3 says put "preprints of papers that are also published" below `#PREPRINTS`. The CV's preprint (10.1101/2026.01.15.000001) has no published version — it is a `## Preprints` section entry. The rule as written does not cover it. `read_doi_list()` hard-stops at the marker, so anything below it is *never harvested*. I put it below the marker and thereby dropped a paper from the anchor set. The opposite choice was equally defensible. **This decides whether a paper's citers enter the candidate pool, and the instructions leave it to a coin flip.**

**3. "any former name of that same university."** I could not establish one for Tel Aviv University, so I included three entries (English, hyphenated, Hebrew). I have no way to know whether a former name exists and the instruction gives no way to check. Note also that the instruction here **contradicts CLAUDE.md**, which says to include "the attached hospital or medical school, and any institute formally part of it." Step 5's list is narrower. I followed step 5 (the thing under test) and so did not add Sourasky/Ichilov. A Tel Aviv affiliate publishing under the hospital name alone would not be excluded.

**4. "show me the top 30 as a readable table."** Top 30 of what — the full ranking, or the post-exclusion shortlist? I used `shortlist_to_verify.csv` because that is what the tool writes and what CLAUDE.md calls "the working list." But its `rank_final` column reads **1, 2, 3, 6, 11, 17, 18, 20, 21, 22, 23, 24, 25, 30, 31, 32, 33, 34, 35, 36, 37, 41, 42, 51, 52, 53, 54, 57, 59, 65** — not 1–30. A non-expert shown this will ask where ranks 4, 5, 7, 8, 9, 10 went. Nothing tells you to explain that.

**5. Step 12 "Tier A / Tier B."** Both candidates are Tier A, so I never tested the tier split with real data. Also unspecified: what to do when a tier is empty (I wrote "Empty" and said why).

**6. Step 12 "the survivors."** With zero survivors the instruction has no defined output. I invented a third category — "conditional include, does not meet the letter of the rule" — because writing three empty files would have been useless. That is me overriding the instruction, and I am reporting it as such rather than hiding it.

## 2. Things in the instructions that did not match reality

**7. Step 9: "how many citing authors were found."** The tool prints `candidates: 3385`, which is citing authors *after* the phantom-author fallback and after removing the author themself — not a raw count. Minor, but the phrasing invites reporting a number the tool does not produce.

**8. Step 10 check 1: "far above three."** `n_institutions` is not a flag, and no threshold exists in the tool. CLAUDE.md says "far above 3"; the actual maximum in 3,385 rows is **7**, and the two shortlist rows above 3 (Herrmann 4, Etienne-Manneville 5) are both genuinely multi-affiliated people, not merges. So the check as specified finds nothing, and a user cannot tell whether that means "clean" or "threshold wrong."

**9. Step 12 filenames.** `referees_shortlist.md`, `.csv`, `referees_excluded.md` do not exist in the tool — you write them yourself, from scratch, with no template and no column list specified for the CSV. I invented 19 columns. Two runs of this prompt will produce two incompatible CSVs.

**10. Step 13 "Flag where one added reference would close several gaps at once."** The `also_covers` column exists but was **empty for every row** in every variant I ran. Nothing to flag. A user told to expect this will think something failed.

## 3. Errors

**11. Step 11 cannot be executed. This is the headline finding.**

Every institutional domain is blocked, and the block is **not** approval-liftable:

```
www.bioc.uzh.ch                     curl: (7) CONNECT tunnel failed, response 403
www.neuropathologie.uk-erlangen.de  curl: (7) CONNECT tunnel failed, response 403
www.fau.de                          curl: (7) CONNECT tunnel failed, response 403
pub.orcid.org                       curl: (7) CONNECT tunnel failed, response 403

request_network_access("www.bioc.uzh.ch")
 → denied: "not on your organization's allowlist. The allowlist is managed by your
    admin and can't be overridden by an approval"
```

Reachable: `api.openalex.org`, `www.ebi.ac.uk` (Europe PMC). That is all. So:

- "find their official institutional page" — cannot be done for anyone.
- "record the page URL you actually used" — always empty.
- "the sentence that establishes whether they lead their own group right now" — always empty. **This is the field the entire include/exclude decision turns on.**
- "if you cannot confirm independent PI status from a current page, exclude and say why" — applied literally, **this excludes all 30 candidates**. The tool's whole output becomes an empty referee list.

Step 2 correctly warns that `git clone` does not work in this sandbox. Step 11 assumes the open web does. It does not, and the instructions offer no fallback, no mention of `request_network_access`, and no guidance for the (actual) case where the request is refused above the user's head.

**12. Step 13 found a conflict the pipeline missed, and the missed conflict is a co-author.**

The single gap the tool reported for Ohad Medalia is:

```
Ohad Medalia -> Introduction  [disordered, interactions, mechanical, neurofilament, proteins]
  Phosphorylation-Induced Mechanical Regulation of Intrinsically Disordered
  Neurofilament Proteins            doi:10.1016/j.bpj.2016.12.050
```

That paper's author list, from the harvested data:

```
first  Eti Malka-Gibor        middle Jan Harapin
middle Micha Kornreich        middle Ohad Medalia
middle Adi Laser-Azogui       last   Roy Beck
middle Ofer Doron
```

**The user is last author on it.** So the tool's #2-ranked referee candidate is a co-author, and the recommendation "cite Medalia" is really "you forgot to cite your own 2017 paper." Three things converge to hide this:

- the 2017 paper is not on the CV (it is a *selected* publication list), so the co-author network built at step 3 never contained Medalia;
- the five-year window from step 8 starts at 2022, so 2017 would not have fired anyway;
- harvest prints `co-authors since 2022: 0`, and `recent_coauthor` reads `False` for Medalia in every output file.

Step 3 warns that a missing paper means "a missing community" — framed as losing candidates. It never says the reverse: **that a missing paper means a missed conflict, and that a selected-publications CV is therefore unsafe for the exclusion side of the tool.** Step 8's question about the window is answered honestly by a user and still yields a co-author at rank 2.

A related case the instructions discuss at length and still get wrong: ranks 8, 9, 10 are Avinery, Kornreich, Laser-Azogui — the user's own former students. They were excluded, but only by `same institution`, not by co-authorship. Any of them who has moved abroad would appear in the top 10 as a referee. Step 5's careful argument about not excluding former institutions does not cover this.

## 4. Where a non-expert would be stuck

- **Step 9's numbers do not reconcile and nothing explains why.** See section 6.
- **Step 10 check 1 returns nothing.** No threshold given, so "clean" and "check is broken" look identical.
- **`rank_final` jumping 3 → 6 → 11 → 65** in the table they are shown, with no explanation.
- **Two shortlist rows have no institution at all** (`Priti Sharma`, `Aditi Giri`, `n_institutions=0`, blank `institutions`). Step 11 says find their institutional page. From what? The instructions never mention this case.
- **12 of 30 shortlist rows have `senior_author_share = 0.0`**, including Dmitri Svergun and Haydyn Mertens — the tool's own docs say near-0 "suggests a student," yet Mertens is ranked 3rd. A user is not told that this column is a pre-filter they could apply before spending verification effort on 30 people.
- **Eight of 30 have not cited the user since 2022 or earlier** (Leermakers: 2020). No staleness guidance.
- **The ORCID resolved to two OpenAlex author ids** (`A5015488088`, `A5033185226`). CLAUDE.md warns extensively about namesake *merging* into one id; nobody warns about one ORCID *splitting* across two. The tool handles it (`author_ids()` returns a set), but a user reading `OpenAlex author ids for this ORCID: ['...', '...']` has no idea whether that is normal or the disaster CLAUDE.md describes.
- **Step 12 asks the user to judge "the order was set" and "any limitation in verification"** — both of which only the assistant knows. Fine here, but the user has no way to check either claim.

## 5. Things I needed to know and was never told

- That institutional pages are unreachable and `request_network_access` exists — and that it can be denied above the user's level.
- Where to get the "most recent paper of theirs that cites me, with its link, and whether they are senior author on it, and which of my papers that one cited." All four fields are in `data/citing_works.json` (`authorships`, `author_position`, `doi`, `publication_year`), but step 11 does not say so, and a reader would go looking on the web for data already on disk.
- The CSV column set for step 12.
- That `data/out_of_scope_dois.txt` must simply not exist when there are none (step 7 implies you create it).
- That `_cfg_path()` resolves `data/` **relative to the script directory, not the cwd** — so the tool must be run from its own directory or paths silently point elsewhere.
- That `--shortlist` expects a CSV with the *same header as the ranked output* — I had to read the source to learn I could subset `shortlist_to_verify.csv` rather than hand-build a file.
- **The interview framing is incompatible with the resume instruction.** "Never run ahead of me" plus 14 sequential questions means a real session is ~14 round-trips; "if we are interrupted, look at what is already in data/ and resume" gives no way to tell which *questions* were already answered. `config.toml` records some answers (ORCID, institutions, window) but not others (first-author rationale, out-of-scope = none, which manuscript). A resumed session re-asks them.

## 6. Were step 9's numbers internally consistent?

Mostly. **Two are not.**

Reported:
```
OpenAlex author ids for this ORCID: 2
from your DOI list: 9/9 resolved
your works: 9  (total citations 880)
co-authors since 2022: 0
citing-work records: 878 total, 878 new this run
of 9 papers, 5 count as group papers (last author)
candidates: 3385   excluded: 126
  recent co-authors: 0 (excluded)
  same institution : 124 (always excluded)
```

Checks I ran:

- **880 total citations** = exact sum of the 9 `cited_by_count` values (194+167+126+76+90+66+64+53+44). ✅
- **126 excluded** = 124 home + 2 manual, and `is_manual_exclusion` is True on exactly 2 rows. ✅ 3385 − 126 = 3259 eligible, top 30 taken. ✅
- **5 group papers** ✅ — verified by author position per work: last on ceb/nanolett/febslet/prl/jacs, first on nmat2566 and la103655x, middle on ja413036q and acsnano. Correct, and the default (exclude first-author) correctly kept the two Safinya-lab first-author papers out.
- ❌ **880 vs 878 is unexplained.** The per-paper harvest counts (194, 167, **124**, **75**, 90, 66, **65**, 53, 44) disagree with `cited_by_count` on three papers: −2, −1, +1. Net −2. Two of the user's citers exist in OpenAlex's counter but not its index. Nobody is told these are different quantities.
- ❌ **"878 citing-work records" is not 878 papers. The distinct count is 808.** 878 is the sum over the user's 9 papers of records retrieved; 70 works cite two or more of them and are counted twice. Step 9 asks you to report "how many citing authors were found" — a user reading "878 citing-work records" will believe 878 distinct papers cite them. That is wrong by 9%.

## 7. What the two verification records actually looked like

**Ohad Medalia** — carried as a conditional include, quoted from `referees_shortlist.md`:

> **Page URL actually used.** NONE read. The intended page, https://www.bioc.uzh.ch/en/research/research-groups/medalia.html, returned 'CONNECT tunnel failed, response 403' and the access request was denied at organisation level.
>
> **Email.** omedalia@bioc.uzh.ch — seen by me in the Europe PMC 'core' record for 10.1038/s41467-025-65800-1 (first publication date 2025-11-26), appended to his own author-affiliation string: 'Department of Biochemistry, University of Zurich, Zurich, Switzerland. omedalia@bioc.uzh.ch.' It is his own paper and his own corresponding address, not a shared one.
>
> **Most recent paper of theirs citing me.** 10.1007/978-3-032-05273-5_6 (2026), 'Insights into the Structure of Intermediate Filaments'. He is LAST author on it.
>
> **Which of my papers it cited.** 10.1016/j.febslet.2015.07.024 — 'Order and disorder in intermediate filament proteins', on which I am last author, so it is a group paper.
>
> **Sentence establishing current group leadership.** No page sentence obtained; this is the field the verification rule turns on and it is empty.

**Harald Herrmann** — excluded, quoted from `referees_excluded.md`:

> **Why excluded.** Two independent grounds. (1) No current institutional page was readable, which the procedure itself says is an exclude. (2) The only role description available at all — snippet-level — is 'senior scientist' in someone else's institute after his own group at DKFZ ended in 2015. That is precisely the staff-scientist-without-a-group case the procedure excludes.
>
> **Email.** (empty) — no address seen in any record I fetched. A dkfz.de address appears in web-search snippets of 2009 and 2016 papers; it is a snippet, and DKFZ is an institution he left in 2015, so it is not recorded.

Two observations on the format. The email rule is followable and worked — one candidate's address came from a record I fetched myself, the other's did not exist and stayed empty; the "drop an address that appears for more than one candidate" rule was untestable at n=2. But **every other field either collapsed to "NONE read" or had to be filled from a source the instructions do not sanction.** The rank-1 candidate is the exact failure mode the instructions warn about at length (a former group leader now a staff scientist) — and I could only detect it from a search snippet, which step 11 tells me not to rely on. **The instruction is internally self-defeating in this environment: it forbids the only evidence available and requires evidence that is unreachable.**

## 8. Full output of step 13, and whether the suggestions are sensible

Command that the instructions specify (verified shortlist, co-authors included):

```
python referee_finder.py suggest test_manuscript.tex --bib test_refs.bib \
    --shortlist data/verified_both.csv --include-coauthors

  checking 2 verified candidates from verified_both.csv
  2 candidates checked against test_manuscript.tex
    not cited: 2   with a defensible placement: 2
```

| name | rank | suggestion | doi | section | shared_terms | also_covers | note |
|---|---|---|---|---|---|---|---|
| Harald O. Herrmann | 1 | Intermediate Filaments: Structure-Mechanics Crosstalk | 10.1007/978-3-032-05273-5_7 | Introduction | filaments, interactions, intermediate | *(empty)* | score 1.15; senior author (last) |
| Ohad Medalia | 2 | Phosphorylation-Induced Mechanical Regulation of Intrinsically Disordered Neurofilament Proteins | 10.1016/j.bpj.2016.12.050 | Introduction | disordered, interactions, mechanical, neurofilament, proteins | *(empty)* | score 1.38 |

**Row-by-row judgement, on the merits.**

*Herrmann → Introduction.* **Warranted.** The manuscript's opening three sentences are about intermediate filament and neurofilament networks, disordered tails mediating interfilament interaction, and network stiffness. A 2026 review titled "Intermediate Filaments: Structure-Mechanics Crosstalk," with Herrmann as senior author, is squarely a review-of-the-field citation for exactly that framing. The placement is right and the section is right. The one caveat is that a 2026 book chapter may not yet be the most citable form of that argument — a primary paper might serve the sentence better — but the omission is real.

*Medalia → Introduction.* **The citation is warranted and the framing is wrong.** The paper is about phosphorylation-controlled mechanics of disordered neurofilament tails; the manuscript's second sentence is "Disordered protein tails mediate interactions between neighbouring filaments, and the resulting network stiffness depends strongly on ionic conditions." That is the same claim. It should be cited. But **the user is last author on it**, Medalia is a middle author, and the tool presents it as a gap attributable to Medalia. The correct advice is "you have omitted your own 2017 paper, which is the closest prior work to your second sentence" — not "consider citing Medalia." Citing it does nothing to address Medalia as an uncited researcher, because his own work (cryo-ET of filament structure) is not what this manuscript is about.

**What the run reveals about the matcher, beyond these two rows.** The `--top 30` variant found 10 placements, and the failures there are more instructive than the successes:

- *Haydyn Mertens → Results and Discussion*, shared terms `changes, disease, lipid, myelin`, for a paper on the myelin protein zero cytoplasmic tail. The manuscript's Results section says "Myelin membrane structure changes with lipid composition, and the transition is relevant to demyelinating disease." The overlap is four content words and the citation is **arguably defensible** — but the manuscript sentence is about lipid-composition-driven structural transition, and the candidate paper is about a protein tail. Adjacent, not the same claim.
- *Omar Saleh → Methods*, shared terms `disordered, function, structure`, for "Pincus blob elasticity in an intrinsically disordered protein." **Not warranted in Methods.** The Methods section is about SAXS, osmotic stress, and entropy estimation from simulated configurations. Nothing in it is about blob elasticity. The match is three generic words. This is the matcher's stated weakness — lexical overlap with no notion of what the section argues — behaving exactly as documented.
- *Sarah Köster → Introduction*, "Ion type and valency differentially drive vimentin tetramers into intermediate filaments." **Warranted, and arguably a stronger Introduction citation than either verified row** — it is precisely about ionic conditions driving vimentin assembly, matching the manuscript's "Vimentin and neurofilament proteins show related but distinct behaviour" and the salt dependence. Köster is rank 18 and would have survived verification on the evidence available. That she surfaced only in the `--top 30` run and not in the verified-shortlist run is an artefact of my stopping verification at two, not of the tool.

So: step 13's instruction to read the rows and judge them is **correct and necessary** — 1 of 2 rows here and at least 1 of 10 in the wider run are misplaced or mis-framed, and the tool cannot know it. The `--shortlist` over `--top` advice is sound in principle but untestable at n=2 (with 2 verified people, `--shortlist` found 2 gaps and `--top 30` found 10 — the instruction's claim runs the other way and only holds once verification is complete). The `also_covers` instruction had nothing to act on. And the instruction never anticipates the case that dominated this run: **a "gap" that is the user's own paper.**

---

## Artifacts

- [referees_shortlist.md]({{artifact:18bc8845-e551-4bbc-af35-2b8611cb5f8f}}) — step-12 write-up, with the verification limitation stated at the top as required
- [referees_excluded.md]({{artifact:386f881c-3701-498f-aac8-4ebb9c752dbb}}) — Herrmann's exclusion with reversible evidence, plus the 126 automatic exclusions
- [referees_shortlist.csv]({{artifact:ea2dc010-4727-4a98-8825-55ca97accd6d}}) — the 19 columns I had to invent
- [gaps_both.csv]({{artifact:0a19a5d3-7e33-49b4-9ef8-36966a798255}}) — step-13 output
- [shortlist_to_verify.csv]({{artifact:ba89e8c2-83c6-4c73-8aaa-52955990799b}}) — the 30 the tool produced, 28 of them unverified

**The three changes that would matter most:** give step 11 a fallback for when institutional pages are unreachable (and tell the reader `request_network_access` exists); warn at step 3 that a *selected* publication list breaks conflict detection, not just candidate discovery; and have step 13 check whether a suggested paper is one of the user's own before attributing it to a candidate.