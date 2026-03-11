"""Phase 5+ — Storage adapters sub-package.

Adapters
--------
StorageAdapter (base) : ABC with save/load/list operations
InMemoryStorage       : dict-based, O(1), for tests (re-export from synthetic)
SQLiteStorage         : SQLite + WAL mode for production

Selection logic:
  STORAGE_BACKEND=memory → InMemoryStorage
  STORAGE_BACKEND=sqlite → SQLiteStorage (YTAIMBOT_DATA_DIR/db/ytaimbot.db)

Status: ✅ SQLiteStorage done (Phase 5, T-431 through T-436)
         ✅ InMemoryStorage done (Phase 0, modules/adapters/synthetic.py)
"""

from modules.adapters.storage.sqlite import SQLiteStorage

__all__ = ["SQLiteStorage"]
