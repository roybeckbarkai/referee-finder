# The one-prompt version

If pasting nine prompts in order is more bookkeeping than you want, paste this single
one instead and answer the questions as they come. It covers the same ground as the
nine-step walkthrough and produces the same files, broken into 14 instructions so that
each setup value is gathered separately, and it asks you one thing at a time and waits,
so you never have to know what comes next.

Start a new Claude Science session. If your CV is a file on your computer rather than
something you want to upload, have its folder path handy. Then paste everything in the
box below.

---

```
Act as my guide through the referee-finder tool, start to finish. I have not used it
before and I do not want to think about what comes next, so run this as an interview:
ask me ONE question at a time with your ask_user tool, wait for my answer, do the work
that answer unlocks, show me the result, and only then ask the next question. Never ask
me two things at once and never run ahead of me.

The goal, by the end: a verified, categorised list of researchers who could referee my
papers and grants, and a review of a manuscript I am writing that tells me which of
them I have failed to cite.

Three rules that hold for the whole session. Do not invent bibliographic or contact
data: no DOI you have not seen in my documents, no email built from a name plus an
institutional domain, no affiliation inferred from a surname. An empty field is correct
where a plausible guess is not. And if something is ambiguous, stop and ask me instead
of deciding for me.

Work through this sequence.

1. Check whether an OpenAlex credential is configured in this workspace. If it is not,
   stop and walk me through adding one: Customize in the left sidebar, then Credentials,
   then Add Credential, choosing OpenAlex, with a free key from https://openalex.org.
   Wait until I tell you it is done, then confirm it is visible before going on.

2. Fetch referee_finder.py and config.example.toml from
   https://raw.githubusercontent.com/roybeckbarkai/referee-finder/main/ with a plain
   HTTP request, not git clone, which does not work in this sandbox. Read CLAUDE.md from
   the same place before you run anything: it is written for you and it lists the traps.
   Run every later command from the directory that holds referee_finder.py, because it
   resolves data/ relative to its own location and not to the working directory. Tell me
   when you have the files.

3. Ask me for my CV or publication list. I will either attach it to my reply or give you
   a folder path on my machine, in which case request access to that folder and find it
   yourself. Then extract every DOI of my own papers into data/author_dois.txt, one bare
   DOI per line, no https://doi.org/ prefix, with anything after a "?" stripped off
   because tracking parameters cause silent 404s. Put preprints of papers that are also
   published below a #PREPRINTS line rather than deleting them. A preprint with no
   journal version yet is a real paper and belongs ABOVE that line so that it is
   harvested; only duplicates of already-published work go below it. Show me the count
   and the whole list, tell me about any CV entry you could not find a DOI for, and wait
   for me to confirm it matches my CV before you go on.

   Tell me if what I gave you is a SELECTED publication list rather than a complete one,
   and ask me for the complete one. This list anchors everything that follows, in both
   directions. A missing paper loses me candidates, and worse, it hides a conflict: the
   co-author exclusion is built only from the papers I give you, so somebody I have
   published with can arrive at the top of the list with no co-author flag against them
   at all. That is exactly what happened when this was tested on a nine-paper selected
   list.

4. Ask me for my ORCID.

5. Ask me which university I am at now. Then propose the home_institutions list and show
   it to me for approval. Include only my current university: its name as it appears in
   affiliations, its name in the local language if there is one, and any former name of
   that same university. Warn me about any entry broad enough to catch a different
   university by accident, since the match is a plain substring test and "york
   university" would also catch "New York University".

   Do not include universities where I did my PhD or my postdoc, even though I have
   papers from them. People at my former institutions are not my conflicts merely
   because I worked there once, and excluding an entire university would silently delete
   part of my own field from the results. What is a genuine conflict from that period is
   my former supervisor and the people I actually published with, and those go in the
   next step.

   Write config.toml with my ORCID, my name as it appears on papers, and the approved
   list.

6. Ask me who I cannot propose as a referee for reasons the citation graph cannot see:
   grant co-PIs, partners on pending proposals, my PhD and postdoc supervisors, thesis
   examiners, anyone I would recuse. Ask me for a short reason for each, because the
   reason gets recorded and I may need to defend it later. Write them to
   data/manual_exclusions.txt as "Surname, Forename   # reason".

7. Ask me whether any of my first-author papers were done in somebody else's lab, as a
   student or a postdoc. Tell me why you are asking: the ranking treats papers where I
   am LAST author as my own group's work and puts the people citing those at the top, so
   counting first-author papers written in a training lab would seed my former
   supervisor's group as candidate referees. In one test that setting put the old
   postdoc host at rank 72 and pulled eight members of that lab into the top 30. Keep
   the first-author setting off unless I tell you I published first-author work as an
   independent PI.

   While we are on it, ask me whether any of my papers sit in a subfield I do not want
   referees from, for instance work from a previous position that I have since left
   behind. If so, put those DOIs in data/out_of_scope_dois.txt. They still count towards
   how broadly someone cites me, but their citers stop being pushed to the top of the
   list.

8. Ask me whether to exclude everyone I have co-authored with in the last five years.
   Tell me the default is yes, because that is the rule funders and journals apply to
   referee nominations, and that we will turn it off later for the citation-gap check,
   where it is the wrong rule. Ask me whether my funder uses a different window.

9. Run the harvest and ranking. Declare the OpenAlex credential on the cells that need
   it. When it finishes, report: how many of my papers resolved in OpenAlex out of how
   many I gave you, my total citations, how many DISTINCT works cite me, how many
   candidate authors that gives, how many were excluded and under which rule, and how
   many of my papers count as group papers, meaning ones where I am last author.

   Two things to get right in that report. The citing-record total the tool prints is a
   sum over my papers, so a work citing three of them is counted three times; compute
   the distinct number yourself and give me that one. And if my ORCID resolved to more
   than one OpenAlex author id, say so and tell me that this is normal and handled,
   because one ORCID routinely splits across several author records.

   Then show me the top 30 as a readable table, and explain why the rank numbers in it
   skip values: the shortlist keeps each person's rank from the full ranking, so the
   gaps are the people who were excluded.

10. Before we verify anybody, run these checks and report them.

    First, look for the name-merge bug: OpenAlex sometimes fuses several real people
    into one row, which invents a nonsense entry and hides everybody inside it. Do NOT
    test this on n_institutions alone. On real data that column reaches six or more on
    dozens of legitimate rows, because OpenAlex attaches every institution on a
    multi-centre paper to each of its authors, and the CSV shows only the first three
    alphabetically so you cannot tell from it anyway. The reliable test is to go back to
    data/citing_works.json and count, per candidate name, how many distinct OpenAlex
    author ids and how many id-less authorships sit under it. One id is one person,
    however many affiliations they have. Several ids, or a pile of id-less records,
    is a merge. Report what you find, and report the maximum n_institutions too so that
    I can see the check ran.

    Second, every row flagged is_home_institution must name the affiliation that
    triggered it. Show me the distinct matched strings so I can see whether my
    institution name is matching too broadly.

    Third, which of my own papers failed to resolve in OpenAlex.

    Fourth, three things I should see before anybody spends an hour on verification: any
    shortlisted candidate with no institution recorded at all, anyone whose
    senior_author_share is at or near zero, which points to a student rather than a PI,
    and anyone who has not cited me for several years.

    Do not skip this step. The two worst bugs in this tool were both found here.

11. Verify all 30 candidates, in batches or with sub-agents, but every one. For each,
    find their official institutional page and record their exact title, department and
    university, the page URL you actually used, an email ONLY if you genuinely saw one
    and a note saying exactly where you saw it, their research keywords and techniques,
    the most recent paper of theirs that cites me with its link and whether they are
    senior author on it, which of my papers that one cited, and the sentence that
    establishes whether they lead their own group right now.

    Independent PIs only. A postdoc, a PhD student, a staff scientist without a group,
    or an emeritus with no active group is an exclude. Be warned that the single most
    common error here is group members of people already on the list: in one run, 15 of
    22 fresh candidates were postdocs or students of candidates ranked above them.

    Some organisations block university domains outright, and the block cannot always be
    lifted by asking. Before you assume the web is available, try one institutional page.
    If it fails, use request_network_access for that domain and tell me the outcome. If
    the request is refused above my level, do not silently give up and do not quietly
    exclude everybody, because applied literally that rule empties the list and hands me
    nothing. Instead, record for every candidate which of these the evidence rests on,
    and tell me the counts:

      page      a current institutional page you actually read
      record    a bibliographic record you retrieved yourself, for instance from
                OpenAlex or Europe PMC, including the affiliation string and
                corresponding address on their own recent papers
      snippet   a search-engine snippet of a page you could not open
      none      nothing found

    Exclude somebody only on positive evidence that they are not an independent PI, not
    merely because the page would not open. Where the basis is snippet or none, say so
    against that person's name and tell me the decision is mine. Then give me the
    headline: how many of the candidates rest on a page read, and how many do not.

    Never construct an email, never take one from a contact aggregator, never reconstruct
    one a page rendered badly, and drop any address that turns up for more than one
    candidate because that is a shared paper's corresponding address. Do not search using
    a guessed address, since confirming a guess is not a sighting. Never present a
    snippet as a page read.

    Then go back over your own includes and tell me which ones rest on a single
    ambiguous sentence, or where the person might be a co-leader rather than running
    their own group. I would rather lose a name than defend a weak one.

12. Write up the survivors, split into two tiers: Tier A cites at least one of my
    last-author papers, Tier B cites me but none of those. Order within each tier by
    distinct last-author papers cited, then by total citing papers. If a tier comes out
    empty, say so rather than leaving it out.

    Produce referees_shortlist.md with a section per person, and referees_shortlist.csv
    with exactly these columns, so that my runs stay comparable with each other and with
    anybody else's:

    tier, rank_final, name, position, institution, official_url, verification_basis,
    email, email_source, research_keywords, techniques, n_group_papers_cited,
    n_group_citing_papers, my_papers_cited, citing_papers, recent, prior_coauthor_years,
    latest_paper, latest_paper_year, latest_paper_url, latest_paper_senior,
    my_paper_cited, my_paper_url, is_current_pi, pi_evidence

    Also referees_excluded.md, listing everyone dropped with the evidence, so I can
    reverse any call. State at the top how the order was set and what the verification
    rested on. Save all three as artifacts.

13. Ask me for a paper or grant I am currently writing, plus its .bib. Then check it
    against my verified shortlist, with recent co-authors included this time, since a
    bibliography is not a referee list and citing close collaborators is normal. Check
    against the verified list rather than a rank cutoff: a cutoff silently skips
    verified people below it, which in one test missed 16 of 24 real gaps.

    Before you show me anything, check the author list of every suggested paper. If I
    am an author on it, say so and reframe it: that is a paper of mine I have failed to
    cite, not a gap attributable to the candidate, and citing it does nothing about them.
    In testing, the single gap reported for the second-ranked candidate turned out to be
    a paper the user had written and led.

    Then go through the rest with me row by row and tell me whether each suggested paper
    genuinely belongs in the section proposed, on the merits. The matching underneath is
    only word overlap between their title and my section text, so it has no idea what my
    paper argues, and a match on three generic words is not an argument. Say plainly
    where a citation is not warranted. Never advise padding a reference list.

    Where the also_covers column is populated, flag it: one added reference would close
    several gaps at once. It is often empty for every row, which is normal and means no
    two candidates happened to share a best-matching paper.

14. Finally, tell me in three sentences how to re-run this in a month, and what I need
    to do when I publish a new paper.

If we are interrupted, look at what is already in data/ and resume from there rather
than starting over.
```

---

## What you will have at the end

- `referees_shortlist.md` and `.csv`: your candidate referees, verified one by one and
  split into two tiers.
- `referees_excluded.md`: everyone dropped and why.
- `citation_gaps.csv`: which of them your draft fails to cite, and where each would go.

Expect roughly an hour, most of it waiting while step 11 runs. Of the 14 instructions,
seven put a question to you: your CV, your ORCID, your current university, your
conflicts of interest, whether your first-author papers came from somebody else's lab,
the co-author window, and the manuscript to check. You will also be asked to confirm the
extracted DOI list before anything runs, and to set up the OpenAlex credential if it is
not already there. The rest the assistant does on its own.
