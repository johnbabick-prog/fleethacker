# The record should never have to wait for the network

## Opening — 30 seconds
An MH-60R detachment is operating without shore connectivity. The maintenance team still has work to do. The manuals are aboard. The parts snapshot is aboard. The sailor is aboard. But the administrative workflow assumes the network is available.

HATCH puts the assistant, evidence, and transaction record on the sailor's device. It works with the hatch shut.

## Demonstration — four minutes
1. **Start disconnected.** Select Device only. Show the local reference count, open work orders, supply snapshot timestamp and pending transactions. Explain that jobs, quantities and identifiers are synthetic; the local reference corpus is supplied separately.
2. **Find the evidence.** Open Local assistant. Ask: “Find references for land hover lights and show my open work orders.” Expand the source identifiers. If no model is running, call this a retrieval demonstration, not AI inference. Do not use the assistant to invent troubleshooting or authorize aircraft release.
3. **Capture once.** Capture completion on WO-001 with a fictional meter reading and administrative note. Attach a synthetic evidence photo if available. Point to the durable pending event. Reload the page to demonstrate persistence.
4. **Verify uncertainty.** Open Document review. Explain that the fixture represents a future OCR output, with an illustrative 62% reading requiring human review. Correct it, acknowledge review, and export JSON. Be explicit: scanned intake and Word/Excel output are planned, not implemented.
5. **Carry the record home.** Select simulated ship connectivity and sync. Then select shore restored and sync. Repeat: zero new acknowledgments demonstrates retry safety. These receivers are local simulations, not a real ERP integration.

## Closing — 20 seconds
The sailor should enter the work once. The device keeps the evidence. The ship gains visibility when the local network is available. The fleet gains visibility when the shore link returns. Connectivity changes when records travel—not whether work can be recorded.

## Judging story
| Criterion | Demonstrable value | Evidence still needed |
|---|---|---|
| Warfighting · 30% | Administrative capture and evidence retrieval with no shore dependency | Timed baseline vs prototype; no readiness improvement asserted without measurement |
| Speed to Fleet · 20% | Runs on a COTS computer with local inference | Device support, model latency, deployment authorization and user testing |
| Scalability · 20% | Source-linked corpus and durable event model | Multi-device conflict handling, remote receivers, load tests and ERP+ interface |
| Barrier Removal · 15% | One view for work orders, inventory evidence and record capture | Actual SKED/OMMS/R-Supply mappings and importer validation |
| Discretion · 15% | Explicit future integration boundary; no new system-of-record claim | Navy wholesale/retail supply and finance interface agreements |

## Measurement card
Record hardware, model ID, corpus size, time to find the relevant reference, time to save a job, inference latency, and duplicate receipts after retries. For OCR, measure token accuracy and confidence calibration on held-out labeled handwriting before claiming the 70% threshold has statistical meaning.

## Demonstration discipline
Use a synthetic corpus for an unrestricted audience. Keep the source-reference deployment local and approved. Never describe synthetic inventory as real availability, simulated receipts as ERP acceptance, or administrative completion as flight authorization.

## New follow-along sequence
Before capturing completion, open **Maintenance procedure** from a work-order card. Find a source module, review its source text, mark a reading section, and save progress. Add a clearly identified demonstration observation to show how experience stays with the module. Use **Brief me with local AI** to summarize existing reports when a model is available. Then upload a synthetic handwritten PDF/photo and download the preserved original. Finish with work-order completion and synchronization. Explain that section acknowledgments track reading, not certified maintenance execution, and that handwriting extraction remains pending.

## Warfighting and deckplate impact — 30%
Lead with the Sailor's burden: finding the right source, remembering observations, re-entering the same facts and handing over incomplete context. Demonstrate one job from source retrieval through saved observations, attached original log and a downloaded watch-handoff draft. The handoff reuses saved records rather than asking the Sailor to type the story again. It is a reviewable draft, not maintenance certification or a CASREP update.

Open Deckplate impact and time equivalent manual and HATCH-assisted administrative trials. Require a qualified reviewer to verify the same output quality before marking a trial passed. Compare median elapsed time using only passing trials; retain failures and pending reviews in the export. Use multiple participants and counterbalance which method they try first to reduce practice effects. Keep the scenario, data access, expected facts and completion criteria fixed.

Report observed task-time differences with sample size, errors, search attempts, screen switches and a 1–5 effort rating. Do not turn elapsed-time differences into labor-hours without accounting for the number of people involved and measured task frequency. Do not claim readiness or casualty-resolution improvements from an administrative demo.

Suggested closing: “HATCH keeps the source, observations and evidence with the job. The next watch starts from the recorded work instead of reconstructing it. We measure the time and effort that this returns to the deckplate.”
