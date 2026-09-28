# Reproducing the ICLR 2026 archive screen

This is deterministic candidate screening, not automated peer-review correctness assessment. It preserves valid zero ratings and exact fractional means. Author identities and signatures are not exported; generic roles are retained. The output is a private research queue and must not automatically replace published articles.

Source: https://github.com/qhjqhj00/iclr-openreview-reviews/releases/tag/v1.0 (author-reported snapshot date2026-05-08).

Extract the2026 `papers.jsonl` and `reviews.jsonl` from `iclr.tar.bz2` into a private directory. The scan streams notes grouped by forum and fails if a forum is split into multiple groups.

```bash
python pipeline/tools/scan_archive.py \
  --papers /private/iclr2026/papers.jsonl \
  --reviews /private/iclr2026/reviews.jsonl \
  --source-url https://github.com/qhjqhj00/iclr-openreview-reviews/releases/download/v1.0/iclr.tar.bz2 \
  --out .cache/archive-screen
```

The coverage file records source hashes, counts, exclusions and limits. Archive SHA-256: `350071daf25ebf1aef854ee1d5dc3a81834e1c468917c82a4f78af5548de34fc`.

Observed inventory:19,814 papers,284,355 unique notes,75,859 official reviews;340 papers lack notes in the archive. Mechanical cohort:13,699, including5,341 accepts and8,358 rejects. Primary exclusive exclusions:5,178 withdrawals,908 desk rejects,8 explicit nonassessment reviews,14 AC-identified review artifacts,4 cases with fewer than three valid reviews,2 blank placeholders,1 duplicate-reviewer case. The documented patterns are heuristics; they do not prove all remaining reviews are substantive. Policy mentions remain flags requiring contextual reading.

Thresholds produce329 accepted means≤4 and one rejected mean≥7. No case reaches a rejected mean≥7.5. These counts are not a misconduct estimate. Serious-error leads are an additional hand-selected research queue, not an exhaustive semantic search. The final public commentary inventory is generated independently from articles that have completed source reading and editorial checks.

The saved public `data/newsroom/coverage.json` discloses this distinction and sets `all_manuscripts_read` and `screening_is_semantic_review` to false. The original snapshot does not certify today's live OpenReview state or the exact chronological scoring stage. It is not the separate API pipeline's production dataset.
