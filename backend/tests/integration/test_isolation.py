import pytest
import asyncio
from uuid import uuid4
from src.db.repos import SessionRepo, MessageRepo

@pytest.mark.asyncio
async def test_session_isolation(db_pool):
    """
    Test that messages sent to two different sessions simultaneously do not leak.
    """
    session_repo = SessionRepo(db_pool)
    message_repo = MessageRepo(db_pool)

    # 1. Create two separate sessions
    s1 = await session_repo.create(title="Session 1", provider="local", model="dummy")
    s2 = await session_repo.create(title="Session 2", provider="local", model="dummy")

    # 2. Add messages to them
    await message_repo.add(s1.id, role="user", content="Hello from 1")
    await message_repo.add(s1.id, role="assistant", content="Reply 1")

    await message_repo.add(s2.id, role="user", content="Hello from 2")
    await message_repo.add(s2.id, role="assistant", content="Reply 2")

    # 3. Retrieve messages
    s1_msgs = await message_repo.list_for_session(s1.id)
    s2_msgs = await message_repo.list_for_session(s2.id)

    # 4. Verify isolation
    assert len(s1_msgs) == 2
    assert s1_msgs[0].content == "Hello from 1"
    assert s1_msgs[1].content == "Reply 1"

    assert len(s2_msgs) == 2
    assert s2_msgs[0].content == "Hello from 2"
    assert s2_msgs[1].content == "Reply 2"
