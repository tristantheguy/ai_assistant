import asyncio
from agent import ClippyAgent


class DiscordAgent:
    """Wrapper around ``ClippyAgent`` that sends messages to a Discord channel."""

    class _ChannelWindow:
        def __init__(self, channel, loop):
            self._channel = channel
            self._loop = loop

        def display_message(self, text: str) -> None:
            """Schedule sending ``text`` to the Discord ``channel``."""
            fut = asyncio.run_coroutine_threadsafe(
                self._channel.send(text), self._loop
            )
            try:
                fut.result()
            except Exception:
                pass

    def __init__(self, channel, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.channel = channel
        self._agent = ClippyAgent(self._ChannelWindow(channel, self.loop))

    def start(self) -> None:
        self._agent.start()

    def stop(self) -> None:
        self._agent.stop()

    def handle_text(self, text: str) -> None:
        self._agent.handle_text(text)
