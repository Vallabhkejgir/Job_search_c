import sys

# Fake database module
class DBMod:
    DB_NAME = "old.db"
    def init_db():
        return globals()["DB_NAME"]

db_mod = type(sys)("database")
db_mod.DB_NAME = "old.db"
db_mod.init_db = lambda: db_mod.DB_NAME
sys.modules["database"] = db_mod

# Fake main module
main_mod = type(sys)("main")
exec("""
from database import init_db
def run():
    print("from main:", init_db())
""", main_mod.__dict__)
sys.modules["main"] = main_mod

import main
main.run()

import importlib
import database
# reload simulation
database.DB_NAME = "new_default.db"
database.init_db = lambda: database.DB_NAME

database.DB_NAME = "test.db"

main.run()
