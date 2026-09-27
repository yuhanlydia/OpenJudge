# ReviewCase read-only data pipeline

Install Python 3.12 with `python -m pip install -e './pipeline[test]'`. Run `PYTHONPATH=pipeline python -m pytest pipeline/tests -q`.

The checked-in ICLR 2026 snapshot is an honest empty, blocked state. Anonymous OpenReview `/notes` returned `ChallengeRequiredError` HTTP 403 on 2026-09-27. The current data **must not pass production validation**. Do not work around the source access gate.

After authorized anonymous access is available, execute from the repository root:

```
PYTHONPATH=pipeline python -m reviewcase discover --venue ICLR.cc/2026/Conference --out .cache/discovery
PYTHONPATH=pipeline python -m reviewcase ingest --config config/iclr2026.yaml --out .cache/capture --resume
PYTHONPATH=pipeline python -m reviewcase normalize --capture .cache/capture --config config/iclr2026.yaml --out .cache/normalized
PYTHONPATH=pipeline python -m reviewcase rank --input .cache/normalized --min-reviews 3 --candidate-n 50 --out .cache/rankings
PYTHONPATH=pipeline python -m reviewcase export --input .cache/normalized --rankings .cache/rankings --reports content/reports --denylist config/denylist.json --out .cache/public-candidate
PYTHONPATH=pipeline python -m reviewcase validate-public --path .cache/public-candidate --mode production
```

Before ingest, inspect the actual review invitation schema and official forum samples; populate `score_schema` with exact allowed rating values, a `scale_id`, and `schema_hash` from a verified source, then set `verified=true`. A group field name alone is insufficient. `ingest` does one global submission enumeration and subsequently one forum query per discovered submission, capped at one request per second; a full conference refresh can take hours. The CLI logs only status/counts. Failures remain in ignored `.cache/` with per-forum coverage and do not become empty pages. Reusing `--resume` on a completed capture starts a fresh enumeration and forum refresh. Review the coverage and eligibility counts before using the candidate. The `export` command stages, validates, and replaces its `--out` directory only after validation; an incomplete candidate cannot replace a valid production directory. The release command archives a validated production candidate and requires a separate approval record ID and matching snapshot metadata.

For a report, generate a bundle with `bundle --forum ID --input .cache/normalized --out .cache/bundles`; privately prepare a schema-valid report. `check-report --report .cache/draft.json --bundle .cache/bundles/BUNDLE_ID.json` verifies exact source spans and hashes. An external editor supplies approval JSON binding `report_id`, `report_digest`, `bundle_hash`, `rubric_version`, `actor`, `approved_at`, and `record_id`. `publish-report --report ... --bundle ... --approval-record ... --out content/reports` imports an allowlisted approved report. Subsequent export attaches it to `paper.report` only while the evidence and rubric remain identical. Drafts must remain in `.cache/`; public pull requests are not private.

The first implementation does not download or parse PDFs. Paper versions remain `unknown` and original availability false unless separately verified and supplied. This prevents definitive original-versus-review contradiction claims. Preserve coverage limits and do not imply a professional factual audit from structural validation.
