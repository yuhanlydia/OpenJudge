# Strict Newsroom Expansion Implementation Plan

> **For agentic workers:** Use executing-plans for Site-owner implementation; independent research agents follow the bounded research contract.

**Goal:** Expand the existing public ICLR2026 newsroom toward100+ carefully supported cases under stricter selection, preserving source and manuscript version boundaries.

**Architecture:** Existing Astro static website, structured article JSON and immutable anonymous evidence. Root owns Site changes and release; independent research batches supply complete articles and source access logs. Current qualifying and historical cases remain distinct.

**Tech Stack:** Astro/TypeScript, Python evidence processing, Playwright validation.

**Spec:** Existing static design at ../specs/2026-09-27-reviewcase-static-design.md, amended by owner's explicit requests in this session: three exclusive news desks, individual scores/outcome first, three-paragraph paper brief, one main contribution, every reviewer/AC/author checked, stricter serious threshold,100+ target, public Sites updates authorized.

## Constraints and review focus

- Serious findings need a material effect on a core comparison, theorem, or factual review premise. Typographic/isolated numeric errors are insufficient.
- Current low accepts mean<=4; current high rejects mean>=7; >=3 substantive reviews.0valid. No quota-based relaxation.
- Author claims and AC forecasts remain attributed. Later revisions do not establish earlier reviewer access.
- Every official reviewer, own-note citation, AC source and exact ratings/decision checked against evidence.
- Separate automatic full-corpus screening from selected-case reading and original manuscript access. Never claim human certification or replication.
- Preserve existing publicURL and historicalroutes. Native HTML details keep large lists and articles usable without JS.
- Repeatedly persist private research; only validated articles enter public source.

## Tasks

- [x] Research: recover and individually read selected forums and primary manuscript sections; write complete caseJSON plus researchlogs; exclude unsupported serious cases.
- [x] Contract: extend NewsArticle with reader-first format, current/historical status, serious_basis. Tests: thresholds4/7, substantive0 retained, historicalexception, missingmaterialbasis rejected.
- [x] Editorial integration: demote Uni3DAR percentageerror and Patch formula from severe; historicalout-of-threshold five; add qualifiednewarticles. Evidencehashmanifest generatedfromactualfiles.
- [x] Interface: dynamicthreeboards, firstsixcards then nativeexpandedlist; historicaldisclosure; exactacceptedtype; seriousconsequencepanel. Data/method/corrections dynamicallydescribe actualcoverage.
- [x] Releaseverification: Pythonpipeline/repository tests; productionarticle/source validation; frontendtests/typecheck/build; staticchecks; alldynamicroutes mobile/desktop/noJS/200%text inpublicbrowsertests.
- [ ] Publish: push exactSites source, package verifieddist, save/deploy publicversion; synchronize same source tree to authorizedGitHubrepo withoutforce. Report actualcasecounts andlimitations.

The user has already approved this scope and asked to continue. No additional design or deployment confirmation is needed.
