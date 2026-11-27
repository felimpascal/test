# Clinic supply service

Local synthetic Flask/SQLite application. Install requirements and run python app.py. Demo tokens: central, north, south, auditor. No real credentials or data.

Contract:
- Central staff manage receipts and approve requests; clinic staff create and view requests for their own clinic only; auditors read all data but cannot mutate.
- Requests reserve no stock until approval. Approval reserves stock exactly once. Dispatch consumes the reservation and transfers physical stock atomically. Cancellation releases reservations only for approved requests. Dispatched requests cannot be cancelled.
- Quantities are positive JSON integers. SKU and clinic identifiers are case-insensitive. References are unique per clinic. Repeating a creation with identical normalized payload returns the existing request; a different payload with the same reference returns conflict.
- Available stock equals physical stock minus reserved stock. No negative quantities or reservations exceeding physical stock. All state changes and audit records commit together.
- Reports show current stock, reservations and available stock per location, and reflect committed changes immediately. Clinic users see only their own location.
- Request lists support status filter and cursor pagination, ordered by increasing ID. Cursor is exclusive; no skipped matching records.
- Errors: malformed input 400, forbidden 403, missing resource 404, conflicting state 409.
