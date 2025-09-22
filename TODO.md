# SkyDesk To-Do

- [ ] Surface a success confirmation on the dashboard after saving a lead (toast or banner).
- [ ] List persisted leads on the dashboard by reading the JSON archive.
- [ ] Add server-side validation for required lead fields with friendly error states.
- [ ] Introduce automated tests (Flask unit tests + snapshot of saved JSON structure).
- [ ] Package configuration for deployment (environment config, production server entrypoint).
- [ ] Replace the placeholder logo with SkyDesk branding assets.
- [ ] Document JSON schema and archival strategy for downstream integrations.

- User added:

- 1. Change lead storage structure to file/lead for more modular storage
- 2. Add file upload to enquiry for uploading files and docs for future reference


- Quote/Booking LLM loop

1. User presses Add new lead button on dashboard which takes them to the new lead page
2. they click either the quote or bookiing button depending on the status of the booking
3. They upload the quote/booking PDF and any notes they want to add and press submit
4. The pdf gets parsed into txt format and sent off to the llm with prompt, message and txt from pdf
5. LLM returns json format.
6. User is taken to a "confirmation page which then shows them everything the llm parsed and gives them an oppertunity to correct or add information
7. User saves and quote/booking is saved the same way that enquiry is, in its own folder, but this time using the lead_id as it's id and the user is then sent to the quote/booking details page