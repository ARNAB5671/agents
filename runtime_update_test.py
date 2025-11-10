import asyncio
from agents.extensions.interrupt_handler.interrupt_handler import InterruptHandler


async def main():
    handler = InterruptHandler()

    await handler.agent_state.set_speaking(True)
    print("\n--- Initial run ---")
    await handler.handle_transcript("umm okay stop", 0.95)

    print("\n--- Updating ignored list dynamically ---")
    handler.update_ignored_words(["uh", "umm", "haan", "acha", "arre", "matlab"])

    await handler.handle_transcript("arre hmm wait", 0.90)
    await handler.handle_transcript("matlab hmm okay", 0.92)
    await handler.handle_transcript("umm okay continue", 0.90)

asyncio.run(main())
