# LiveKit Interrupt Handler — Arnab Das

### Branch: `feature/livekit-interrupt-handler-arnab`

This branch adds an **extension module** for LiveKit Agents that intelligently filters out filler sounds like  
`uh`, `umm`, `hmm`, `haan`, and `acha` — so the agent does **not** pause unnecessarily during speech.  
At the same time, it still **instantly reacts** to real interruptions like `stop`, `wait`, or `no not that one`.

No modifications were made to the LiveKit core or its VAD (Voice Activity Detection).  
All logic exists as an **extension layer**, ensuring clean integration and scalability.

---

## 🧩 What Changed

**New module:**
- `agents/extensions/interrupt_handler/interrupt_handler.py`

### Key Components

- **`InterruptHandler`**
  - Decides between `IGNORED`, `INTERRUPT`, and `FORWARDED` decisions in real time.
  - Handles fuzzy filler detection, discourse filtering, and partial-token heuristics.
- **`AgentState`**
  - Tracks whether the agent is currently speaking.
  - Used asynchronously to prevent race conditions.
- **Runtime Configuration**
  - `ignored_words` — default: `["uh", "um", "umm", "hmm", "haan", "acha", "em"]`
  - `stop_words` — default: `["stop", "wait", "hold on", "pause", "no not that one"]`
  - `confidence_threshold` and `low_confidence_threshold` for noise filtering.
- **Runtime Update**
  - Dynamically update filler words via:
    ```python
    handler.update_ignored_words(["uh", "umm", "haan", "acha", "arre", "matlab"])
    ```
- **Structured Logging**
  - For debug visibility:
    - `IGNORED_FILLER_OR_DISCOURSE`
    - `INTERRUPT_STOP_WORD`
    - `INTERRUPT_MEANINGFUL`
    - `IGNORED_LOW_CONF`
    - `IGNORED_ACK`
    - `FORWARDED`

---

## ✅ What Works (Verified)

- Ignores **fillers only** when the agent is speaking.
- Instantly interrupts on **real user commands** like:
  - `"stop"`, `"wait"`, `"hold on"`, `"no not that one"`
- **Filler + Command** combo works correctly:
  - `"umm okay stop"` → Interrupts  
  - `"acha hmm wait a sec"` → Interrupts  
  - `"uh hmm okay"` → Ignored (soft acknowledgment)
- When the agent is **not speaking**, all fillers are **forwarded** normally.
- Handles low-confidence ASR input as noise (`confidence < 0.35`).
- Supports multilingual fillers (Hindi + English mix).
- Dynamic filler updates in real time (`runtime_update_test.py`).
- Tested thoroughly across 74 cases with `ultimate_salescode_test.py` achieving **97%+ accuracy**.

---

## 🧠 Design Decisions

### “OK” / “Okay”
- Treated as **soft acknowledgment** (ignored) when spoken alone.
- Triggers interrupt only when combined with a command (e.g., `okay stop`).
- Prevents the agent from pausing unnecessarily on polite confirmations.

### “uh hmm okay” and “acha hmm okay”
- Currently treated as **IGNORED** — considered acknowledgment, not command.
- Earlier versions treated them as interrupts; this conservative version was chosen for smoother flow.

### Partial Fragments
- Fragments like `wa`, `st`, `wai` are ignored unless confidence rises > 0.7.

### Fuzzy Matching
- Handles variable-length fillers (`umm`, `ummm`, `uhhh`) via regex-based matching.

---

## ⚙️ Technical Flow

1. Agent sets speaking state:
   ```python
   await handler.agent_state.set_speaking(True)

