import pytest
import aiosqlite
import database


@pytest.mark.asyncio
async def test_init_database(db_path):
    await database.init_database(db_path)

    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()
        await cursor.execute('''
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='hieroglyphs'
        ''')

        assert await cursor.fetchone() is not None

        await cursor.execute('''
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='usages'
        ''')

        assert await cursor.fetchone() is not None


@pytest.mark.asyncio
async def test_get_all_hieroglyphs(initialized_db):
    """проверка если бд не пуста"""
    all_hieroglyphs = await database.get_all_hieroglyphs(initialized_db)

    assert len(all_hieroglyphs) == 1

    assert isinstance(all_hieroglyphs, list) and isinstance(all_hieroglyphs[0], dict)

    assert "id" in all_hieroglyphs[0] and "hieroglyph" in all_hieroglyphs[0]

    assert all_hieroglyphs[0]["hieroglyph"] == "日"


@pytest.mark.asyncio
async def test_get_all_hieroglyphs_empty(db_path):
    """проверка если бд пуста"""
    await database.init_database(db_path)

    all_hieroglyphs = await database.get_all_hieroglyphs(db_path)

    assert len(all_hieroglyphs) == 0


@pytest.mark.asyncio
async def test_get_by_hieroglyph(initialized_db):
    non_existing_hieroglyph = await database.get_by_hieroglyph("月", initialized_db)

    assert non_existing_hieroglyph is None

    existing_hieroglyph = await database.get_by_hieroglyph("日", initialized_db)

    assert existing_hieroglyph is not None

    assert isinstance(existing_hieroglyph, dict) and len(existing_hieroglyph) == 2

    assert "hieroglyphs" in existing_hieroglyph and "usages" in existing_hieroglyph

    assert existing_hieroglyph["hieroglyphs"] == "日"

    keys = ["id", "usage", "reading", "translation"]
    values = [1, "日", "ひ", "солнце"]
    for key, value in zip(keys, values):
        assert existing_hieroglyph["usages"][0][key] == value


@pytest.mark.asyncio
async def test_add_card(initialized_db):
    """не проверяем вариант некорректного ввода usages, оно проверяется в main.py"""
    """добавление пустой строки, иероглифа с 1 использованием и добавление уже существующего иероглифа"""
    empty_hieroglyph = await database.add_card("  ", [{"usage": "月", "reading": "つき", "translation": "луна"}], initialized_db)
    assert not empty_hieroglyph

    await database.add_card("月", [{"usage": "月", "reading": "つき", "translation": "луна"}], initialized_db)
    assert await database.get_all_hieroglyphs(initialized_db) ==  [{'hieroglyph': '日', 'id': 1}, {'hieroglyph': '月', 'id': 2}]

    new_data1 = await database.get_by_hieroglyph("月", initialized_db)
    assert new_data1

    await database.add_card("月", [{"usage": "月", "reading": "げつ", "translation": "месяц"}], initialized_db)

    assert await database.get_all_hieroglyphs(initialized_db) ==  [{'hieroglyph': '日', 'id': 1}, {'hieroglyph': '月', 'id': 2}]

    new_data2 = await database.get_by_hieroglyph("月", initialized_db)

    assert "usages" in new_data2

    assert len(new_data2["usages"]) == 2


@pytest.mark.asyncio
async def test_edit_card_by_usage_id(initialized_db):
    result_no_such_id = await database.edit_card_by_usage_id(2, "げつ", "месяц", initialized_db)
    assert not result_no_such_id

    result_reading = await database.edit_card_by_usage_id(usage_id=1, new_reading="げつ", db_path=initialized_db)
    assert result_reading

    sun_info1 = await database.get_by_hieroglyph("日", initialized_db)
    assert len(sun_info1["usages"]) == 1

    assert sun_info1["usages"][0]["reading"] == "げつ"

    assert sun_info1["usages"][0]["translation"] == "солнце"

    result_translation = await database.edit_card_by_usage_id(usage_id=1, new_translation="месяц", db_path=initialized_db)
    assert result_translation

    sun_info2 = await database.get_by_hieroglyph("日", initialized_db)
    assert len(sun_info2["usages"]) == 1

    assert sun_info2["usages"][0]["reading"] == "げつ"

    assert sun_info2["usages"][0]["translation"] == "месяц"


@pytest.mark.asyncio
async def test_add_one_usage(initialized_db):
    result_no_hieroglyph = await database.add_one_usage("月", "月","つき", "луна", initialized_db)
    assert not result_no_hieroglyph

    result_have_hieroglyph = await database.add_one_usage("日", "月","つき", "луна", initialized_db)
    assert result_have_hieroglyph

    sun_info = await database.get_by_hieroglyph("日", initialized_db)
    assert len(sun_info["usages"]) == 2


@pytest.mark.asyncio
async def test_delete_hieroglyph(initialized_db):
    result_no_hieroglyph = await database.delete_hieroglyph("月", initialized_db)
    assert not result_no_hieroglyph

    result_have_hieroglyph = await database.delete_hieroglyph("日", initialized_db)
    assert result_have_hieroglyph

    async with aiosqlite.connect(initialized_db) as connection:
        cursor = await connection.cursor()
        await cursor.execute('SELECT COUNT(*) FROM hieroglyphs')

        result_hieroglyphs = await cursor.fetchone()
        assert result_hieroglyphs[0] == 0

        await cursor.execute('SELECT COUNT(*) FROM usages')

        result_usages = await cursor.fetchone()
        assert result_usages[0] == 0






















