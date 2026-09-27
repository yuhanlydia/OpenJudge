# ReviewCase contributor instructions

- Follow docs/superpowers/specs/2026-09-27-reviewcase-static-design.md.
- Anonymous public OpenReview sources only. Never bypass a challenge/permission barrier.
- Test fixtures are synthetic and must never enter production rankings.
- No paid model API, no cron, no dynamic backend. Manual quarterly refresh.
- Preserve exact score arithmetic, unknowns, conflicts, and evidence version boundaries.
- Never manufacture human approval. Draft reports remain private and git-ignored.
- A failed refresh must not replace the current validated snapshot.
- User selected yuhanlydia/OpenJudge and authorized initializing this repository with the project. GitHub Pages remains the hosting target; actual site publication requires valid real data and explicit publication approval.
- Before release run Python tests, production data validation, frontend tests/build, static checks, and browser tests. An intentional gate failure means not publishable.
