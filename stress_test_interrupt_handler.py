import asyncio, random, time
from agents.extensions.interrupt_handler.interrupt_handler import InterruptHandler, Decision

# Big set of realistic and edge scenarios
TEST_CASES = [
    # === 1. Basic fillers during speaking ===
    ("uh", 0.93, True, Decision.IGNORED),
    ("umm", 0.88, True, Decision.IGNORED),
    ("hmm haan", 0.92, True, Decision.IGNORED),
    ("hmm", 0.4, True, Decision.IGNORED),
    ("ummm", 0.99, True, Decision.IGNORED),

    # === 2. Filler + command ===
    ("umm okay stop", 0.95, True, Decision.INTERRUPT),
    ("uh wait a sec", 0.9, True, Decision.INTERRUPT),
    ("umm hmm no not that one", 0.96, True, Decision.INTERRUPT),
    ("haan stop please", 0.94, True, Decision.INTERRUPT),

    # === 3. Real interruptions (clear) ===
    ("stop stop stop", 0.98, True, Decision.INTERRUPT),
    ("wait one second", 0.93, True, Decision.INTERRUPT),
    ("no no go back", 0.91, True, Decision.INTERRUPT),

    # === 4. Background murmurs (low confidence noise) ===
    ("hmm yeah okay", 0.25, True, Decision.IGNORED),
    ("uhh hmm maybe", 0.2, True, Decision.IGNORED),
    ("hmm hmm hmm", 0.15, True, Decision.IGNORED),

    # === 5. Mixed language fillers (Hinglish) ===
    ("acha hmm okay", 0.9, True, Decision.INTERRUPT),
    ("haan theek hai", 0.93, True, Decision.INTERRUPT),
    ("hmm nahi", 0.92, True, Decision.INTERRUPT),

    # === 6. Quiet agent (everything forwarded) ===
    ("umm", 0.8, False, Decision.FORWARDED),
    ("haan", 0.75, False, Decision.FORWARDED),
    ("okay got it", 0.9, False, Decision.FORWARDED),
    ("stop", 0.7, False, Decision.FORWARDED),
    ("hmm", 0.3, False, Decision.FORWARDED),

    # === 7. Partial streaming transcripts ===
    ("u", 0.95, True, Decision.IGNORED),   # partial filler
    ("uh", 0.95, True, Decision.IGNORED),  # partial still filler
    ("umm okay", 0.96, True, Decision.INTERRUPT),  # filler + meaning
    ("wa", 0.4, True, Decision.IGNORED),   # incomplete "wait"
    ("wait", 0.9, True, Decision.INTERRUPT),   # completed "wait"

    # === 8. Long natural speech ===
    ("uh so basically what I was saying is that maybe we can stop there", 0.95, True, Decision.INTERRUPT),
    ("umm i think that’s fine", 0.9, True, Decision.INTERRUPT),
    ("uhh menu please", 0.94, True, Decision.INTERRUPT),
    ("hmm okay continue", 0.85, True, Decision.INTERRUPT),

    # === 9. Empty / garbage input ===
    ("", 0.0, True, Decision.IGNORED),
    ("    ", 0.1, True, Decision.IGNORED),
    (None, 0.0, True, Decision.IGNORED),

    # === 10. Random background chatter ===
    ("two people talking", 0.35, True, Decision.IGNORED),
    ("background noise", 0.3, True, Decision.IGNORED),
    ("music playing", 0.4, True, Decision.IGNORED),

    # === 11. Rapid repetition (user frustration) ===
    ("stop stop stop stop stop", 0.99, True, Decision.INTERRUPT),
    ("wait wait okay", 0.98, True, Decision.INTERRUPT),
    ("umm stop haan stop", 0.97, True, Decision.INTERRUPT),

    # === 12. Very low confidence quiet user ===
    ("uh", 0.1, False, Decision.FORWARDED),
    ("umm", 0.2, False, Decision.FORWARDED),

    # === 13. High-confidence noise during quiet ===
    ("random word", 0.9, False, Decision.FORWARDED),
    ("music", 0.88, False, Decision.FORWARDED),
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
        print("🎯 All edge cases handled successfully!")
    else:
        print("⚠️ Some cases failed — inspect logs for reasons.")

if __name__ == "__main__":
    asyncio.run(run_tests())
