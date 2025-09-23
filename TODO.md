# SkyDesk To‑Do

- [x] Surface success confirmations (toasts) after save
- [x] List persisted leads on the dashboard (totals + recent)
- [x] Add Active To‑Dos panel on dashboard
- [x] Align Enquiry layout to two-column detail view
- [x] Remove Travellers card; move Communication into right column
- [x] Add top tabs (Overview • Communication • Documents) on quote/booking
- [x] Add “Log new touchpoint” modal (UI only)

Engineering
- [ ] Persist Communication modal submission (form_type='log') to record.json
- [ ] Add MAX_CONTENT_LENGTH (10MB) to protect uploads
- [ ] Basic server-side email/phone validation on Enquiry
- [ ] Tests: payload builder, routes, persistence round‑trip
- [ ] Clean up legacy JS blocks and duplicate scripts
- [ ] Hash deep-links for tabs (e.g., #communication)
- [ ] Sync toggle/delete with `todos.json` index or document that it is append‑only

Design/Brand
- [ ] Replace placeholder logo with SkyDesk asset
- [ ] Document JSON schema and archival strategy
- [ ] Expand copy and empty states for all tabs

User added
- [ ] Change lead storage structure to file/lead for more modular storage
- [ ] Add file upload to Enquiry for uploading files and docs for future reference

Quote/Booking LLM loop (status)
1. Add new lead → New page [done]
2. Choose Quote/Booking [done]
3. Upload PDF + notes → submit [done]
4. Parse via LLM [done]
5. JSON returned [done]
6. Confirmation page for edits [done]
7. Save under lead_id, redirect to details [done]
