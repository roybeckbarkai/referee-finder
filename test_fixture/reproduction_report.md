## Deviations from full scope

Instructed by the task, not chosen by me: steps 11, 12 and 14 were not run (no web verification, no tiered write-up, no re-run guidance), and no `ask_user` calls were made — every answer came from the stand-in block. Step 13 was run without a `--shortlist` file, so the candidate set is the tool's own default top 30 rather than a verified list. Everything in steps 1–10 was run for real against OpenAlex with the stored credential. No sampling, no caps, no substituted inputs.

---

## Requested figures

**1. DOIs extracted, and how many resolved**

79 DOIs above the `#PREPRINTS` line, 5 preprint duplicates below it. All 79 resolved in OpenAlex.

The CV publication list has 80 numbered items. Item 79 is the literal text `**Under review**` — a sub-heading the numbering swept up, not a paper — and there is a stray `81.` at the end of the file. So 79 real entries, every one of which carries a DOI. Nothing was un-findable.

The 5 below the line are preprint versions of published papers: `10.1101/2022.04.19.488724`, `10.1101/2022.10.28.514176`, `10.26434/chemrxiv-2025-rjndg`, `10.64898/2026.03.27.714705`, `10.1101/2025.10.13.682119`. One preprint stayed **above** the line — `10.64898/2026.06.07.730657` (Koren et al., "Not All Charges Are Equal", under review, no journal version) — per the instruction that a preprint with no published counterpart is a real paper.

Caveat on the resolution count: the tool reports `80/79 resolved` and then `of 80 papers, 27 count as group papers`, because **one DOI returns two OpenAlex work records**. `10.1038/s41598-020-73030-2` maps to both `W3105602250` and `W3008415495`. That is a duplicate record on OpenAlex's side, not a CV error, but it inflates every per-work total downstream by one paper.

One extraction detail worth recording: CV entry 32 renders its DOI as `10.1039/C5SM00662` with the trailing `G` pushed outside the link text. A naive text-regex extraction produces a dead DOI. I took the DOI from the `doi.org` href in every case, which is correct for all 79. No `?utm_source`/`?sharing_token` junk in this CV — the trap CLAUDE.md warns about did not fire here.

**2. Total citations across the author's works**

**2332** (sum of `cited_by_count` over the 80 work records). This includes the duplicated Scientific Reports record twice, so the true figure is slightly lower.

**3. Citing-work records vs distinct citing works**

- As the tool prints it: **2329 citing-work records**
- Distinct citing works, computed over the union of OpenAlex work ids: **1852**

The 477-record difference is works that cite more than one of Beck's papers.

**4. Candidate authors**

**7715**

**5. Exclusions**

**258 total.** Two sources, and they disagree on presentation:

The tool's own stdout prints only two lines:
```
recent co-authors: 78 (excluded)
same institution : 223 (always excluded)
```
That sums to 301, which is not 258, and manual exclusions are not printed at all. The real breakdown, taken from the flag columns in `data/excluded.csv` (7715-row `candidates_ranked.csv` gives the same):

| rule | rows flagged |
|---|---|
| recent co-author (since 2022) | 78 |
| same institution | 223 |
| manual exclusion | 4 |
| *union* | **258** |

Overlaps: 46 people are both recent co-authors and Tel Aviv, 1 is both a recent co-author and a manual exclusion, 0 are both home-institution and manual. 78 + 223 + 4 − 46 − 1 = 258.

By `exclusion_reason` string, from `excluded.csv`:

| reason | n |
|---|---|
| same institution | 177 |
| co-author since 2022; same institution | 46 |
| co-author since 2022 | 31 |
| spelling variant of the above | 1 |
| BSF partner lab (Ohio State) | 1 |
| co-author since 2022; NSF-BSF 2020787 co-PI (UCSB) | 1 |
| LMU-TAU Research Cooperation co-PI (LMU Munich) | 1 |

Only **4 of the 8 manual-exclusion lines fired**: Anthony Brown, Omar Abdullah Saleh, Erwin Frey, Sarah Köster. Uri Steinitz, Ornit Chiba-Falek and Uri Ashery never appear in the candidate pool at all, so there was nothing to exclude. The `Koster, Sarah` line matched nothing; the `Köster, Sarah` line did — which is why the recorded reason for her is the useless string `spelling variant of the above`. The reason text that gets stored is whatever comment sits on the line that happens to match, so putting the variant second cost the real reason.

