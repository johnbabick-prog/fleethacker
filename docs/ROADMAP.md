# From hackathon foundation to end-to-end demonstration

1. **Local inference validation:** select the actual COTS device and model; measure memory use, latency and grounded answer accuracy. Confirm functionality with external networking disabled.
2. **Document ingestion:** printer writes PDF to onboard inbox; validate and hash files, preserve originals, render pages locally, queue processing. Add device-side upload for disconnected capture.
3. **Template repository:** version Word content controls and Excel named ranges; maintain field types, units and equipment applicability. Retrieve candidate templates, use a local model for semantic selection and field mapping, then validate schema. Ambiguity goes to a reviewer.
4. **Handwriting recognition:** integrate a local OCR engine exposing token-level recognition scores. Calibrate against a held-out labeled set. Preserve token geometry and original image; unknown scores and scores below 0.70 require verification. Do not label LLM self-assessment as statistical confidence.
5. **Office output:** deterministic template population after approval; create distinct DOCX/XLSX artifacts with provenance, template version, scan hash and reviewer history. Do not overwrite masters.
6. **Actual onboard service:** deploy a separately addressable receiver and encrypted storage; authenticate devices and users; send immutable event IDs and content hashes; acknowledge only after durable commit.
7. **Conflict handling:** inventory movements rather than quantity overwrite; record-version conflicts go to reconciliation. Never silently merge competing maintenance sign-offs. Inventory snapshots retain age and scope.
8. **Shore adapter:** implement a mock external ERP contract first, then map to authorized Navy ERP+ interfaces. Fleetwide visibility is acknowledged receipt plus accepted business state, not merely a successful HTTP response.
9. **Deployment hardening:** whole-database encryption, OS-managed keys, role separation, auditing, secure update/provisioning and backup/recovery. Model prompts and corpus contents must remain in the approved local environment.

## Core entities
Asset; work order; catalog item; stock snapshot; inventory movement; assignment; meter reading; evidence attachment; source module/revision; template/version; scan; extracted token/confidence; review; generated artifact; event; receiver receipt; reconciliation conflict.

The initial prototype implements a compact subset using encrypted JSON job/event payloads and FTS5 corpus records. Normalize entities and add migrations as the actual interface contracts become known.
