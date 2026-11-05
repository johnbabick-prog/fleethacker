# HATCH
**Readiness without reachback.** CDAO hackathon, 4–6 November 2026.

An offline maintenance administration prototype grounded in a local MH-60R reference corpus. Operational work orders and supply records are synthetic. Reference material remains local and is not included in this repository.

## Run
```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 scripts/ingest.py '/Users/johnbabick/Cloud/References/MH-60R-Maintenance/extracted data/text'
./start.sh
```
Open http://127.0.0.1:8765. The app needs no internet, CDN, external font, or cloud AI service at runtime. Provision dependencies and model files beforehand.

Start your local OpenAI-compatible inference server separately on port 8080. Set `HATCH_MODEL` to its loaded model ID if required. `HATCH_LLM_URL` defaults to `http://127.0.0.1:8080/v1/chat/completions`; non-loopback hosts are rejected. No model weights are bundled. When inference is unavailable, the app explicitly returns evidence-only results, not a generated answer.

## Working today
- SQLite database with three synthetic MH-60R detachment jobs and two demo inventory items.
- Local FTS5 reference retrieval with source module identifiers; local LLM receives retrieved excerpts and structured records.
- Completion notes, meter reading and optional PNG/JPEG evidence saved in encrypted payloads.
- Atomic event creation with optimistic version checks; duplicate completion rejected.
- Durable, idempotent simulated ship/shore receipts; shore delivery requires ship receipt.
- Interactive low-confidence review fixture and reviewed JSON download.
- Responsive browser UI served entirely from the device.

## Explicit prototype boundaries
This is not yet the full challenge implementation. OCR, actual scan-to-folder intake, calibrated token confidence, semantic Word/Excel template selection, and populated Office downloads remain to implement. The document screen is a labeled fixture, not OCR. Inventory is synthetic; no authoritative NSNs or live stock feed were found or imported. Personnel scheduling is not implemented.

Ship and shore are simulated receiver tables in the same database, not remote servers. Network selection is a demonstration control. Real transport authentication, reconciliation, ERP+ contracts and receiver-side business validation remain to implement. Current records represent administrative completion, never maintenance certification or release to flight.

Record payloads and attachments are encrypted using Fernet. The development key is a permission-restricted file under `data/`; production must use an OS credential store. The corpus index, IDs, receipt flags and database metadata are **not encrypted**. This is not an encrypted-database or CUI-compliant deployment claim. Use an approved encrypted volume/environment for the supplied corpus. Do not delete the device key while retaining records.

The sampled supplied modules carry CUI / Distribution Statement C markings. `data/` is ignored and source modules are not bundled. Review repository contents before sharing. Public demonstrations should use an approved synthetic corpus; the local UI can expose source text. Do not publish the runtime database or screenshots of restricted excerpts.

## Repository
- `hatch/store.py`: schema, encrypted record storage, retrieval, event queue
- `hatch/app.py`: local API and inference boundary
- `scripts/ingest.py`: transactional replacement of local text index
- `static/`: offline UI
- `docs/DEMO_STORY.md`: pitch, demonstration and scoring narrative
- `docs/ROADMAP.md`: remaining requirements and delivery sequence

## Verify
```sh
python3 -m unittest discover -s tests -v
```
Tests use an isolated temporary database and check encryption of payloads, stale update rejection, source preservation, and idempotent delivery.

## Procedure workspace and handwritten logs
The Maintenance procedure tab searches source modules, reconstructs their original text from overlapping import windows, and presents source-ordered reading sections. These are not parsed or validated maintenance steps; figures and linked modules remain in the approved publication. Select a work order, load a module, acknowledge reviewed sections and save notes. Progress is encrypted, revision-bound and protected against stale updates.

Technician observations are stored with source module, work order, timestamp and ID. The local AI can brief the technician from these records, with an explicit unverified-observation status. No historical lessons are fabricated or pre-seeded. Without a local model, the original observations remain readable.

At the end of the procedure, upload an original PDF, JPEG or PNG handwritten log (10 MB maximum). Files are signature-checked, hashed, encrypted, linked to the work order and included in queued sync events. Originals can be downloaded again. Upload works after administrative completion too. This is real file capture, **not OCR**: uploaded logs remain marked “OCR pending,” separate from the illustrative document-review fixture.

