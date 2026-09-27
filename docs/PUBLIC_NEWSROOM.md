# OpenJudge public commentary edition

On 2026-09-28 (Asia/Shanghai), the owner explicitly requested a public, shareable website and stronger, evidence-grounded criticism of reviewers and ACs. This authorizes publication of this ten-case AI-assisted commentary edition. It does not represent independent human technical review or proof that a paper should have been accepted.

The public edition uses `commentary_public`, with explicit `human_reviewed: false`. It never creates an `approved` report or a fabricated editorial approval record. The original full-conference ranking pipeline and its production validation remain unchanged; those rankings are not included in this edition's deployment artifact.

`data/newsroom/articles.json` contains ten complete commentaries. The source evidence files retain only the previously collected public, anonymized notes, original public URLs and license metadata. `release.json` binds the exact article bytes and evidence hashes, score exclusions, archive date, and publication scope. Source archive: [v1.0](https://github.com/qhjqhj00/iclr-openreview-reviews/releases/tag/v1.0), 2026-05-08. No independent original-PDF verification or experiment reproduction is claimed.

Every article identifies its strongest finding as a documented error, record conflict, unsupported inference, standard dispute, or not established. A transcription error is distinct from an erroneous experiment; a discrepancy does not prove motive, and a score difference does not prove a wrong decision. Counterevidence and limitations remain attached to each finding.

The 2026-09-28 reviewer-method revision adds a five-part evidence audit to every article and a visible corrections record. The adopted workflows, exact upstream commits, source boundaries and validation contract are recorded in [REVIEWER_METHODS.md](REVIEWER_METHODS.md). Selected public arXiv passages were additionally inspected; they are explicitly versioned and do not establish that the reviewed submission PDF was identical.

## Build and validate

```bash
pnpm install --frozen-lockfile
pnpm --dir apps/web test
pnpm --dir apps/web exec tsc --noEmit
node scripts/build-newsroom.mjs
```

The built edition has fourteen HTML pages: home, ten articles, methodology, source scope and corrections. Private preview input remains opt-in and cannot enter the public loader. Public validation checks article/evidence digests, exact scores and decisions, source note IDs, all seven analysis roles, and honest publication metadata.

The source remains in yuhanlydia/OpenJudge. The public case website is hosted with Sites; its opaque identity is in `.openai/hosting.json`. The owner requested a globally shareable link; its audience is public. The existing GitHub Pages workflow remains available for a future validated full-conference release.

Changes to source evidence or analysis require updating the release digests and rerunning validation. User authorization to publish does not authorize unsupported allegations, deanonymization, or falsely claiming professional review.
