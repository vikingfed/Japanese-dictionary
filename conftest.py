import pytest
import aiosqlite
import database
from fastapi.testclient import TestClient
import main


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db" # уникальный путь для каждого теста


@pytest.fixture
async def initialized_db(tmp_path):
    db_path = tmp_path / "test.db"

    await database.init_database(db_path)

    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()
        await cursor.execute('INSERT OR IGNORE INTO hieroglyphs (hieroglyph) VALUES (?)',
                             ("日",)
        )

        await cursor.execute(
            '''INSERT INTO usages
            (hieroglyph_id, usage, reading, translation)
            VALUES (?, ?, ?, ?)''', (1, "日", "ひ", "солнце")
        )

        await connection.commit()

    yield db_path


@pytest.fixture
def client():
    return TestClient(main.app)