Additional API tests require `pip install httpx`; run `python3 -m unittest discover -s tests -v`.

The procedure workspace now opens with a paginated library of all imported source modules (24 per page). Each card displays the original title and module identifier. Search filters titles and identifiers; selecting a card opens the full source in the existing follow-along view. Overlapping corpus chunks are grouped into one library entry per source. Reference modules remain labeled as such rather than being represented as validated maintenance tasks.

## Share with teammates on the same network
Run `./share.sh` and keep the terminal open. This starts a separate instance on port **8766**, bound to all network interfaces. The original private instance on 8765 can remain running. Shared mode uses `data/team-review/`, seeded with three explicitly synthetic administrative workflows, and never imports the MH-60R reference library. Its jobs, uploads, events and key are separate from private data.

Find this Mac’s local IP under System Settings → Wi-Fi → Details → TCP/IP (or the corresponding Ethernet settings). Share `http://<Mac-IP>:8766` with teammates on the same reachable network. If macOS asks, allow incoming connections for Python. Guest networks or client isolation may prevent access. Stop sharing with Control+C in the sharing terminal.

This review server has no login, TLS or per-user isolation: visitors can change the shared demonstration records and download shared uploads. Use synthetic information only. Do not port-forward or expose it publicly. Internet-wide review needs a separate deployment with authentication and TLS. The local model connection remains loopback-only on the host Mac.

## Right-side local AI chat
The persistent chat pane sends the selected module section, recorded observations and recent conversation turns to the host's loopback inference endpoint. Source excerpts appear with each answer. Chat history stays in browser memory and clears on reload. Without a selected procedure, it searches the corpus. There is no cloud fallback.

For llama.cpp, start its local OpenAI-compatible server and set `HATCH_MODEL` to the loaded model ID. For Garrison, configure `HATCH_LLM_URL` to its actual loopback `/v1/chat/completions` endpoint **if that deployment provides the compatible API**; this integration has not been live-tested with Garrison. Example configuration for either compatible server:

```sh
HATCH_HOST=0.0.0.0 HATCH_LLM_URL=http://127.0.0.1:8080/v1/chat/completions HATCH_MODEL=your-loaded-model ./start.sh
```
Inference runs on the hosting machine when clients connect over LAN. It does not run separately on each visitor's device.

## Ship-class schematic library
Mission Workspace (01) includes a searchable ship-class dropdown, multiple-file upload, and class-filtered original downloads. PDF, PNG and JPEG originals are accepted up to 20 MB each. Content and descriptive metadata are encrypted in SQLite; the class key remains plaintext for filtering. Originals receive independent IDs and SHA-256 hashes, so a later upload does not overwrite a prior drawing. This library is local to the running instance; schematics are not yet part of simulated ship/shore synchronization or AI retrieval.

`config/ship_classes.json` provides a broad named-class catalog covering surface combatants, carriers, amphibious ships, submarines, MSC/support ships, and selected future/legacy classes. It is not an exhaustive historical or authoritative current fleet inventory. Source references include the NAVSEA Naval Vessel Register, MSC inventory, and the public Navy equipment class list. Custom class entries become available in the dropdown after their first successful upload. No schematics are downloaded from these sources. On the unauthenticated team-review instance use synthetic drawings only, as all visitors can download saved files.

## My Watch and Job Workspace
01 is now My Watch: searchable jobs, open/completed/blocker filters, assignee/location, next-watch notes and Start/Continue actions. 02 is the unified Job Workspace: watch context autosaves after a short pause, with explicit saving/failure feedback and version-conflict protection. It brings existing source procedure, class schematic downloads, supply snapshot, log capture, completion and handoff into one page. Uploaded class drawings are lookup candidates, not verified hull-specific applicability. Draft autosave requires connectivity to the app host; it is not browser-offline storage. Reading acknowledgments still use the explicit Save progress button. Draft fields are included in the downloadable handoff and queued as events.

Presenter script: `docs/TALK_TRACK.md` (five minutes, thirty-second version, and judge questions).

## Demo work centers and sailors
My Watch filters by Electrical, Mechanical or SONAR and by FC1 Ochoa, FC3 Kluzak or FC2 Donohue. Assigned-to selection in the job workspace uses the same roster; existing free-text assignees are preserved. Demo assignments are illustrative, not qualifications or identity authentication.

