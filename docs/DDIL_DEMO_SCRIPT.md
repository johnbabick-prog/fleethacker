# Fleet Tech — DDIL AI Demo Script

> Five minutes. One thesis: **AI that works when the network doesn't.**

---

## Pre-flight checklist

```bash
# 1. Delete old data so corrective jobs and cleaned lessons seed fresh
rm -f data/hatch.db

# 2. Seed troubleshooting reports (run once)
python3 scripts/seed_demo_troubleshooting.py

# 3. Start the app (auto-detects GPU model on port 18080)
./start.sh

# 4. Verify terminal shows: "HATCH model: EdgeRunner-Full-Combat" (GPU)
#    If it shows EdgeRunner-Medium, the GPU server isn't running.
```

- [ ] GPU model running (`llama-server --gpu-layers 99` on port 18080)
- [ ] Terminal shows `HATCH model: EdgeRunner-Full-Combat` (not Medium)
- [ ] App open at `127.0.0.1:8765`
- [ ] Connectivity set to **Device only**
- [ ] Have a terminal ready to kill the model (for degradation demo)
- [ ] Browser fullscreen, dev tools closed
- [ ] This script open on a second screen or printed

---

## CLICK PATH — Every step, every question

---

### 0:00–0:30 — The problem (My Watch)

**You're on My Watch. Connectivity is Device only.**

> "Every AI demo you've seen today assumes the network is there. Ours doesn't.
>
> An MH-60R detachment is operating without shore connectivity. The maintenance team has work orders, manuals, parts snapshots, and observations from the last watch — but the administrative workflow assumes a cloud connection that doesn't exist.
>
> Fleet Tech runs AI inference, evidence retrieval, and encrypted record-keeping on the sailor's device. No cloud. No CDN. No fallback to an API endpoint. The hatch is shut."

**Point to the connectivity selector: Device only. Point to the metrics — open work orders, local reference chunks.**

---

### 0:30–1:00 — Start from the job, not the chatbot

1. Click **Electrical** in the Work Center filter
2. Find **DEMO-11** (Electrical distribution panel voltage checks — due today)
3. Click **Follow procedure →**

**The job workspace opens. Note the greeting in the chat pane.**

4. Set **Assigned to** → **FC3 Kluzak**

> "We start from the job, not the chatbot. Kluzak is a first-time performer — watch the greeting change. The AI tells her it will explain in plain language and help with terminology."

5. Under CURRENT SHIP, set **Ship class** filter → **DDG**
6. In **Ship name**, type `Ben` → select **USS Benfold (DDG-65)**
7. In **Equipment / system**, select **Electrical distribution panel**

> "Ship identity is normalized from the fleet directory — 461 ships across 96 classes. Equipment is filtered to this hull type. The context is saved to the device."

**Wait for "Saved on host" confirmation.**

---

### 1:00–1:45 — WOW MOMENT 1: AI with traced evidence

