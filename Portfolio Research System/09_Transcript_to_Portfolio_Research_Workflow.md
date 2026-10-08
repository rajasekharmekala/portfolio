# Transcript-to-Portfolio Research Workflow

## Purpose

The Transcript-to-Portfolio Research Workflow turns a meeting transcript into a
reviewable, evidence-based shortlist workflow without immediately mutating an
investment account.

The workflow is designed for the Wealthfolio portfolio model and its four
strategy buckets:

- Core Alpha
- Tactical / Momentum
- Leveraged
- Options

## Support-Aware Research Handoff

Transcript extraction and strategy-fit triage must not manufacture entry
levels. The research stage must separate candidate quality from entry timing:
for every candidate that could receive new capital, it should verify and report
the nearest support/MA confluence, support type, distance in `ATR(14)`, entry
zone, stop below support, target, and reward-to-risk. An extended candidate is
retained as research or `WAIT_FOR_SUPPORT`; a broken-support or incomplete-data
candidate is `NO_TRADE / RESEARCH_REQUIRED`. Existing holdings may remain on
`HOLD` when their thesis is intact.

It supports transcripts pasted into the UI or uploaded as text files. A
provider extracts securities and evidence, the user reviews the extracted
items, research and reviewer stages are run, and only explicitly selected
items are added to selected account shortlists.

## End-to-end flow

```text
Transcript
   |
   v
Intake and persisted run
   |
   v
Security extraction
   |
   v
India / US / Other classification
   |
   v
Strategy-fit triage
   |
   v
Research batches
   |
   v
Independent reviewer
   |
   v
Human approval and curation
   |
   v
Account and strategy-bucket allocation
   |
   v
Deduplicated shortlist creation
   |
   v
Existing deep-audit workflow
```

The workflow is intentionally human-in-the-loop. Extraction, research, and
review do not create shortlist candidates. Candidate creation happens only
after the user selects securities, destination accounts, and strategy buckets.

## What the workflow produces

For each extracted security, the UI can show:

- Ticker or best-effort symbol
- Company or security name returned by the provider
- Regional grouping: India, US, or Other
- Transcript evidence and supporting quote
- Identity uncertainty where speech-to-text makes the company ambiguous
- Research output
- Portfolio-bucket fit
- Risks and invalidation considerations
- Reviewer feedback and verdict
- Whether the security is already held or shortlisted

The provider output is retained as a persisted workflow transcript so the
research decision can be reviewed later. It is not treated as a verified
recommendation or an automatic trade instruction.

## Provider support

The workflow uses a normalized provider adapter interface. The UI exposes:

| Provider | Runtime behavior | Current status |
| --- | --- | --- |
| Built-in agent | Uses the existing Wealthfolio AI chat service and enables the `web_search` tool on the web server path. | Wired, but requires a valid configured/enabled AI provider. |
| Claude CLI | Runs `claude --print`. | Smoke-tested successfully. |
| GitHub Copilot CLI | Runs `copilot -p`. | Smoke-tested successfully and used for transcript extraction. |
| Agy CLI | Runs `agy --print`. | Smoke-tested successfully. |

CLI execution reports launch failures, non-zero exit codes, stderr, empty
responses, and timeouts. The configured subprocess timeout is 900 seconds.

The built-in web path is not a model by itself. It delegates to the existing
AI provider configuration. For example, an isolated smoke test failed with:

```text
Azure OpenAI requires an endpoint URL.
```

This means the workflow code was reached, but the selected AI provider was not
configured sufficiently. Configure and enable a supported provider in
**Settings > AI Providers** before selecting **Built-in agent**.

The desktop/Tauri built-in path is less complete than the web path and may use
the deterministic core fallback when a richer AI adapter is not wired into the
desktop environment. Use the web runtime for the most complete built-in
provider behavior.

## Architecture

### Frontend

The primary UI is:

```text
apps/frontend/src/pages/transcript-research/transcript-research-page.tsx
```

It owns:

- Transcript paste and text-file upload
- Provider selection
- Run creation and saved-run loading
- Extraction, research, and reviewer controls
- India / US / Other security cards
- Security selection and removal from the user's working set
- Destination-account selection
- Four strategy-bucket assignment
- Duplicate display and skip behavior
- Shortlist creation
- Workflow deletion

The Research page integration is in:

```text
apps/frontend/src/pages/research/research-page.tsx
```

The shared frontend adapter functions are in:

```text
apps/frontend/src/adapters/shared/research.ts
apps/frontend/src/adapters/web/core.ts
apps/frontend/src/lib/types.ts
```

### Web backend

The web API is implemented in:

