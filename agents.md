# agents.md

## Mission Snapshot
- Rebrand Nova CRM -> **SkyDesk** across templates.
- Build lead intake workflow with JSON persistence.
- Polish UI interactions (navigation links, accent styling, anchored back button).

## Active Agents

### Backend Integrator
- Owns Flask routing (`dashboard`, `leads_new`).
- Persists POSTed form data to `leads/<quote-id>.json`, handling sanitisation and deduping.
- Ensures redirect flows and flash or confirm hooks are in place.
- Next: expose the archive on the dashboard, add validation and tests.

### Frontend Stylist
- Maintains Tailwind-driven presentation.
- Aligns new views with the SkyDesk theme (cards, selects, buttons, layout rhythm).
- Keeps navigation consistent (`/leads/new`, dashboard CTA, bottom-left back button).
- Next: add success toast on dashboard, align gutter spacing, refine form helper text.

### Brand Steward
- Tracks product naming, assets, copy voice.
- Updated titles, README headline, and template branding to SkyDesk.
- Curates Style Guide and TODO artefacts for the team.
- Next: replace logo asset, expand marketing copy, document JSON schema.

## Workflow Notes
1. Use `TODO.md` to prioritise engineering and design follow-ups.
2. Reference `STYLE_GUIDE.md` before introducing new UI components.
3. Commit JSON archives only for fixtures; `leads/` is gitignored by default.
4. Run lightweight Flask tests when touching persistence logic.
