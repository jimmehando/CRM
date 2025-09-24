# agents.md

## Mission Snapshot
- Rebrand Nova CRM -> **SkyDesk** across templates.
- Build lead intake workflow with JSON persistence.
- Polish UI interactions (navigation links, accent styling, anchored back button).
- Add To‑Do workflow and dashboard aggregation.
- Add top tabs (Overview • Communication • Documents) and comms modal.
 - Persist comms + To‑Dos to dedicated JSON files per lead.
 - Add document uploads on all lead detail pages.
 - Shared Quote/Booking detail template (record_detail.html).

## Active Agents

### Backend Integrator
- Owns Flask routing (`dashboard`, `leads_new`).
- Persists POSTed form data to `leads/<quote-id>.json`, handling sanitisation and deduping.
- Ensures redirect flows and flash or confirm hooks are in place.
 - Recent: dashboard shows totals + recent + Active To‑Dos; LLM ingestion wired for quotes/bookings; To‑Do assistant writes `todos.json`; Communication modal persists to `communications.json`; MAX_CONTENT_LENGTH added; `/todos` route added; document uploads saved under `documents/` for all leads.
 - Next: auth + CSRF, tests, search/filters; migrate any legacy inline `todos`/`communications` into external files.

### Frontend Stylist
- Maintains Tailwind-driven presentation.
- Aligns new views with the SkyDesk theme (cards, selects, buttons, layout rhythm).
- Keeps navigation consistent (`/leads/new`, dashboard CTA, bottom-left back button).
 - Recent: success toasts added; enquiry detail aligned to two-column; Travellers card removed; Communication moved right; top tabs added; comms modal implemented with a11y; tabs deep-linked via URL hash; dashboard To‑Dos refined (cap, actions, layout, color‑coded pills).
 - Next: unify pill palette in style guide, extract shared JS for tabs/modals, polish mobile spacing.

### Brand Steward
- Tracks product naming, assets, copy voice.
- Updated titles, README headline, and template branding to SkyDesk.
- Curates Style Guide and TODO artefacts for the team.
 - Recent: Style Guide expanded with Tabs and Modals; PNG logo added as app icon + favicon; dashboard pill colors tuned.
 - Next: expand marketing copy, document JSON schema, asset variants (favicon sizes).

## Workflow Notes
1. Use `TODO.md` to prioritise engineering and design follow-ups.
2. Reference `STYLE_GUIDE.md` before introducing new UI components.
3. Commit JSON archives only for fixtures; `leads/` is gitignored by default.
4. Run lightweight Flask tests when touching persistence logic.
5. Communications and To‑Dos now persist to `communications.json` / `todos.json` within each lead directory. Inline arrays are read for backward compatibility only.
