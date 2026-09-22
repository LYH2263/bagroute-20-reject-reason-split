import os
import tempfile

# 必须在导入 app 之前生效：用本地 SQLite 文件替代 postgres，关闭自动 seed
_db_path = os.path.join(tempfile.gettempdir(), "bagroute_pytest.sqlite")
if os.path.exists(_db_path):
    os.remove(_db_path)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["SEED_ON_EMPTY"] = "false"
