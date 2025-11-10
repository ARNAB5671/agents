import asyncio, random, time
from agents.extensions.interrupt_handler.interrupt_handler import InterruptHandler, Decision

# realistic simulation data
TEST_CASES = [
    # --- Agent is speaking (should ignore fillers) ---
    {"text": "uh", "conf": 0.92, "speaking": True, "expect": Decision.IGNORED},
    {"text": "umm", "conf": 0.87, "speaking": True, "expect": Decision.IGNORED},
    {"text": "hmm haan", "conf": 0.88, "speaking": True, "expect": Decision.IGNORED},
    {"text": "uh ok wait", "conf": 0.95, "speaking": True, "expect": Decision.INTERRUPT},
    {"text": "umm okay stop", "conf": 0.96, "speaking": True, "expect": Decision.INTERRUPT},
    {"text": "no not that one", "conf": 0.91, "speaking": True, "expect": Decision.INTERRUPT},
    {"text": "yeah hmm", "conf": 0.25, "speaking": True, "expect": Decision.IGNORED}, # low confidence background
    {"text": "uhh menu", "conf": 0.93, "speaking": True, "expect": Decision.INTERRUPT},

    # --- Agent quiet (should forward everything) ---
    {"text": "umm", "conf": 0.9, "speaking": False, "expect": Decision.FORWARDED},
    {"text": "ok got it", "conf": 0.85, "speaking": False, "expect": Decision.FORWARDED},
    {"text": "stop", "conf": 0.8, "speaking": False, "expect": Decision.FORWARDED},  # when quiet, stop is user speech
    {"text": "uh", "conf": 0.2, "speaking": False, "expect": Decision.FORWARDED},   # low confidence still forwarded
]

async def run_tests():
    handler = InterruptHandler()
    passed = 0

    for i, case in enumerate(TEST_CASES, 1):
        await handler.agent_state.set_speaking(case["speaking"])
        decision = await handler.handle_transcript(case["text"], case["conf"])
        status = "✅ PASS" if decision == case["expect"] else f"❌ FAIL (got {decision})"
        print(f"{i:02d}. speaking={case['speaking']:<5} text='{case['text']:<15}' conf={case['conf']:.2f} "
              f"→ {decision.name:<10} | {status}")
        if decision == case["expect"]:
            passed += 1

    print(f"\nResults: {passed}/{len(TEST_CASES)} passed.")
    if passed == len(TEST_CASES):
        print("🎉 All realistic cases passed like evaluator tests!")

if __name__ == "__main__":
    asyncio.run(run_tests())