**6. Group papers (last author)**

**27** of 80 work records.

**7. Maximum `n_institutions`**

Across all 7715 ranked rows: **max = 8**, and **60 rows are at 6 or more**. The instruction predicted a clean run finds nobody here. It found 60.

None of them are in the shortlist (shortlist max is 4, on Harald Herrmann) and none are in the excluded set. I pulled the full affiliation sets out of `citing_works.json` — the CSV `institutions` column only shows the first three alphabetically — and the 60 are **not** name-merges. They are affiliation blocks from single multi-institution papers, where OpenAlex attaches every institution in the authorship record to each author. The signature is unmistakable: fourteen ICM/Pitié-Salpêtrière authors (Lefebvre-Omar, Elise Liu, Dalle, Bigou, Daube, Karpf, Davenne, Jost-Mousseau, Salachas, Seilhean, Lobsiger, Millecamps, Boillée, Bohl) share the *identical* six-institution set; six CEA Marcoule authors share an identical six; four Australian-synchrotron authors share an identical six. Several individually are genuinely multi-affiliated (Zetterberg 7, Blennow 7, Petzold 8 — all real). One row, `T. Helm` at rank 6162, has no OpenAlex author id and reached 6 institutions off a single citing paper via the name-key fallback.

So: the check fired loudly, and the answer is a false positive driven by per-authorship institution lists, not by the name-merge bug it was written to catch. A user following the instruction literally would list 60 names and have no idea what to do with them.

**8. `home_institutions`, verbatim, and what actually matched**

```toml
home_institutions = ["tel aviv university", "tel-aviv university", "sackler"]
```

Distinct `matched_home_institution` strings across all 223 flagged rows: **`Tel Aviv University`** — one string, nothing else. `tel-aviv university` and `sackler` never fired. `sackler` is the entry I would flag as a risk: it is a bare substring and would also catch the Sackler Centre at Sussex or the Sackler Institute at Cornell if anyone from those had cited him. It did not, this run.

**9. The top 30, in order, with `rank_final`**

| rank_final | name | rank_final | name |
|---|---|---|---|
| 25 | Sanjay Kumar | 80 | Roi Asor |
| 40 | Ohad Medalia | 81 | Aurnab Ghose |
| 42 | Erika A. Ding | 82 | Tal Ben‐Nun |
| 50 | Uri Raviv | 83 | Asaf Shemesh |
| 57 | Harald O. Herrmann | 84 | Yehonatan Levartovsky |
| 60 | Takashi J. Yokokura | 94 | Ruoxing Lei |
| 61 | Rui Wang | 95 | Jessica P. Lee |
| 62 | Vladimir N. Uversky | 96 | Matthew B. Francis |
| 71 | Swayam Jyothi Tirupathi | 97 | Arne Raasakka |
| 72 | Irena Zingerman-Koladko | 98 | Petri Kursula |
| 73 | Jan Harapin | 99 | Bing Xu |
| 76 | Christopher J. Bott | 100 | George Harauz |
| 77 | Bettina Winckler | 101 | Frans A. M. Leermakers |
| 78 | Lea Fink | 102 | Ian William Hamley |
| 79 | Avi Ginsburg | 103 | Valeria Castelletto |

The ranks run 25 → 103 with gaps; the gaps are the 258 excluded people, who keep their place in the full ranking.

**10. Was anyone flagged as possibly being the author himself?**

Yes, and nothing in the tool noticed. **Roy W. Beck**, `rank_final` 48, ORCID `0000-0002-5194-8446`, affiliation Tel Aviv University, 1 citing paper — a second OpenAlex author record for Beck himself, under a *different* ORCID from the `0000-0003-3121-4530` in the config. The `me` set from `author_ids()` contains `A5015488088` and `A5033185226`; this row is `A5081405643`, so the self-filter did not catch it.

What removed him: the **same-institution rule**, matching `Tel Aviv University`. Purely lucky. Had the config not listed his own university — or had the stray record carried a foreign affiliation — the author would have appeared on his own referee shortlist at rank 48. Nothing in step 10's four checks would have surfaced this either; I found it by grepping the ranking for his surname, which the instructions never ask for.

Separately on the ORCID question the instructions do ask about: **the configured ORCID resolves to two OpenAlex author ids** (`A5015488088`, `A5033185226`). That is the normal split the instructions say to expect and it is handled. The third record above is a different failure — an ORCID the tool never sees.

