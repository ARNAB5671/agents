import asyncio, random, time
from agents.extensions.interrupt_handler.interrupt_handler import InterruptHandler, Decision

# === Full Coverage Test Matrix for SalesCode.ai Challenge ===
# Covers: fillers, real commands, partials, confidence drift, multi-language, low conf, repetition, silence, noise.

TEST_CASES = [
    # ==== 1️⃣ Pure Filler - High Confidence ====
    ("uh", 0.95, True, Decision.IGNORED),
    ("umm", 0.93, True, Decision.IGNORED),
    ("hmm", 0.9, True, Decision.IGNORED),
    ("haan", 0.94, True, Decision.IGNORED),
    ("acha", 0.92, True, Decision.IGNORED),
    ("ummm", 0.97, True, Decision.IGNORED),
    ("uhhh", 0.99, True, Decision.IGNORED),
    ("em", 0.85, True, Decision.IGNORED),  # non-English filler

    # ==== 2️⃣ Filler + Command ====
    ("uh okay stop", 0.92, True, Decision.INTERRUPT),
    ("umm yeah wait", 0.96, True, Decision.INTERRUPT),
    ("haan okay stop", 0.94, True, Decision.INTERRUPT),
    ("acha hmm wait a sec", 0.95, True, Decision.INTERRUPT),
    ("ummm okay fine stop", 0.96, True, Decision.INTERRUPT),

    # ==== 3️⃣ Clear Interruptions ====
    ("stop", 0.98, True, Decision.INTERRUPT),
    ("wait", 0.9, True, Decision.INTERRUPT),
    ("no not that one", 0.91, True, Decision.INTERRUPT),
    ("hold on", 0.92, True, Decision.INTERRUPT),
    ("can you stop", 0.93, True, Decision.INTERRUPT),
    ("pause", 0.94, True, Decision.INTERRUPT),
    ("listen", 0.9, True, Decision.INTERRUPT),

    # ==== 4️⃣ Low Confidence Noise ====
    ("uh", 0.1, True, Decision.IGNORED),
    ("hmm yeah", 0.3, True, Decision.IGNORED),
    ("background chatter", 0.2, True, Decision.IGNORED),
    ("music", 0.25, True, Decision.IGNORED),
    ("random words", 0.35, True, Decision.IGNORED),
    ("traffic noise", 0.32, True, Decision.IGNORED),

    # ==== 5️⃣ Multi-language Mix ====
    ("haan stop please", 0.9, True, Decision.INTERRUPT),
    ("acha hmm okay", 0.9, True, Decision.IGNORED),
    ("theek hai", 0.88, True, Decision.INTERRUPT),
    ("nahi ruk jao", 0.9, True, Decision.INTERRUPT),
    ("uh haan continue", 0.9, True, Decision.INTERRUPT),
    ("umm theek hai stop", 0.92, True, Decision.INTERRUPT),

    # ==== 6️⃣ Quiet Agent (Everything Forwarded) ====
    ("umm", 0.8, False, Decision.FORWARDED),
    ("haan", 0.85, False, Decision.FORWARDED),
    ("okay stop", 0.9, False, Decision.FORWARDED),
    ("no not that one", 0.9, False, Decision.FORWARDED),
    ("background chatter", 0.25, False, Decision.FORWARDED),
    ("hmm", 0.4, False, Decision.FORWARDED),

    # ==== 7️⃣ Partial / Streaming Fragments ====
    ("u", 0.95, True, Decision.IGNORED),  # partial of uh
    ("um", 0.9, True, Decision.IGNORED),  # partial
    ("wa", 0.4, True, Decision.IGNORED),  # start of wait
    ("wai", 0.6, True, Decision.IGNORED), # intermediate
    ("wait", 0.9, True, Decision.INTERRUPT),
    ("st", 0.45, True, Decision.IGNORED), # partial stop
    ("stop", 0.95, True, Decision.INTERRUPT),

    # ==== 8️⃣ Long Sentences ====
    ("uh so basically what I mean is stop there", 0.9, True, Decision.INTERRUPT),
    ("umm yeah I think we can continue", 0.88, True, Decision.INTERRUPT),
    ("haan actually no not that one", 0.9, True, Decision.INTERRUPT),
    ("acha okay go ahead", 0.9, True, Decision.INTERRUPT),
    ("uh so anyway hmm yeah", 0.8, True, Decision.IGNORED),

    # ==== 9️⃣ Empty and Blank ====
    ("", 0.0, True, Decision.IGNORED),
    (" ", 0.1, True, Decision.IGNORED),
    (None, 0.0, True, Decision.IGNORED),

    # ==== 🔟 Rapid Turn Taking (Agent and User alternate) ====
    ("umm stop", 0.96, True, Decision.INTERRUPT),
    ("umm", 0.9, False, Decision.FORWARDED),
    ("wait one second", 0.95, True, Decision.INTERRUPT),
    ("okay go", 0.9, False, Decision.FORWARDED),
    ("uh hmm okay", 0.85, True, Decision.IGNORED),
    ("no stop", 0.95, True, Decision.INTERRUPT),
    ("umm okay continue", 0.9, True, Decision.INTERRUPT),

    # ==== 11️⃣ Repetitions (User frustration) ====
    ("stop stop stop stop", 0.99, True, Decision.INTERRUPT),
    ("wait wait wait", 0.98, True, Decision.INTERRUPT),
    ("umm stop haan stop", 0.97, True, Decision.INTERRUPT),

    # ==== 12️⃣ Confidence Drift Mid Speech ====
    ("uh okay st", 0.4, True, Decision.IGNORED),
    ("uh okay stop", 0.8, True, Decision.INTERRUPT),
    ("hmm haan w", 0.3, True, Decision.IGNORED),
    ("hmm haan wait", 0.85, True, Decision.INTERRUPT),

    # ==== 13️⃣ ASR false positive words ====
    ("two people talking", 0.3, True, Decision.IGNORED),
    ("background noise music", 0.2, True, Decision.IGNORED),
    ("air conditioner", 0.25, True, Decision.IGNORED),

    # ==== 14️⃣ Edge Case - Very short valid command ====
    ("go", 0.9, True, Decision.INTERRUPT),
    ("no", 0.9, True, Decision.INTERRUPT),
    ("ok", 0.9, True, Decision.IGNORED),  # FIXED: ok alone is acknowledgment, not interrupt
    ("yo", 0.8, True, Decision.INTERRUPT),
]

async def run_tests():
    handler = InterruptHandler()
    passed = 0
    random.shuffle(TEST_CASES)
    start_time = time.time()

    for i, (text, conf, speaking, expect) in enumerate(TEST_CASES, 1):
        await handler.agent_state.set_speaking(speaking)
        try:
            decision = await handler.handle_transcript(text or "", conf)
        except Exception as e:
            print(f"{i:02d}. ERROR for text='{text}': {e}")
            continue

        status = "✅ PASS" if decision == expect else f"❌ FAIL (expected {expect}, got {decision})"
        print(f"{i:02d}. speaking={speaking:<5} conf={conf:.2f} text='{text}' -> {decision.name:<10} | {status}")
        if decision == expect:
            passed += 1

    total = len(TEST_CASES)
    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print(f"TOTAL: {passed}/{total} passed ({(passed/total)*100:.1f}%) in {elapsed:.2f}s")
    print("="*60)
    if passed == total:
        print("🎯 All possible scenarios handled perfectly!")
    else:
        print("⚠️ Some edge cases need review.")

if __name__ == "__main__":
    asyncio.run(run_tests())
