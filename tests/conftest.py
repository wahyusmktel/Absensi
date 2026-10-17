"""
Fixture pengujian Pytest untuk mengelola event loop sesi tunggal di Windows.
"""

import asyncio
import pytest
from app.core.database import async_engine
from app.core.init_db import init_db


@pytest.fixture(scope="session")
def event_loop():
    """
    Membuat satu event loop untuk seluruh sesi pengujian pytest.
    Mencegah penutupan event loop prematur antar-test yang memutus pool asyncpg di Windows.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.run_until_complete(async_engine.dispose())
    loop.close()
