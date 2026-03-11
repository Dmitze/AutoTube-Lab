"""Phase 5+ — Storage adapters sub-package.

Adapters
--------
StorageAdapter (base) : ABC with save/load/list operations
InMemoryStorage       : dict-based, O(1), for tests (re-export from synthetic)
SQLiteStorage         : SQLite + WAL mode for production

Selection logic:
  STORAGE_BACKEND=memory → InMemoryStorage
  STORAGE_BACKEND=sqlite → SQLiteStorage (YTAIMBOT_DATA_DIR/db/ytaimbot.db)

Status: 🔲 Pending — T-431 (Phase 5, SQLite implementation)
         ✅ InMemoryStorage done (Phase 0, modules/adapters/synthetic.py)
"""
