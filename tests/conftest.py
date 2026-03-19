import os
from pathlib import Path


TEST_DB_PATH = Path(__file__).resolve().parent / "test_agent.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
os.environ["APP_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
