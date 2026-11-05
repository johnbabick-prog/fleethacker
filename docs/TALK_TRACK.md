# Fleet Tech — five-minute hackathon talk track

## Before presenting
Start the app and verify the local model is actually answering. If sharing outside the approved corpus environment, run `./share.sh` with synthetic references and uploads. Prepare one synthetic log image and one synthetic schematic under DDG. Keep one open demo work order. Set connectivity to Device only. No time savings or readiness gains are preclaimed.

## 0:00–0:40 — The sailor's problem
**Show My Watch.**

“It's watch turnover aboard ship. A maintenance job is still open, the last watch has observations, and shore connectivity is unavailable. The next sailor needs to know: What am I working on? What is blocking me? Where is the reference? And what has already been recorded?

Fleet Tech brings that work into one job workspace. Our principle is simple: the sailor records the work once, and the record travels when the network can.”

## 0:40–1:20 — Start from the job
**Click Start job. Set assignee, location, ship type, and a blocker.**

“Instead of beginning with a chatbot, we begin with the job. I can see the priority, name the watch team, record the equipment location, and make a blocker visible to the next watch.

These fields autosave. That status changes to Saved on host only after the server confirms the write. On a device running the host locally, that stays on the device. A browser connected to the shared demo still needs a connection to its host.”

**Wait for Saved on host; return to My Watch and click Continue job.**

“The context is still here. We don't make the next person reconstruct the last person's memory.”

## 1:20–2:10 — Evidence beside the task
**Open the procedure library and select a source. Expand supply and schematics.**

“The source reference, supply snapshot and uploaded class drawings are available from the job. I can record which source sections I reviewed and save observations without leaving the work.

This prototype preserves extracted source wording. These reading sections are not yet validated maintenance steps. Class-level drawings also require hull and revision verification; selecting DDG does not establish applicability to every destroyer.”

## 2:10–2:50 — Local assistance with traceable evidence
**Ask the local assistant about the selected reference. Show a source citation.**

“The assistant uses a model running on this host. It can help locate evidence and summarize recorded lessons. Observations retain their source and are labeled unverified; they are not substituted for approved instructions.

If the model is unavailable, Fleet Tech says so and leaves the underlying evidence readable. We do not present a canned response as AI inference.”

If the model is not running, say: “Today this portion is demonstrating retrieval and the model connection boundary, not live inference.”

## 2:50–3:35 — Capture evidence once
**Upload a synthetic handwritten log and download the original.**

“The sailor can capture a photo or attach an original log to the work order. The original is preserved, encrypted, and associated with that job.

The upload is working today. Handwriting extraction, calibrated confidence scoring, and populated Word or Excel output remain to implement. We label the file OCR pending so nobody mistakes file capture for verified transcription.”

## 3:35–4:15 — A useful watch handoff
**Enter a next-watch note and download the handoff.**

“The handoff includes the assignee, equipment location, source reference, recorded observations, blockers, next-watch action and evidence inventory. It's a reviewable draft—not aircraft release authority.

This is the practical outcome: less reconstruction at turnover, and a clearer record of what remains to be done.”

## 4:15–4:45 — When the connection returns
**Select simulated ship connectivity and sync; then simulated shore connectivity and sync. Repeat once.**

“Records are queued durably. Our simulator shows receipt aboard and receipt ashore. Repeating delivery does not duplicate the same event.

These are local receiver simulations. Authenticated remote synchronization, conflict reconciliation and a Navy ERP+ adapter are the next integration work, not something we are claiming to have connected today.”

## 4:45–5:00 — Close
**Return to My Watch.**

“Fleet Tech is designed around the watch: find the job, keep the evidence with it, capture once, and leave a useful handoff. Connectivity should determine when the record moves—not whether a sailor can record the work.”

## Thirty-second version
“Fleet Tech is a local-AI maintenance workspace for disconnected operations. It puts the job, source references, supply snapshot, class drawings, observations and handwritten originals together. Watch notes autosave, and the next watch can resume and download a handoff. We have working local storage and a duplicate-safe sync simulator. The next work is verified procedure structure, handwriting extraction and actual ship-to-shore integration. The goal is less searching and re-entry, with a clearer record at turnover.”

## Questions to anticipate
- **Does this replace the system of record?** No. The intended integration sends validated transactions to the authorized backend; no ERP connection is currently configured.
- **Does it work completely disconnected?** The app and model can run on the same host without shore service. A browser on another device still requires a route to that host. We have not delivered an independently offline mobile client.
- **Is the data encrypted?** Drafts, job/event payloads and uploaded originals are encrypted. Corpus indexes and some metadata are not; development keys are local files. Production device security remains work.
- **Does AI authorize maintenance?** No. It retrieves and summarizes evidence. The prototype's completion is an administrative record, not certification or release authority.
- **What improvement have you measured?** None claimed yet. Use Deckplate Impact to time equivalent tasks, review output quality, and record screen switches and user effort with sailors.
- **How is this scalable?** The class library and event model support extension. Real multi-device transport, fleet-scale tests and backend contracts still need to be proven.

## Experience-aware demonstration
Choose FC1 Ochoa, FC2 Donohue or FC3 Kluzak in the job assignment dropdown. These are user-defined demo profiles: Ochoa has performed each maintenance item more than ten times; Donohue three to four times; Kluzak is attempting maintenance for the first time. Show the profile panel, then ask the local assistant to explain the selected section. The model receives the saved assignee's profile and is instructed to adjust explanation depth. Required warnings and verification remain unchanged. These profiles are not verified completion histories or qualifications, and answer quality still requires validation with the running local model.

## Sister-ship learning
Show ship name, hull and named class in the workspace. Record a synthetic symptom, the actions taken and the observed outcome. Save a troubleshooting report, then search class history. Explain: “This preserves where the report came from and what was actually observed. A technician on another ship of the same class can use it as evidence to investigate—not as automatic authority to repeat a repair. Today the reports are local and queued; actual fleet distribution is the next integration.”

## Optional speed-to-fleet / security evidence segment

Open **06 Deckplate impact → View security scans & deployment evidence**.

“This is a deployment candidate with evidence, not an approval badge. We have a pinned container build, an SBOM, actual scan results and a network-disabled smoke test. The page shows the measured startup time, exact image ID and any open findings. We are giving an integration team a package they can inspect and repeat, instead of asking them to start packaging from scratch.

Iron Bank submission and target UDS validation remain gates. The full model package, identity controls and actual fleet synchronization must also be integrated. We will not equate a successful scan with an ATO or operational readiness.”

Use the current generated results, not numbers copied from an earlier run. See `security/READINESS.md` for reproduction commands and claim boundaries.
