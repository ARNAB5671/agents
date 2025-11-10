    # 🧠 SalesCode.ai Final Round Qualifier  
    ## LiveKit Voice Interruption Handling Challenge  
    ### Author: Arnab Das  
    Branch: `feature/livekit-interrupt-handler-arnab`

    ---

    ## 🔍 Overview

    This project implements an **Interrupt Handler Module** that enhances **LiveKit Agents** to intelligently distinguish **filler sounds** (like “uh”, “umm”, “hmm”, “haan”, “acha”) from **real user interruptions** (like “wait”, “stop”, “no not that one”) during live voice interaction.

    In traditional Voice Activity Detection (VAD), these short fillers often trigger **false pauses** — breaking the natural flow of speech.  
    This implementation ensures that:
    - The agent **continues speaking naturally** when users say small fillers like _“uh”, “umm”, “hmm”, “haan”_.
    - It **instantly stops** when real interruption phrases like _“wait”_, _“stop”_, _“hold on”_, or _“no not that one”_ are detected.
    - The logic runs in **real time** and does **not modify** LiveKit’s base SDK or VAD algorithm.

    > **NOTE:** Check `ultimate_salescode_test.py` for details on edge-case assumptions like “ok” —  
    > since its meaning depends on user vocal tone (e.g., stretched “ok” vs. flat “ok”).  
    > The current logic treats standalone “ok” as acknowledgment (ignored),  
    > but “ok stop” or “ok continue” as actionable interruptions.


    

    ## 🎯 Objective

    - ✅ Ignore specific filler sounds while the agent is speaking.
    - ✅ Detect real user interruptions (like “wait” or “stop”) with instant responsiveness.
    - ✅ Forward user speech normally when the agent is not speaking.
    - ✅ Support multilingual (English + Hindi) filler and command recognition.
    - ✅ Allow runtime configuration of filler words without restarting.
    - ✅ Keep the design non-invasive and compatible with LiveKit Agents.

    ---

    ## 🧩 Example Scenarios

    | Scenario | Input | Agent Speaking | Expected Behavior |
    |-----------|--------|----------------|-------------------|
    | Filler words | “uh”, “umm”, “hmm”, “haan” | ✅ Yes | Ignored |
    | Real command | “wait one second”, “stop” | ✅ Yes | Interrupt |
    | Filler while quiet | “umm” | ❌ No | Forwarded |
    | Mixed filler + command | “umm okay stop” | ✅ Yes | Interrupt |
    | Multilingual | “acha hmm okay”, “nahi ruk jao” | ✅ Yes | Works |
    | Low-confidence noise | “hmm yeah” (conf=0.3) | ✅ Yes | Ignored |

    ---

    ## ⚙️ Technical Implementation

    ### 📁 New Module
    `agents/extensions/interrupt_handler/interrupt_handler.py`

    ### 🧠 Core Classes

    #### 1️⃣ `Decision` (Enum)
    Defines the decision outcomes:
    - `IGNORED`: Filler / non-actionable
    - `INTERRUPT`: Real command or user intent
    - `FORWARDED`: Passed through when agent not speaking

    #### 2️⃣ `AgentState`
    Tracks whether the agent is currently speaking (`True` / `False`) using an asynchronous lock to avoid race conditions.

    #### 3️⃣ `InterruptHandler`
    Main logic class that:
    - Normalizes multilingual text (`normalize_text`)
    - Tokenizes and filters speech
    - Handles real-time ASR transcripts with confidence thresholds
    - Logs structured events for debugging and analysis

    ---

    ## 🧠 Key Algorithm Logic

    ### ✅ Normalization
    Handles filler variations:
    ```python
    replacements = {
        r"ach+?a+": "acha",
        r"ha+?n+": "haan",
        r"arre+": "arre",
        r"umm+": "umm",
        r"uh+": "uh",
        r"hmm+": "hmm",
        r"ok+?ay*": "ok",
        r"th(e)?ek\s*hai": "theek hai",
    }
    ✅ Configurable Parameters
    ignored_words = ["uh", "um", "umm", "hmm", "haan", "acha", "em", "arre", "chalo", "theek", "theek hai"]
    stop_words = ["stop", "wait", "hold on", "pause", "no not that one"]
    confidence_threshold = 0.5
    low_confidence_threshold = 0.35

    ✅ Runtime Update Support
    handler.update_ignored_words(["uh", "umm", "haan", "acha", "arre", "matlab"])

    ✅ Smart Filtering Flow

    Low-confidence background speech → Ignored

    Pure filler tokens → Ignored

    Stop or command words present → Immediate interrupt

    Soft acknowledgments like “ok”, “haan” → Ignored

    Agent not speaking → All inputs forwarded normally

    🧩 Logging Categories

    Each decision is logged with clear, structured tags:

    [IGNORED_FILLER_OR_DISCOURSE]

    [IGNORED_LOW_CONF]

    [IGNORED_ACK]

    [INTERRUPT_STOP_WORD]

    [INTERRUPT_MEANINGFUL]

    [FORWARDED]

    Example:

    [INTERRUPT_STOP_WORD] text='umm okay stop' conf=0.95 extra={'matched': 'stop'}
    [IGNORED_FILLER_OR_DISCOURSE] text='uh hmm okay' conf=0.85 extra={}

    🧪 Testing & Validation
    🧰 Test Scripts
    Script	Purpose
    ultimate_salescode_test.py	74 comprehensive test cases (filler, commands, confidence, multilingual)
    multilingual_test.py	Hindi + English test coverage
    test_interrupt_demo.py	INITIAL behavior demo
    🧾 Example Output
    ============================================================
    TOTAL: 74/74 passed (100.0%) in  ultimate_salescode_test.py
    ============================================================
    🎯 All possible scenarios handled perfectly!


    Highlights:

    Ignores fillers (uh, umm, hmm, haan) while speaking

    Detects commands instantly (stop, wait, hold on)

    Works perfectly on multilingual inputs (acha hmm okay, nahi ruk jao)

    Low-confidence speech (<0.35) safely ignored as background

    🧠 Design Decisions
    “OK” / “Okay”

    Alone: Treated as acknowledgment → IGNORED

    With command: (“okay stop”) → INTERRUPT

    “uh hmm okay” / “acha hmm okay”

    Classified as acknowledgment → IGNORED by design

    Prevents awkward, false interruptions during polite confirmations.

    Partial Fragments

    wa, st, wai ignored unless confidence > 0.7
    Prevents early ASR token interruptions.

    Multilingual Fillers

    “acha”, “haan”, “arre”, “matlab”, “theek hai” normalized for bilingual users.

    ⚙️ Technical Flow
    # 1️⃣ Set agent state
    await handler.agent_state.set_speaking(True)

    # 2️⃣ Pass transcript from ASR
    decision = await handler.handle_transcript(text, confidence)

    # 3️⃣ Take action
    if decision == Decision.INTERRUPT:
        agent.pause_tts()
    elif decision == Decision.IGNORED:
        pass
    elif decision == Decision.FORWARDED:
        forward_to_agent(text)

    # 4️⃣ Reset state
    await handler.agent_state.set_speaking(False)

    🧩 How to Test

    Run
    python3 ultimate_salescode_test.py




    Expected output:

    TOTAL: 74/74 passed (100.0%)
    🎯 All possible scenarios handled perfectly!

    🧰 Environment Details
    Parameter	Value
    Python Version	3.12 (≥3.10 compatible)
    Platform	macOS 14 (Sonoma)
    Dependencies	Standard library only (asyncio, re, time, enum, typing)
    Integration	Non-invasive — no changes to LiveKit SDK or VAD
    Hardware	Apple M1 MacBook Air
    🧾 Known Issues

    Edge case: "uh hmm okay" → ignored intentionally for realism.

    Confidence thresholds may need tuning for certain ASR models.

    Filler lists can be expanded per language (future enhancement).

    Occasional false positives possible due to ASR transcription noise.

    🧩 Commit Summary
    Commit	Message
    bf20a14	chore(interrupt): add placeholder for interrupt handler
    ca2ebc4	fix(interrupt): handle fuzzy fillers and short tokens
    242ec81	fix(interrupt): improve filler + partial token logic
    latest	feat(interrupt): final multilingual, runtime dynamic handler

    🧪 Test Results Summary
    Category	Example	Result
    Filler suppression	uh, umm, hmm, haan	✅ Ignored
    Real interruption	stop, wait, hold on	✅ Interrupt
    Mixed filler + command	umm okay stop	✅ Interrupt
    Low-confidence noise	background chatter, traffic noise	✅ Ignored
    Multilingual	acha hmm okay, nahi ruk jao, theek hai	✅ Correct
    Acknowledgments	ok, haan, acha	✅ Ignored
    Edge cases	uh hmm okay, wa, st	✅ Handled
    Accuracy	—	🎯 100.0% Passed (74/74)
\