```text
apps/server/src/api/research.rs
```

The workflow routes are:

```text
GET    /api/v1/research/runs
POST   /api/v1/research/runs
GET    /api/v1/research/runs/{id}
POST   /api/v1/research/runs/{id}/stages
DELETE /api/v1/research/runs/{id}
```

The web built-in adapter uses the existing `ChatService` and allows
`web_search`. CLI adapters are registered alongside it.

### Desktop backend

The Tauri command surface is implemented in:

```text
apps/tauri/src/commands/research.rs
apps/tauri/src/context/providers.rs
apps/tauri/src/context/registry.rs
apps/tauri/src/lib.rs
```

### Core workflow

The provider abstraction and execution logic are in:

```text
crates/core/src/research/provider.rs
crates/core/src/research/workflow_model.rs
crates/core/src/research/workflow_service.rs
crates/core/src/research/workflow_traits.rs
```

The workflow service:

1. Validates and persists the transcript run.
2. Executes the requested provider stage.
3. Stores provider output as transcript entries.
4. Extracts dollar-prefixed ticker mentions while ignoring dollar amounts.
5. Keeps evidence context bounded to the relevant ticker block.
6. Batches research and reviewer prompts into groups of 24 securities.
7. Avoids adding research/reviewer output back into the extracted-mention list.
8. Persists reviewer results and derives a review verdict.
9. Updates the run state.

### Storage

The SQLite implementation is in:

```text
crates/storage-sqlite/src/research/workflow_model.rs
crates/storage-sqlite/src/research/workflow_repository.rs
crates/storage-sqlite/migrations/2026-08-20-000001_research_workflow/
```

The workflow stores:

- Research runs
- Transcript entries
- Extracted mentions
- Typed strategy-fit results
- Reviewer results

Foreign-key cascade behavior removes child transcript, mention, and reviewer
records when a workflow run is deleted.

Shortlist candidates remain separate from workflow records. This allows a user
to discard a run or individual securities without leaving partially created
portfolio objects.

## Deduplication and cleanup behavior

When adding selected items to a shortlist:

- A held symbol is skipped.
- A symbol already shortlisted for the destination account is skipped.
- Multiple destination accounts can be selected.
- Candidate creation is tracked sequentially.
- If a later candidate creation fails, candidates created earlier in that
  operation are deleted as a rollback attempt.
- Deleting a workflow removes its persisted workflow children through cascade
  deletion.

The workflow does not delete existing user holdings or existing shortlist
candidates. Those are real portfolio records and require an explicit user
action.

## Implementation plan

### Completed foundation

1. Define provider-neutral workflow and stage models.
2. Add web and Tauri workflow command/API surfaces.
3. Persist runs, transcript entries, mentions, and reviewer results.
4. Add the Transcript Workflow tab to Research.
5. Add paste and text-file intake.
6. Add Claude, Copilot, and Agy subprocess adapters.
7. Add built-in web-provider integration through the existing AI service.
8. Add regional grouping and four-bucket selection.
9. Add duplicate prevention and rollback cleanup.
10. Add workflow deletion with child-record cleanup.
11. Fix ticker parsing for markdown and compact provider formats.
12. Batch large research and reviewer requests to avoid one oversized CLI
    request.
13. Persist and validate strategy-fit results per extracted mention before
    research can proceed.

### Remaining hardening

1. Complete browser-level validation of extraction, strategy-fit triage,
   research, reviewer, and
   shortlist stages after batching.
2. Add a first-class persisted report schema instead of relying primarily on
   provider transcript text.
3. Persist explicit region, identity confidence, evidence claims, inclusion or
   exclusion decisions, source URLs, thesis fields, risks, and invalidation
   rules as structured records.
4. Add a user-visible remove or reject action for each extracted security,
   rather than only excluding it from the current selection.
5. Add progress and cancellation for multi-batch research and reviewer stages.
6. Wire the same web-enabled built-in behavior into the desktop runtime, or
   clearly label the desktop fallback in the UI.
7. Add stable browser E2E coverage for the workflow using a fresh database.
8. Add explicit failure-injection coverage for candidate rollback and cascade
   deletion.
9. Add provider-specific output normalization so company names, exchange
   suffixes, and uncertain identities are displayed consistently.

## Running the workflow in the UI

### 1. Start the web application

From the repository root:

```bash
pnpm run dev:web
```

The normal local web address is:

```text
http://localhost:1420
```

For an isolated E2E database, prepare it before starting the server:

```bash
node scripts/prep-e2e.mjs
pnpm run dev:web
```

Do not use an existing production or personal database for validation runs.

### 2. Complete onboarding if needed