**The procedure should auto-load (it's linked to DEMO-11). If not, open Browse manuals & procedures and select the electrical voltage check.**

8. In the **chat pane** on the right, copy-paste this question:

```
What are the correct voltage readings and acceptance bands for each test point in this procedure?
```

**As tokens stream, narrate:**

> "Watch what happens. The system searches the local FTS5 corpus — all on this device. It streams the answer from a model running on localhost with GPU acceleration."

**Point out as they appear:**
- The activity feed: *Retrieving → Contacting → Connected → Preparing final answer*
- The answer citing specific values: **24.0V DC (23.5–24.5V) on SIM-TP-01/02** and **12.0V DC (11.8–12.2V) on SIM-TP-03/04**
- The bracketed citation IDs

> "Every claim traces back to a specific source chunk. The AI cannot invent procedures or skip safety warnings."

---

### 1:45–2:15 — WOW MOMENT 2: Experience-aware adaptation

9. Change **Assigned to** from **FC3 Kluzak** → **FC1 Ochoa**

**Watch the chat greeting change — Ochoa gets "concise reminders" vs. Kluzak's "plain language."**

10. Click **Ask AI about this step** in the step coaching panel (right side, under the step heading)

> "Same step, same source reference — but the explanation depth changes. Kluzak gets plain-language detail. Ochoa gets concise reminders and relevant exceptions. Required warnings and verification stay identical for both."

**Point to the training history showing ">10 completed exercises."**

> "These are user-defined profiles, not rank-inferred qualifications. The model receives the profile as context. Experience adjusts guidance, not safety."

---

### 2:15–2:50 — WOW MOMENT 3: Kill the model

> "Now I'm going to break it."

11. **In your terminal**, kill the model:

```bash
pkill -f llama-server
```

12. In the chat pane, copy-paste:

```
What should I verify before changing the selector switch position?
```

**The activity feed shows: Contacting local model → Request failed.**

**Then a fallback answer appears with structured local records.**

> "The model is gone. In a cloud-dependent system, this is a blank screen. Fleet Tech falls back to structured local records — the step instruction, recorded lessons, and sailor-specific corrections. The mode label switches from 'Local AI' to 'Local records.'
>
> This is what DDIL means in practice. Not 'we hope the network works.' The system is designed to degrade, and it tells you when it has."

13. **Restart the model** (have the command ready):

```bash
# Restart llama-server with GPU acceleration
llama-server -m /path/to/model.gguf --gpu-layers 99 --port 18080 --alias EdgeRunner-Full-Combat &
```

---

### 2:50–3:25 — WOW MOMENT 4: Sister-ship learning

14. In the **Reports for this ship class** section, copy-paste into the search box:

```
voltage drop
```

15. Click **Search class history**

> "Another technician on the Benfold found an intermittent voltage drop on this exact equipment. The report shows what they observed, what they tried, and what happened — with the originating ship and technician attributed."

**Point to the report showing FC1 Ochoa's voltage fluctuation finding on DDG-65.**

> "This isn't AI-generated advice. It's evidence from a specific sailor on a specific hull. A technician on another destroyer of the same class can use it to investigate — not as automatic authority to repeat a repair."

16. Now search for:

```
temperature alarm filter
```

**The SONAR cabinet cooling report appears — heavy debris caused overheating.**

> "Different equipment, different ship, same class. The data model supports fleet learning from attributed observations. Today these reports are local and queued. Fleet distribution is the next integration."

---

### 3:25–3:55 — WOW MOMENT 5: The record travels

17. Check **steps 1, 2, and 3** in the procedure checklist

**The progress bar fills. Point to it.**

> "The sailor reviews source text and checks steps. This is revision-bound — if the source document changes, the checkmarks clear."

18. Click **Clear all checks** → then re-check **steps 1 and 2** → Click **Save progress**

> "The demo resets cleanly. In a real session, this preserves exactly where the sailor stopped."

19. Click **Capture work-order completion →**
20. In **What was done**, enter: `Voltage verified within acceptance band on all test points. Contact B2 cleaned per class history report from DDG-65.`
21. *(Optional)* Expand **Add a meter reading** and enter: `24.1`
22. Click **Save & queue for sync →**

**Watch the pending event count increase in the notice.**

23. Press **5** (keyboard shortcut) to go to Fleet synchronization
24. Set connectivity to **Ship network**
25. Click **Sync to ship**

> "Records queue durably on the device. When the ship network appears, they deliver."

26. Set connectivity to **Shore restored**
27. Click **Sync to shore**

> "When shore connectivity returns, they deliver again."

28. Click **Sync to shore** again

> "Zero new acknowledgments. Idempotent delivery — no duplicates, no lost records. The sailor entered the work once. The device kept the evidence. Connectivity determines when records travel — not whether work can be recorded."

---

### 3:55–4:30 — WOW MOMENT 6: Measured impact

29. Press **6** to go to Deckplate impact

> "We don't claim time savings. We measure them."

30. Set method to **Manual baseline** → Click **Start timed trial** → wait ~12 seconds → Click **Stop trial**
31. Set quality to **Passed review** → Click **Save trial result**
32. Set method to **HATCH-assisted** → Click **Start timed trial** → wait ~6 seconds → Click **Stop trial**
33. Set quality to **Passed review** → Click **Save trial result**

**The comparison appears with elapsed-time difference.**

> "Same scenario, same accuracy requirement, same reviewer. Small demo samples don't establish fleet-wide savings — but the measurement framework is built in. Judges can run their own trials and export the data."

---

### 4:30–5:00 — Close

34. Press **1** to return to My Watch

> "Fleet Tech is AI that works in DDIL. Not because we bolt a chatbot onto a disconnected form — but because every layer is designed for it.
>
> Local inference on loopback with GPU acceleration — with graceful degradation to structured evidence when the model goes down. Encrypted storage with device-locked keys. Experience-aware coaching that adapts depth without changing safety. Traced citations, not generated text passed off as fact. Durable records that travel when connectivity allows.
>
> The sailor records the work once. The AI helps with what it can prove. The record survives the network."

---

## ALTERNATE PATH: Corrective maintenance — something is broken

> Use this instead of (or after) the preventive path. This is the "sailor calls it in" demo.

### Setup

The app seeds three corrective maintenance jobs (CM-1, CM-2, CM-3) marked **Urgent** with a pulsing red dot. They appear at the top of the watch.

---

### The corrective demo (2–3 minutes standalone)

1. On **My Watch**, point to the **CM-1** card: "Diagnose lighting zone failure"

> "This isn't a scheduled check. Someone reported a problem — lighting zone 2 went dark at 0215. The sailor needs to figure out what happened."

**Point to the red pulsing dot and CORRECTIVE / Urgent label.**

2. Click **Diagnose problem →** on CM-1

3. The **problem report panel** appears with a red border. Type in the symptom box:

```
Forward lighting zone 2 went completely dark during mid-watch. No other zones affected. Was working at 0200 rounds.
```

4. *(Optional)* Click **Upload a photo** and attach any image to show the photo capture flow

5. Click **Ask AI to help diagnose →**

> "The sailor describes what they see. The AI searches local references AND class troubleshooting history. Watch — it finds a report from another destroyer where FC1 Ochoa saw a similar voltage issue on the same equipment."

**As the answer streams, point to:**
- The class troubleshooting report being cited
- The specific fault-isolation steps suggested
- The traced source citations

6. Set ship to **USS Halsey (DDG-97)** and equipment to **Electrical distribution panel**

7. Follow the corrective procedure steps — these guide fault isolation, not a checklist:
   - Step 3: "Locate panel, check breaker — it reads TRIPPED"
   - Step 5: "Junction box shows arcing on neutral terminal"

8. In the chat, ask:

```
The breaker was tripped and I found arcing damage on connector SIM-FC-207. What should I do next and what should I tell the next watch?
```

> "The AI uses the fault-isolation steps, the sailor's own findings, and the class history to help build the response. But it doesn't authorize the repair — it helps document what was found."

9. Open **Record troubleshooting findings** and fill in:
   - Observed problem: `Lighting zone 2 dark, breaker SIM-CB-LZ2 tripped`
   - Actions taken: `Reset breaker, zone restored. Found arcing damage at SIM-FC-207 neutral terminal.`
   - Outcome: `Zone operational, monitoring for retrip. Connector requires replacement next maintenance period.`

10. Click **Save troubleshooting record**

> "This report is now available to every ship of this class. The next sailor who searches 'lighting zone dark' or 'breaker tripped' will find exactly what happened here, on this hull, with this technician's name on it."

11. Complete the job:
    - Click **Capture work-order completion →**
    - What was done: `Breaker SIM-CB-LZ2 reset, zone 2 forward restored. Arcing damage at connector SIM-FC-207 requires replacement. Monitoring every 30 min.`
    - Click **Save & queue for sync →**

---

### Corrective maintenance copy-paste questions

```
Forward lighting zone 2 went completely dark during mid-watch. No other zones affected. Was working at 0200 rounds.
```

```
The breaker was tripped and I found arcing damage on connector SIM-FC-207. What should I do next and what should I tell the next watch?
```

```
I'm seeing a drip at the base of valve SIM-V-104, about one drip every 3 seconds. System pressure looks normal. What should I check?
```

```
SONAR console is showing fault code E101 on channel 2. Channels 1 and 3 are working. What's the isolation procedure?
```

```
Have any other ships in this class had problems with this connector or this lighting zone?
```

---

## Copy-paste question bank

Keep these ready in case judges ask to see more, or if you need to repeat a moment:

### Evidence retrieval

```
What are the correct voltage readings and acceptance bands for each test point in this procedure?
```

```
What safety precautions should I take before opening the strainer for inspection?
```

```
What is the pass/fail criteria for the emergency lighting battery discharge test?
```

### Experience-aware (assign Kluzak first, then switch to Ochoa)

```
Explain what I need to do in this step and why it matters.
```

```
What mistakes have been recorded on this step?
```

### Degradation test (after killing the model)

```
What should I verify before changing the selector switch position?
```

```
Are there any recorded lessons about this step I should review?
```

### Equipment-specific

```
What is the current parts availability for this equipment and what does the inventory snapshot tell me?
```

```
Have other ships in this class reported problems with this equipment?
```

### Cross-reference (with PDFs uploaded)

```
Find the wiring diagram for the 24V distribution panel.
```

---

## Wow moment summary

| # | Moment | What judges see | The line that lands |
|---|---|---|---|
| 1 | Traced evidence | Citations stream with expandable sources, specific voltage values | "Every claim traces back to a source chunk" |
| 2 | Experience switch | Same step, different depth for Kluzak vs Ochoa | "Experience adjusts guidance, not safety" |
| 3 | **Kill the model** | Fallback to records, mode label changes | **"The system is designed to degrade, and it tells you when it has"** |
| 4 | **Corrective: "something's broken"** | Sailor describes problem, AI searches class history + references | "Describe what you see — the AI finds who's seen it before" |
| 5 | Sister-ship reports | Troubleshooting data from another hull appears by class | "Evidence from a specific sailor on a specific hull" |
| 6 | Idempotent sync | Second delivery = zero new acks | "Connectivity determines when records travel" |
| 7 | Live measurement | Timed trials with comparison | "We don't claim time savings. We measure them." |

---

## Backup: 30-second version

"Fleet Tech runs AI inference, evidence retrieval, and encrypted record-keeping on a sailor's device with no cloud dependency. Kill the model — it degrades to structured local records and tells you. Bring connectivity back — queued records deliver idempotently. The AI adapts coaching depth to experience level but never changes safety warnings. Every answer traces to a source citation. We measure time savings instead of claiming them. This is AI designed for DDIL, not adapted to it."

---

## Questions to own

| Question | Answer |
|---|---|
| "What if the model hallucinates?" | Every answer includes citation IDs. Response filtering strips internal reasoning. If it can't produce a valid answer, it falls back to structured records and labels the mode change. |
| "Does this replace the system of record?" | No. Administrative records, not release-to-flight. No ERP connection exists today. |
| "What model are you running?" | EdgeRunner-Full-Combat on llama.cpp with Metal GPU acceleration. The app discovers any OpenAI-compatible server on loopback. Works with llama.cpp, Garrison, or any compatible local server. |
| "How is this different from local ChatGPT?" | Six ways: (1) page-cited evidence retrieval, not just generation; (2) experience-aware coaching; (3) explicit degradation to structured records; (4) can't invent procedures or skip warnings; (5) revision-bound records with idempotent sync; (6) AI is one layer in a maintenance workflow, not a standalone chat. |
| "What improvement have you measured?" | None claimed. The measurement framework is built in — run a trial and export the data. |
| "Why not just use the cloud when you have it?" | Fleet Tech works with or without. But the design point is zero connectivity. If you design for the worst case, the connected case is trivial. Cloud AI can layer on top — it doesn't replace the local capability. |
| "How do you handle model updates?" | Swap the GGUF file and restart. The app discovers whatever model is running on loopback. No retraining, no fine-tuning — it's retrieval-augmented generation over local evidence. |
