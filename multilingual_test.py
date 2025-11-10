import asyncio
from agents.extensions.interrupt_handler.interrupt_handler import InterruptHandler, Decision

async def main():
    handler = InterruptHandler()
    await handler.agent_state.set_speaking(True)

    cases = [
        ("achaa hmm okay", 0.9),
        ("haanji wait", 0.95),
        ("umm chalo stop", 0.93),
        ("theek hai continue", 0.9),
        ("arre arre hmm", 0.88),
    ]

    for i, (text, conf) in enumerate(cases, 1):
        decision = await handler.handle_transcript(text, conf)
        print(f"{i:02d}. text='{text}' -> {decision.name}")

asyncio.run(main())

