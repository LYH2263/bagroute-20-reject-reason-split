"""导入应用前先把数据库指向临时 SQLite，避免依赖 Postgres。"""

import os
import tempfile

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()

os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{_db_file.name}")
os.environ.setdefault("SEED_ON_EMPTY", "false")
