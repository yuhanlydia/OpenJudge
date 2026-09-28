# OpenJudge public commentary edition

The owner requested a public, shareable ICLR 2026 website, 100+ strictly selected cases, and detailed checks of reviewers, ACs and author responses. That instruction authorizes publication of this AI-assisted commentary edition. It does not represent independent human technical review or proof that a conference decision was wrong.

The current edition is defined by `data/newsroom/articles.json` and `release.json`. Exact case counts, evidence hashes and public-note inventory are generated from those files, not maintained as a separate hand-entered total. Five old articles remain accessible as historical material and do not count toward current selection.

## Selection and scope

Three exclusive desks:

- Serious errors require a documented material consequence for a core experiment, central theoretical claim, or factual premise of evaluation. A typo alone is insufficient. The `serious_basis` field identifies the claim, consequence and evidence.
- Low-score accepted: exact archived mean ≤4, accepted, at least three substantive reviews.
- High-score rejected: exact archived mean ≥7, rejected, at least three substantive reviews.

The complete ICLR 2026 slice of the [2026-05-08 public archive](https://github.com/qhjqhj00/iclr-openreview-reviews/releases/tag/v1.0) was mechanically screened: 19,814 papers, 284,355 unique notes, 75,859 official reviews. Documented filters leave 13,699 papers in the mechanical cohort; 329 low-score accepts and one high-score reject meet the numerical thresholds. This is not a claim to have read every manuscript or verified every review. The source archive is not certified complete or current relative to OpenReview today. Reproduction instructions are in [CORPUS_SCREENING.md](CORPUS_SCREENING.md).

New articles record a complete reading of the selected forum's archived notes, relevant manuscript access where available, and explicit limitations where a manuscript is unavailable. Later manuscripts are not silently substituted for what the original reviewer saw. Individual pages distinguish reported results from independently reproduced results; no experiment reproduction is claimed. A real 0 score remains valid. Reviewer followups, author summaries and AC forecasts of changed scores are identified separately.

## Reader contract

Every article starts with scores and outcome, exactly three paper-summary paragraphs (gap, method, comparative result), one principal contribution, every official reviewer, AC, and author-response/data consistency. Each finding includes evidence, a reasonable alternative explanation and its actual scope. Shorter new articles use the `reader-first` schema; the original seven-section format remains in historical articles and older case details.

The publication state is `commentary_public`, with `human_reviewed: false`. It never creates an `approved` report or fabricated human approval. Private drafts and raw manuscripts are excluded from the repository. Public evidence retains anonymous note roles, public URLs and license metadata. No identity investigation is performed.

## Build and validate

```bash
pnpm install --frozen-lockfile
python -m pip install -r pipeline/requirements.lock
PYTHONPATH=pipeline python -m pytest pipeline/tests -q
python -m unittest discover -s scripts/tests -q
pnpm --dir apps/web test
pnpm --dir apps/web exec tsc --noEmit
node scripts/build-newsroom.mjs
NEWSROOM_PUBLIC=1 TEST_DIST=../../dist pnpm --dir apps/web exec playwright test e2e/public-newsroom.spec.ts
python scripts/repository-guard.py
```

Public validation binds every article to exact scores, decisions, source note identities, evidence digests and the release inventory. It enforces the strict desk thresholds and honest scope metadata. Browser checks cover every article, mobile/desktop layouts, internal links, expanded text and no-JavaScript use.

The public website uses Sites at https://openjudge.longyunbo218.chatgpt.site; source is maintained in yuhanlydia/OpenJudge. The separate original API-based full-conference ranking pipeline remains unvalidated for production and is excluded from this deployment artifact. Its gate is not bypassed by the commentary release.
