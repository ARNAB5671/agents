import asyncio
from agents.extensions.interrupt_handler.interrupt_handler import InterruptHandler, Decision

async def demo():
    handler = InterruptHandler()

    # Agent starts speaking
    await handler.agent_state.set_speaking(True)
    print("\nAgent speaking...\n")

    tests = [
        ("umm", 0.9),
        ("uh hmm", 0.92),
        ("umm okay stop", 0.95),
        ("hmm yeah", 0.3),
    ]

    for text, conf in tests:
        result = await handler.handle_transcript(text, conf)
        print(f"Input: '{text}' -> Decision: {result}")

    # Agent stops speaking
    await handler.agent_state.set_speaking(False)
    print("\nAgent quiet...\n")

    result = await handler.handle_transcript("umm", 0.9)
    print(f"Input: 'umm' -> Decision: {result}")

asyncio.run(demo())