Nine additional synthetic jobs are seeded once: one due today, one overdue and one completed for each center. Dates persist from first launch; the dashboard uses the host's current date and Monday–Sunday week. Due-this-week counts incomplete jobs due within that week; completed-this-week uses completion date; overdue means incomplete with a due date before today. Unscheduled earlier jobs remain visible under All work centers. Today's schedule links directly to synthetic administrative reference modules, not real equipment maintenance instructions. Schedule steps, parts-requirement assessment and experience-tailored automatic hints remain separate implementation work.

Dashboard navigation regression: `node tests/test_start_job.cjs` checks Start job selection/navigation, loader completion, error feedback and button recovery without a browser. My Watch now prioritizes the schedule and weekly counts; schematic and supply libraries are collapsed, and the promotional hero has been removed. Browser rendering/click verification must still be performed in the running app.

Demo procedure checklists now contain 12 synthetic administrative steps. Each checkbox saves through the revision/version-checked procedure API; selection follows the next unchecked step and local chat receives that step. Imported source modules retain the original reading-section presentation. Any of the three demo sailors may be assigned from a work-item card or the workspace header. Assignment updates the experience-aware greeting and model context while preserving existing work-item progress. Reassignment does not represent certification or transfer of sign-off authority.

## Ship identity and reusable troubleshooting
The Job Workspace now shows ship name, hull number, named class and equipment. These fields autosave with the work item and appear in the handoff. The class-history panel saves immutable, encrypted reports of symptoms, actions/findings and outcomes, including technician, originating ship, procedure-progress snapshot and evidence references. A repeated save of the same draft version returns the same report. Later draft changes do not rewrite earlier reports.

Search locally available reports by named class and equipment/symptom keywords. Broad hull types (DDG, CVN, etc.) are insufficient for class reports; select a named class. Local AI receives the current ship context and up to five recent reports from the same class, labeled unverified with originating-ship attribution. A class match is not proof of equipment/configuration applicability. Each report queues a synchronization event, but real ship-to-ship/shore distribution, review approval and fleet-wide ingestion remain unimplemented. This is a local class-history foundation, not a connected fleet repository.

## Normalized ship directory
The workspace presents class first, then an accessible searchable ship dropdown. No class filter shows all imported ships alphabetically (ignoring USS/USNS prefixes); class selection limits the second dropdown. Search accepts a name or hull number. Choose a result to save `ship_id`, canonical ship name, hull number and named class; the server derives identity from the ID, ignoring mismatched typed identity fields. Older free-text records remain readable until reselected. Class changes clear the current selection. The schema still accepts legacy/manual draft records for backward compatibility.

`config/ships.json` contains 461 entries across 96 class labels, extracted on 2026-11-04 from the current-ships tables at https://en.wikipedia.org/wiki/List_of_current_ships_of_the_United_States_Navy . Scope includes commissioned, non-commissioned, support, Ready Reserve Force and reserve vessels, with source categories retained. It excludes future ships and historical vessels outside those tables. Source listings may lag commissioning/decommissioning; this is not authoritative readiness data. No homeports or operational details were imported. Each record retains its source URL. Hull numbers are distinct from class names, and hull-less entries use stable name IDs.

To refresh after reviewing changes:
```sh
curl -L -A 'Mozilla/5.0' 'https://en.wikipedia.org/wiki/List_of_current_ships_of_the_United_States_Navy' -o /tmp/ships.html
node scripts/import_ship_directory.cjs /tmp/ships.html
```
The import validates identity fields and unique IDs. Runtime selection is offline; it does not contact the source site.

The workspace's visible class selector now uses hull-type codes (DDG, LCS, ESB, CVN, etc.). DDG includes both Arleigh Burke and Zumwalt; LCS includes Freedom and Independence. The selected ship still stores its named class internally for class-specific troubleshooting and schematic lookup. Hull-less directory entries appear under OTHER. With no type selected the full alphabetical directory remains available.

## Replaceable destroyer equipment demo
`config/demo_equipment.json` contains eight publicly documented system names: six Arleigh Burke candidates (LM2500, SPY-1D, SPS-67, SPS-64, SQQ-89 and SPY-6) and two Zumwalt candidates (SPY-3 and IPS). Official Navy source links accompany every entry. Direct downloads returned 403; names were extracted from publicly indexed official-page excerpts. This is not an actual installed-equipment list: variants and flights differ, particularly SPY-1 versus SPY-6.

