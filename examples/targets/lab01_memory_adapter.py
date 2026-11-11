"""Example: connect Lab 01 to your application's memory implementation.

Copy this pattern into your own project and replace DemoProductMemory with
your real memory client or SDK calls.
"""

from agentic_ai_security_lab.memory_isolation import (
    MemoryContext,
    run_memory_isolation_lab,
)


class DemoProductMemory:
    """Small stand-in for an application's real persistent memory API."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, str], str] = {}

    def put_memory(
        self,
        *,
        actor_id: str,
        session_id: str,
        key: str,
        value: str,
    ) -> None:
        del session_id  # persistence intentionally survives session changes
        self._data[(actor_id, key)] = value

    def get_memory(
        self,
        *,
        actor_id: str,
        session_id: str,
        key: str,
    ) -> str | None:
        del session_id
        return self._data.get((actor_id, key))


class ProductMemoryAdapter:
    """Translate the AASL memory contract into the target application's API."""

    def __init__(self, client: DemoProductMemory) -> None:
        self.client = client

    def remember(self, context: MemoryContext, key: str, value: str) -> None:
        self.client.put_memory(
            actor_id=context.actor_id,
            session_id=context.session_id,
            key=key,
            value=value,
        )

    def recall(self, context: MemoryContext, key: str) -> str | None:
        return self.client.get_memory(
            actor_id=context.actor_id,
            session_id=context.session_id,
            key=key,
        )


def main() -> None:
    client = DemoProductMemory()
    adapter = ProductMemoryAdapter(client)
    result = run_memory_isolation_lab(adapter)
    print(result.to_dict())


if __name__ == "__main__":
    main()