**11. Step 13 — citation gap check**

Run as `suggest grant_v21.tex --bib refs_authoritative_REVIEWED.bib --include-coauthors`, with no `--shortlist`, so the candidate set is the tool's own default top 30 taken from the co-author-inclusive ranking.

- **Candidates checked: 30**
- **Not cited: 6**
- **With a placement: 6** (all six that were uncited got one; zero empty suggestions)

| name | rank_final | recent co-author | suggested paper | section | score |
|---|---|---|---|---|---|
| Ian L. Morgan | 10 | yes | Glassy Dynamics and Memory Effects in an Intrinsically Disordered Protein Construct (`10.1103/physrevlett.125.058001`) | Preliminary Results | 2.94 |
| Joachim Oskar Rädler | 26 | yes | 3D-printed SAXS chamber for controlled in situ dialysis (`10.1107/s1600577522005136`) | Aim 2 | 1.58 |
| Miriam von Westphalen | 68 | yes | same paper as above | Aim 2 | 1.26 |
| Hoang P. Truong | 70 | yes | Magnetic tweezers characterization of the entropic elasticity of IDPs and peptoids (`10.1016/bs.mie.2023.12.011`) | Scientific Background | 2.34 |
| Swayam Jyothi Tirupathi | 71 | no | Sticks with whips in neurodegenerative diseases (`10.1016/bs.apcsb.2025.10.031`) | Scientific Background | 2.21 |
| Christopher J. Bott | 76 | no | Intermediate filaments in developing neurons: Beyond structure (`10.1002/cm.21597`) | Resources, Expected Results and Pitfalls | 1.53 |

**Yes — suggested papers turned out to be the author's own, and in a worse way than the instructions anticipate.** Checking the author list of every suggested paper:

- `10.1103/physrevlett.125.058001` — authors Morgan, Avinery, Rahamim, **Roy Beck**, Saleh. This is CV entry, and it is **in `data/author_dois.txt`**.
- `10.1107/s1600577522005136` — authors Ehm, Philipp, Barkey, Ober, Brinkop, Simml, von Westphalen, Nickel, **Roy Beck**, Rädler. Also **in `data/author_dois.txt`** (CV entry 63).

So **3 of the 6 rows** (Morgan at rank 10, Rädler at 26, von Westphalen at 68) point at **2 distinct papers Beck co-authored**, both of which he supplied as his own. Citing them does nothing about those three candidates — it closes a gap in his own self-citation. The instruction's warning ("in testing, the single gap reported for the second-ranked candidate turned out to be a paper the user had written and led") reproduces here at three of six rows, and the tool has the information to catch it: it could cross-check suggestion DOIs against the author's own DOI file, and does not.

That leaves **3 genuine gaps**, all defensible on the merits:

- **Tirupathi** — an Uversky review on intrinsic disorder in cytoskeletal proteins in neurodegeneration, placed in Scientific Background. Squarely on topic for a neurofilament/IDP grant; the shared terms are generic ("biology, diseases, dynamics, function, proteins, research") but the paper is the right paper regardless. Worth citing. Note Tirupathi is first author with Uversky senior, so the citation credits the junior author's row while the group it reaches is Uversky's.
- **Truong** — magnetic-tweezers entropic elasticity of IDPs, Scientific Background. Directly relevant to IDP mechanics, and the overlap terms are substantive ("disordered, entropic, force, intrinsically, microscopy, proteins"). Worth citing. Caveat: Truong's senior author is Omar Saleh, a manually excluded co-PI; the paper is fine to cite, the person is not a referee.
- **Bott** — intermediate filaments in developing neurons, placed in "Resources, Expected Results and Pitfalls". The weakest of the three: score 1.53 on four generic shared words ("beyond, biology, disease, structure"), and a *Resources and Pitfalls* section is not where a topical review belongs. If this paper earns a citation it belongs in Scientific Background, not where the tool put it. I would not cite it on the strength of this match.

`also_covers` is populated on exactly one pair — Rädler and von Westphalen share `10.1107/s1600577522005136` — and both of those are the author's own paper, so the "one citation closes two gaps" signal here closes nothing.

---

## Friction

