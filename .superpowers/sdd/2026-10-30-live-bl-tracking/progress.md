# SDD ledger — plan: docs/superpowers/plans/2026-10-30-live-bl-tracking.md

Setup: Worktree created from merged PR head 9cc8c6f; plan file was untracked in source workspace and is not present here. Approved behavior from conversation: any GET /track/{BL} triggers live ZenRows lookup, returning BL container summary/details; preserve scheduled workflow.
Ruling: Continue from merged PR head rather than current master — the approved scraper fix is present here and is the user's active task base; cost if wrong: branch ancestry may include the feature commit even though it is already merged.
Pre-flight: Task 1 produces `scrape_bl(bl_number, zenrows_api_key=None)` consumed by Task 2 route. Use lazy import in route/module test so missing ADMIN_TOKEN environment in tests does not abort import; API independently validates ADMIN_TOKEN for save endpoint.

Task 1: complete (uncommitted in worktree; tests: `python -m unittest test_scraper.ScraperLiveBLTests -v` → 5 passed). Scraper parameterized; missing key and ZenRows errors typed; requests dependency added.
Task 2: complete (uncommitted in worktree; tests: `python -m unittest test_main -v` → 4 passed). GET route scrapes requested BL, validates identifier, maps errors 503/502; POST cache endpoint remains intact.
Task 3: complete (uncommitted in worktree; tests: full suite `python -m unittest discover -v` → 9 passed; compile and `git diff --check` passed). Added docs/live-bl-testing.md; verified existing scheduled workflow unchanged.
Final review: fresh reviewer found one Important distinction issue (unknown upstream HTML vs legitimate no-result response); fixed with RED→GREEN tests `test_scrape_bl_rejects_unrecognized_upstream_html` and `test_scrape_bl_returns_zero_for_recognized_empty_results_table`; full suite 9/9.
Final: minor (deferred): `TestClient` emits StarletteDeprecationWarning about httpx compatibility in local environment. Tests pass; update test client dependency only if warning becomes an issue.