Open the app and complete the initial onboarding flow. Create or select at
least one investment account. The workflow needs an account scope before it
can add candidates.

### 3. Configure the built-in provider, if using it

In the app:

1. Open **Settings**.
2. Open **AI Providers**.
3. Configure an available provider, including its API key and endpoint when
   required.
4. Enable the provider and choose a model.
5. Return to Research.

If this is not configured, select Claude, Copilot, or Agy instead.

### 4. Open Transcript Workflow

1. Open **Research**.
2. Select the target account from the account selector.
3. Select the **Transcript Workflow** tab.
4. Confirm the page shows the selected destination account.

The direct route shape is:

```text
http://localhost:1420/research?account=<ACCOUNT_ID>&tab=workflow
```

### 5. Upload or paste the transcript

1. Enter a descriptive run title.
2. Select **Built-in agent**, **Claude CLI**, **GitHub Copilot CLI**, or
   **Agy CLI**.
3. Either paste the transcript into the text area or choose **Upload text
   file**.
4. Select **Start extraction**.

The first stage only extracts evidence and securities. It does not add
anything to the account.

### 6. Review extracted securities

Review the three region cards:

- India stocks
- US stocks
- Other

Check ticker identity, company name, transcript evidence, and uncertainty.
Speech-to-text errors must be treated as uncertain rather than silently
corrected.

Select only the securities that should continue. Do not select every
transcript mention automatically.

### 7. Run strategy-fit triage

1. Select **Run Strategy Fit Triage**.
2. Review the tentative strategy-book fit and evidence score for every mention.
3. Use the Core Alpha, Tactical / Momentum, Leveraged, and Options filters to
   narrow the ledger.
4. Select only the securities that should continue to comprehensive research.

This is a lightweight filtering pass based on transcript evidence. It is not a
valuation report, price target, or investment approval.

### 8. Run research and reviewer stages

1. Select **Run Candidate Research & Strategy Review**.
2. Wait for the research output to appear.
3. Read the thesis, current facts, evidence, portfolio fit, risks, and
   invalidation rules.
4. Select **Run reviewer**.
5. Read reviewer corrections and the final verdict.

Large runs are processed in batches. Research output is advisory and must be
checked against primary or otherwise reliable sources before capital is
allocated.

### 9. Choose accounts and strategy buckets

1. Under **Destination accounts**, select one or more accounts.
2. Select each security's strategy bucket:
   - Core Alpha
   - Tactical / Momentum
   - Leveraged
   - Options
3. Re-check that the bucket matches the intended use. A security discussed as
   a long-term business is not automatically a Core Alpha candidate.

### 10. Add selected securities to the shortlist

Select **Add selected to shortlist** only after reviewing the evidence and
reviewer output.

The workflow skips securities already held or already shortlisted for the
destination account. It creates candidates with a research-in-progress status
and keeps the originating run ID in the notes and thesis context.

The existing deep-audit callback is then invoked for each created candidate
when available.

### 11. Delete or clean up

To discard the entire workflow:

1. Select **Delete workflow**.
2. Confirm the success notification.

This removes the run and its transcript, mentions, and reviewer records. It
does not remove existing holdings or candidates.

To remove a candidate created by the workflow, use the normal candidate
deletion control in the Research page. Only delete candidates that belong to
the validation or workflow operation being corrected.

## Validation checklist

Before considering a run complete, verify:

- The correct account is selected.
- The transcript is the intended file or pasted content.
- Securities are separated into India, US, and Other correctly.
- Ambiguous speech-to-text identities are marked uncertain.
- Explicit holding claims are not inferred from proximity or wording.
- Research facts are separated from judgement.
- Risks and invalidation rules are present.
- Reviewer feedback has been read and corrections resolved.
- The intended strategy bucket is selected for every security.
- Existing holdings and shortlist candidates were not duplicated.
- No unwanted candidates remain after cleanup.
- Deleting a discarded workflow removes its child workflow records.

## Known limitations

This workflow is a decision-support feature, not an automated trading system.
It does not guarantee correct security identity, current market data,
investment suitability, or future performance.

The current implementation still has these quality boundaries:

- Provider outputs can contain ticker and company-name hallucinations.
- Exchange suffixes and regional classification may require manual review.
- The current persisted report is primarily transcript/provider text rather
  than a complete normalized research dossier.
- Built-in provider behavior depends on existing AI provider configuration.
- The desktop built-in path is not as complete as the web path.
- No automatic orders are submitted.
- A full 185-security research/reviewer run can be slow even with batching.

For portfolio decisions, treat the workflow as a structured research
accelerator with explicit human approval, not as an unattended investment
advisor.
