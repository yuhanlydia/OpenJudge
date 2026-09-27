# Reviewer-method audit, 2026-09-28

The owner requested use of reviewer skills, reviewed a three-case pilot, and then explicitly requested updating the live website. This revision applies a focused review-of-review workflow to all ten public articles. It is an AI-assisted editorial reassessment of public sources, not independent human technical certification.

## Method sources

- [paper-review.skill](https://github.com/jam-cc/paper-review.skill), commit `bb9900ff7a95e6a28092ab0a9e1d81098f41634e`: claim–evidence alignment, fair comparison conditions, limited-source review, reference verification, proportionate conclusions.
- [Review Feedback Agent](https://github.com/zou-group/review_feedback_agent), commit `669c00df741b6ba022eeed7f26d014b57c592697`: missed evidence, vague criticism, grounded novelty objections, contextual reading and critique of generated feedback.

The relevant Markdown instructions, examples and prompt source were read and adapted as analytical guidance. The upstream external-model API pipeline and its LLM reliability tests were not executed. No claims about automated accuracy or independent expert approval follow from using these methods. No third-party skill code is bundled into the website.

## Public audit contract

Every public article has an `audit` object containing `reviewed_at`, `claim`, `evidence`, `alternative`, `verdict`, `impact`, `scope`, and `source_ids`. The five analytical fields render directly in a reader-facing panel; scope identifies actual source access. Referenced IDs must exist in the article source list. Public builds reject missing scope, an empty counter-explanation, or untraceable sources.

Original article title, anonymous note provenance, score arithmetic, archive date, all seven analysis sections, human-review status and immutable evidence digests are retained. Public evidence remains the 2026-05-08 snapshot; newly accessed public manuscript versions are cited separately and never silently substituted for the original submission.

## Editorial checks

For each disputed claim: identify the precise statement and date; check the relevant evidence and experimental conditions; consider the strongest reasonable alternative; separate a demonstrated error from ambiguity, missing evidence or a standards dispute; state what can actually be inferred about the paper and the decision. A typo in a positive review does not establish a causal role in rejection. A later manuscript does not prove a reviewer saw the same content. Parameter-free NormalHedge does not make a whole system hyperparameter-free.

Each article's current finding must agree with its audit panel, headline and limitations. The public corrections page records material narrowing of the site's own earlier claims. Source inspection and case-specific reassessment are distinct from complete proof checking, implementation review and experiment reproduction, none of which are claimed here.

## Verification

Run the existing frontend tests and type check, `node scripts/build-newsroom.mjs`, and public-edition browser tests with `NEWSROOM_PUBLIC=1` and `TEST_DIST=../../dist`. Source validation binds the article digest, ten-case inventory, raw ratings, decisions, cited note identities and 176-note evidence archive. CI now explicitly validates and browser-tests the public edition in addition to the original project checks.