Select a DDG ship to populate Equipment / system. Other ship classes display “No demo register.” Each test asset has a ship-scoped ID, a synthetic location and a fictitious test-kit requirement. SQLite table `demo_equipment_stock` holds seeded ship-specific balances. Availability is calculated as max(0, on hand − reserved), producing Ready, Short or Unknown. These are fictional scenario results, not valid part compatibility, repair requirements or operational readiness. Local AI receives the selected fixture with explicit synthetic labeling. Changing ships clears equipment; the backend rejects an equipment ID from another ship.

Replace the catalog with an authorized installed-asset import keyed by ship ID and stable asset/model IDs. Replace the demo stock adapter with ship inventory snapshots and validated procedure requirements. Existing record names remain visible until a new selection is made. Neither source webpages nor real operational inventories are contacted at runtime.

## Equipment PDF repository and retrieval
In Job Workspace, select a ship and equipment, then expand **Equipment schematics & manuals**. Upload multiple PDFs, enter the revision, and choose this ship/equipment (default) or the same model across the named class. Each original is preserved with a checksum and revision; subsequent uploads do not overwrite older documents. Older class-only uploads remain under My Watch and are not automatically mapped to equipment.

`hatch/equipment_docs.py` stores encrypted PDF originals and per-page extracted text in SQLite. Local retrieval ranks matching text chunks from only the selected equipment's applicable documents and adds up to five excerpts to AI context with document IDs, names, revisions and page numbers. The repository metadata and extraction status are also available to the assistant. This is lexical text retrieval, not diagram interpretation. The local page viewer renders every PDF page as a PNG, preserving raster images and vector diagrams, including graphics on pages with text. It labels text, graphics/scans, and likely blank pages. Graphics detection is structural, not semantic: tables and borders also count. Existing uploads work without re-uploading. OCR is still needed to search scanned text. No OCR, visual circuit reasoning, automatic applicability verification, supersession policy or fleet PDF transport is implemented. These documents remain local to the instance.

Limits: 20 MB and 500 pages per PDF. Password-protected or damaged PDFs are rejected. Install `pypdf` through `requirements.txt` before starting the updated backend. Equipment-document tests exercise actual in-memory PDF text extraction, ship/class scope, selected-equipment isolation, source citations, original download integrity and image-only/invalid-file handling.

The equipment PDF upload panel now includes an explicit equipment dropdown, synchronized with the workspace selection, and a scope/destination summary. New uploads atomically queue an `equipment_document_uploaded` event containing the encrypted PDF package and distribution metadata. Ship scope retains the originating ship ID; class scope targets the same named class and equipment model. `/api/ships/{ship_id}/equipment-document-manifest` demonstrates cloud-pull eligibility from acknowledged local shore receipts. Tests verify ship-only isolation, class/model matching, pre-acknowledgment absence and retry-safe receipt behavior. This is a local simulator, not deployed cloud transport or real remote ingestion. Existing pre-change PDFs are not retroactively queued.

### Step coaching and synthetic performance

`config/demo_performance.json` contains fictional training history for the nine demo tasks: 12 completions per task for FC1 Ochoa, four for FC2 Donohue, and none for FC3 Kluzak. Step-specific lessons and correction examples are labeled synthetic and matched by procedure revision. These are not personnel records or qualification evidence. Actual saved observations remain separate in the encrypted database.

Checklist navigation immediately updates the chat panel's current-step instruction. `/api/step-coaching` supplies local record-based reminders without waiting for LLM inference. “Ask AI about this step” sends the current step, experience profile and relevant history to the configured local model for explanation. Changing steps invalidates stale reminder responses; checked boxes are not treated as evidence of physical execution.

## Deployment candidate and security evidence

The repository now includes a non-root Dockerfile, hash-locked Python dependencies, a Helm chart, a draft Zarf/UDS package definition, and a non-submittable Iron Bank manifest example. Actual local scan reports and disconnected smoke-test evidence are generated under `security/evidence`; see [security/READINESS.md](security/READINESS.md) for commands, findings and remaining gates. Open **06 Deckplate impact → View security scans & deployment evidence** for the demo. This is not Iron Bank acceptance, UDS validation or operational authorization.