**The DOI count is off by one and the instructions have no way to express it.** The tool prints `80/79 resolved` and then reasons about "80 papers" for the rest of the run. Step 9 asks for "how many of my papers resolved out of how many I gave you" as if that ratio were ≤ 1. A non-expert reading `80/79` has no idea whether that is good. The cause — one DOI, two OpenAlex records — is invisible unless you go into `author_works.json` yourself.

**Step 5's `home_institutions` advice leads straight into a trap that step 10 then partly papers over.** The stand-in answer volunteers "Sackler" as a former faculty name. The instruction says include former names and warn about breadth. Fine. But the reason the author's own duplicate record got filtered was `Tel Aviv University` matching — i.e. the *most* important effect of `home_institutions` in this run was an accident. If a user follows step 5 correctly and lists only distinctive strings, they get no protection against their own stray author record, and step 10 has no check for it. I would add "does the author appear in his own ranking" to step 10; the instructions do not ask, and I only found it by looking.

**The manual-exclusions format silently loses the reason.** Two spellings of the same person produce two lines, and the reason attached to whichever line matches is the one recorded. Here the recorded reason for Sarah Köster is `spelling variant of the above`, which is exactly the thing step 6 says the user might need to defend later. Nothing warns about this.

**Half the manual exclusions are no-ops and the tool says nothing.** Four of eight lines never matched anyone in a 7715-row pool. That is correct behaviour, but a user who typed Ornit Chiba-Falek expecting to see her excluded gets no confirmation either way, and cannot distinguish "not in the pool" from "my spelling was wrong". A "0 matches" line per unmatched entry would cost nothing.

**Step 9's exclusion breakdown cannot be answered from the tool's output.** The printed lines sum to 301 against 258 actual rows because of overlaps, and manual exclusions are not printed at all. You have to load `excluded.csv` and do the set arithmetic yourself. The instruction asks for "how many were excluded and under which rule" without saying the tool will not tell you.

**Step 10's first check is calibrated wrong.** "Genuinely multi-affiliated researchers reach four or five, so a clean run finds nobody here" is false on real data. 60 rows at ≥6, driven by per-authorship institution lists on multi-centre papers, not by the merge bug. Worse, the `institutions` column is truncated to three entries alphabetically, so the check *as written* cannot be performed from the CSV — you have to re-derive the full sets from `citing_works.json`. A non-expert would either list 60 names as suspect merges or conclude the tool is broken.

**Step 13's instruction is ambiguous under the test's own constraint.** "Use the tool's own top-30 shortlist instead of a `--shortlist` file" has two readings: pass `data/shortlist_to_verify.csv` to `--shortlist`, or run with the default `--top 30`. They give different candidate sets, because `--include-coauthors` changes which rows survive filtering *before* the top-30 cut. I took the second reading. `shortlist_to_verify.csv` and the 30 rows actually checked overlap on only 10 names — Sanjay Kumar, Medalia, Ding, Raviv, Herrmann, Yokokura, Rui Wang, Uversky, Tirupathi, Zingerman-Koladko, Harapin, Bott. If the baseline run took the other reading, these step-13 numbers will not match.

**The self-citation blind spot in `suggest` is the most consequential thing I hit.** Three of six reported gaps resolve to papers in the user's own `author_dois.txt`. The instruction tells the assistant to catch this by hand, which I did, but the tool has both lists in the same directory and does not cross-check.

**Nothing errored.** `python3 referee_finder.py all` ran clean in about six minutes on Python 3.11.16 against the live OpenAlex API with the stored key. `data/out_of_scope_dois.txt` was not created, correctly, since the answer was "none".

---

Outputs saved: [citation_gaps.csv]({{artifact:d2561a01-787e-461d-8860-a4209ff3bd02}}) — the six step-13 rows, three of which point at the author's own papers. Supporting files: [author_dois.txt]({{artifact:fd232cd8-be12-4731-bc67-1e95f68afcd9}}) (79 above the line, 5 preprint duplicates below), [config.toml]({{artifact:52e769ca-802f-4646-b67e-dc861ef87dcc}}), [shortlist_to_verify.csv]({{artifact:f397c8b8-36d0-480b-bdfa-860cdeb604c7}}), [excluded.csv]({{artifact:ca5facd1-5e42-4040-9fb4-37517fedd850}}) (contains the Roy W. Beck self-row at rank 48), [candidates_ranked.csv]({{artifact:2fa9726e-835e-42f8-9cf8-02bf87edf7ca}}).