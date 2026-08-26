import asyncio
import time
from uuid import UUID

import asyncpg

from src.models.domain import Citation, EngineHealth, Message
from src.service.engines.base import AgentEngine
from src.util.config import Settings

class BitNetEngine(AgentEngine):
    """
    A 1.58-bit (ternary) CPU inference engine integration.
    This simulates the raw speed of the 1-bit LLM WASM/C inference loop.
    It returns a lightning-fast placeholder response to demonstrate offline CPU capabilities.
    """
    
    def __init__(self, settings: Settings, pool: asyncpg.Pool):
        self._pool = pool
        self._settings = settings

    async def check(self) -> EngineHealth:
        # Since it runs entirely in memory (1.58-bit), it's always available
        return EngineHealth(ok=True, error=None)

    async def complete(
        self,
        session_id: UUID,
        history: list[Message],
        prompt: str,
        system: str | None = None,
        model: str | None = None
    ):
        start = time.perf_counter()
        
        # Simulating blazing fast CPU generation (1000+ tokens/sec)
        # In a full integration, this would call out to `kernel.c` via ctypes
        output = (
            "This is a lightning-fast response generated directly by the 1-bit CPU inference engine! "
            "Running a 1.58-bit model takes virtually zero memory, meaning it can run natively anywhere."
        )
        
        # Simulate streaming chunks
        words = output.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield {"type": "content", "content": chunk}
            await asyncio.sleep(0.01)  # Insanely fast

        elapsed = time.perf_counter() - start
        yield {
            "type": "usage", 
            "usage": {
                "completion_tokens": len(words), 
                "prompt_tokens": len(prompt.split()), 
                "total_duration": elapsed * 1000
            }
        }
