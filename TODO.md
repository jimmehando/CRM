# SkyDesk To‑Do

- [x] Surface success confirmations (toasts) after save
- [x] List persisted leads on the dashboard (totals + recent)
- [x] Add Active To‑Dos panel on dashboard
- [x] Align Enquiry layout to two-column detail view
- [x] Remove Travellers card; move Communication into right column
- [x] Add top tabs (Overview • Communication • Documents) on quote/booking
- [x] Add “Log new touchpoint” modal (UI only)

Engineering
- [x] Persist Communication modal submission (stored in per‑lead communications.json)
- [x] Add MAX_CONTENT_LENGTH (10MB) to protect uploads
- [ ] Basic server-side email/phone validation on Enquiry
- [ ] Tests: payload builder, routes, persistence round‑trip
- [ ] Clean up legacy JS blocks and duplicate scripts
- [x] Hash deep-links for tabs (e.g., #communication)
- [x] Sync toggle/delete with `todos.json` (external file is now authoritative)

Design/Brand
- [x] Replace placeholder logo with SkyDesk asset (logo.png used for header + favicon)
- [ ] Document JSON schema and archival strategy
- [ ] Expand copy and empty states for all tabs

User added
- [x] Change lead storage structure to file/lead for more modular storage (comms + todos as separate JSON files)
- [x] Add file upload to Enquiry for uploading files and docs for future reference (also Quote/Booking)

Quote/Booking LLM loop (status)
1. Add new lead → New page [done]
2. Choose Quote/Booking [done]
3. Upload PDF + notes → submit [done]
4. Parse via LLM [done]
5. JSON returned [done]
6. Confirmation page for edits [done]
7. Save under lead_id, redirect to details [done]

Ideas

- Product & Workflow
  - [ ] Smart reminders (email/Slack) for due To‑Dos; snooze/defer
  - [ ] Calendar/timeline views for trips, due dates, payments
  - [ ] Kanban board for stages (Enquiry → Quote → Booking)
  - [ ] Global search/command palette to add notes/touchpoints/To‑Dos
  - [ ] Link Enquiry→Quote→Booking into a single case thread

- UX & Accessibility
  - [ ] Global keyboard shortcuts (add log/todo, save notes, switch tabs)
  - [ ] Drag‑and‑drop uploads with progress + AV indicator
  - [ ] Rich empty states and inline validation (email/phone masks)
  - [ ] Modal/tab a11y: focus traps, roles, ARIA labels
  - [ ] Time zones: capture user TZ; show relative times

- Data & Search
  - [ ] Full‑text search (SQLite FTS5 or Whoosh)
  - [ ] Filters: stage, date range, destination, consultant, overdue
  - [ ] JSON schema versioning + migrations for records/logs/todos
  - [ ] Export bundles (record + docs + comms/todos) for audit/handoff

- Reliability & Security
  - [ ] Auth + roles (consultant/lead/view); per‑lead permissions
  - [ ] CSRF protection; CSP; rate limits
  - [ ] File hygiene: MIME sniff, extension whitelist, size (10MB), AV scan
  - [ ] Audit trail of changes (who/when/what)
  - [ ] Backups/versioning for JSON or move to SQLite/Postgres

- LLM Quality & Guardrails
  - [ ] Validate against JSON Schemas; auto‑repair minor issues
  - [ ] Observability: prompt/response logs (redacted), latency metrics
  - [ ] Retry/fallback models; timeouts; background queue for heavy PDFs
  - [ ] Versioned prompt library with tests on sample docs

- Engineering Ops
  - [ ] Tests: routes, payload builders, persistence round‑trip, snapshots
  - [ ] CI/CD: lint/type (ruff/mypy), tests, preview deploys
  - [ ] Flask Blueprints (leads/uploads/dashboard); typed DTOs
  - [ ] Move inline JS to modules; optional build step (Vite/Rollup)
  - [ ] Dockerize; env‑based config; health/readiness endpoints
