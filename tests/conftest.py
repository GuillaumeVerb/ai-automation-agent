import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = Path(__file__).resolve().parent / "test_agent.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
os.environ["APP_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
