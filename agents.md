# agents.md

## Mission Snapshot
- Rebrand Nova CRM -> **SkyDesk** across templates.
- Build lead intake workflow with JSON persistence.
- Polish UI interactions (navigation links, accent styling, anchored back button).
- Add To‑Do workflow and dashboard aggregation.
- Add top tabs (Overview • Communication • Documents) and comms modal.

## Active Agents

### Backend Integrator
- Owns Flask routing (`dashboard`, `leads_new`).
- Persists POSTed form data to `leads/<quote-id>.json`, handling sanitisation and deduping.
- Ensures redirect flows and flash or confirm hooks are in place.
- Recent: dashboard shows totals + recent + Active To‑Dos; LLM ingestion wired for quotes/bookings; To‑Do assistant writes `todos.json`.
- Next: persist Communication modal submit; add `MAX_CONTENT_LENGTH`; validation and tests; (optional) sync toggle/delete with `todos.json` index.

### Frontend Stylist
- Maintains Tailwind-driven presentation.
- Aligns new views with the SkyDesk theme (cards, selects, buttons, layout rhythm).
- Keeps navigation consistent (`/leads/new`, dashboard CTA, bottom-left back button).
- Recent: success toasts added; enquiry detail aligned to two-column; Travellers card removed; Communication moved right; top tabs added; comms modal implemented.
- Next: deep-link tabs via URL hash, refine modal a11y (aria attributes), unify spacing.

### Brand Steward
- Tracks product naming, assets, copy voice.
- Updated titles, README headline, and template branding to SkyDesk.
- Curates Style Guide and TODO artefacts for the team.
- Recent: Style Guide expanded with Tabs and Modals.
- Next: replace logo asset, expand marketing copy, document JSON schema.

## Workflow Notes
1. Use `TODO.md` to prioritise engineering and design follow-ups.
2. Reference `STYLE_GUIDE.md` before introducing new UI components.
3. Commit JSON archives only for fixtures; `leads/` is gitignored by default.
4. Run lightweight Flask tests when touching persistence logic.
