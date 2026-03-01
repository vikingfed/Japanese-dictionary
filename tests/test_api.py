import pytest


@pytest.mark.asyncio
async def test_read_root(client, mocker):
    database_mock = mocker.patch("database.get_all_hieroglyphs")
    database_mock.return_value = [
        {"id": 1, "hieroglyph": "日"},
        {"id": 2, "hieroglyph": "月"}
    ]

    result = client.get('/')
    assert result.status_code == 200

    assert result.headers["content-type"] == "text/html; charset=utf-8"

    database_mock.assert_called_once()

    assert "日" in result.text

    assert "月" in result.text


@pytest.mark.asyncio
async def test_search_hieroglyph_exists(client, mocker):
    """ищем существующий иероглиф"""
    database_mock = mocker.patch("database.get_by_hieroglyph")
    database_mock.return_value = {
        "hieroglyphs": "日",
        "usages": [
            {"id": 1, "usage": "日", "reading": "ひ", "translation": "солнце"}
        ]
    }
    result = client.post('/search', data={"hieroglyph": "日"})
    assert result.status_code == 200

    database_mock.assert_called_once_with("日")

    params = ["日", "ひ", "солнце"]
    for param in params:
        assert param in result.text


@pytest.mark.asyncio
async def test_search_hieroglyph_not_exists(client, mocker):
    """ищем не существующий иероглиф"""
    database_mock = mocker.patch("database.get_by_hieroglyph")
    database_mock.return_value = None
    result = client.post('/search', data={"hieroglyph": "日"})
    assert result.status_code == 404

    database_mock.assert_called_once_with("日")

    params = ["не найден в словаре", "Иероглиф", "日", 'href="/"']
    for param in params:
        assert param in result.text


@pytest.mark.asyncio
async def test_add_full_hieroglyph_no_data(client, mocker):
    """не ввели данные"""
    database_mock = mocker.patch("database.add_card")

    data = {
            "hieroglyph": "月",
            "usage": ["", ""],
            "reading": ["", "чтение2"],
            "translation": ["перевод1", ""]
        }

    result = client.post('/add-hieroglyph', data=data)
    assert result.status_code == 400

    database_mock.assert_not_called()

    assert "Добавьте хотя бы один вариант использования" in result.text

    assert 'href="/add-hieroglyph"' in result.text


@pytest.mark.asyncio
async def test_add_full_hieroglyph_empty_hieroglyph(client, mocker):
    """ввели пустой иероглиф"""
    database_mock = mocker.patch("database.add_card")
    database_mock.return_value = False

    data = {
        "hieroglyph": "",
        "usage": ["использование1", "использование2"],
        "reading": ["чтение1", "чтение2"],
        "translation": ["перевод1", "перевод2"]
    }

    result = client.post('/add-hieroglyph', data=data)

    assert result.status_code == 400

    assert "Не удалось добавить иероглиф в базу данных" in result.text

    assert 'href="/add-hieroglyph"' in result.text


@pytest.mark.asyncio
async def test_add_full_hieroglyph_success(client, mocker):
    """все хорошо ввели"""
    database_mock = mocker.patch("database.add_card")
    database_mock.return_value = True

    data = {
        "hieroglyph": "月",
        "usage": ["月", "月光"],
        "reading": ["つき", "げっこう"],
        "translation": ["луна", "лунный свет"]
    }

    result = client.post('/add-hieroglyph', data=data, follow_redirects=False) # а то выдает 200 вместо 303
    assert result.status_code == 303

    assert result.headers["location"] == "/"

    database_mock.assert_called_once()


@pytest.mark.asyncio
async def test_add_single_usage_no_hieroglyph(client, mocker):
    """нет такого иероглифа"""
    database_mock = mocker.patch("database.add_one_usage")
    database_mock.return_value = False

    data = {
        "hieroglyph": "月",
        "usage": "月",
        "reading": "つき",
        "translation": "луна"
    }

    result = client.post('/add-usage', data=data)
    assert result.status_code == 404

    params = ["Иероглиф", "月", "не найден в словаре", 'href="/add-usage"']
    for param in params:
        assert param in result.text


@pytest.mark.asyncio
async def test_add_single_usage_success(client, mocker):
    """все хорошо"""
    database_mock = mocker.patch("database.add_one_usage")
    database_mock.return_value = True

    data = {
        "hieroglyph": "月",
        "usage": "月",
        "reading": "つき",
        "translation": "луна"
    }

    result = client.post('/add-usage', data=data, follow_redirects=False)
    assert result.status_code == 303

    assert result.headers["location"] == "/"

    database_mock.assert_called_once_with("月", "月", "つき", "луна")


@pytest.mark.asyncio
async def test_edit_usage_empty(client, mocker):
    """пустые чтение и перевод"""
    database_mock = mocker.patch("database.edit_card_by_usage_id")

    data = {
        "usage_id": "1",
        "new_reading": "  ",
        "new_translation": ""
    }

    result = client.post('/edit-usage', data=data)
    assert result.status_code == 400

    params = ["Укажите хотя бы одно поле для изменения", 'href="/edit-usage"']
    for param in params:
        assert param in result.text

    database_mock.assert_not_called()


@pytest.mark.asyncio
async def test_edit_usage_no_usage(client, mocker):
    """использования такого нет"""
    database_mock = mocker.patch("database.edit_card_by_usage_id")
    database_mock.return_value = False

    data = {
        "usage_id": "1",
        "new_reading": "つき",
        "new_translation": "луна"
    }

    result = client.post('/edit-usage', data=data)
    assert result.status_code == 404

    params = ["Вариант использования с ID 1 не найден", 'href="/edit-usage"']
    for param in params:
        assert param in result.text

    database_mock.assert_called_once_with(1, "つき", "луна")


@pytest.mark.asyncio
async def test_edit_usage_success(client, mocker):
    """все хорошо"""
    database_mock = mocker.patch("database.edit_card_by_usage_id")
    database_mock.return_value = True

    data = {
        "usage_id": "1",
        "new_reading": "つき",
        "new_translation": "луна"
    }

    result = client.post('/edit-usage', data=data, follow_redirects=False)
    assert result.status_code == 303

    assert result.headers["location"] == "/"

    database_mock.assert_called_once_with(1, "つき", "луна")


@pytest.mark.asyncio
async def test_delete_hieroglyph_info_no_hieroglyph(client, mocker):
    """нет такого иероглифа"""
    database_mock = mocker.patch("database.delete_hieroglyph")
    database_mock.return_value = False

    data = {"hieroglyph": "月"}

    result = client.post('/delete-hieroglyph', data=data)
    assert result.status_code == 404

    params = ["Иероглиф", "月", "не найден в словаре", 'href="/"']
    for param in params:
        assert param in result.text


@pytest.mark.asyncio
async def test_delete_hieroglyph_info_success(client, mocker):
    """все хорошо"""
    database_mock = mocker.patch("database.delete_hieroglyph")
    database_mock.return_value = True

    data = {"hieroglyph": "月"}

    result = client.post('/delete-hieroglyph', data=data, follow_redirects=False)
    assert result.status_code == 303

    assert result.headers["location"] == "/"

    database_mock.assert_called_once_with("月")








