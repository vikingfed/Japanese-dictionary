from typing import List, Optional, Dict
import aiosqlite


async def init_database(db_path = 'japanese.db'):
    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS hieroglyphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hieroglyph TEXT NOT NULL UNIQUE
            )
        ''')

        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS usages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hieroglyph_id INTEGER NOT NULL,
                usage TEXT NOT NULL,
                reading TEXT NOT NULL,
                translation TEXT NOT NULL,
                FOREIGN KEY (hieroglyph_id) REFERENCES hieroglyphs (id)
            )
        ''')

        await connection.commit()


async def get_all_hieroglyphs(db_path = 'japanese.db'):
    async with aiosqlite.connect(db_path) as connection:
        connection.row_factory = aiosqlite.Row
        cursor = await connection.cursor()
        await cursor.execute('SELECT id, hieroglyph FROM hieroglyphs')
        return [dict(row) for row in await cursor.fetchall()]


async def get_by_hieroglyph(hieroglyph: str, db_path = 'japanese.db'):
    async with aiosqlite.connect(db_path) as connection:
        connection.row_factory = aiosqlite.Row # делает формат возвращаемых данных из бд не кортежем, а типо словариком (доступ по имени столбца)
        cursor = await connection.cursor()
        await cursor.execute('''
            SELECT id, hieroglyph 
            FROM hieroglyphs WHERE hieroglyph = ?''',
            (hieroglyph, )
        )
        fetched_data = await cursor.fetchone()

        if not fetched_data:
            return None

        await cursor.execute('''
            SELECT id, usage, reading, translation
            FROM usages 
            WHERE hieroglyph_id = ? 
            ORDER BY id
        ''', (fetched_data['id'], )
        )

        usages = [dict(row) for row in await cursor.fetchall()] # список словарей, где ключи - айди варианта, вариант использования, чтение и перевод

        return {
            'hieroglyphs': fetched_data['hieroglyph'],
            'usages': usages
        }


async def add_card(hieroglyph: str, usages: List[Dict], db_path = 'japanese.db'):
    if not hieroglyph or not hieroglyph.strip(): # пустая строка
        return False

    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()
        await cursor.execute('INSERT OR IGNORE INTO hieroglyphs (hieroglyph) VALUES (?)',
                       (hieroglyph, )
        )

        await cursor.execute('SELECT id FROM hieroglyphs WHERE hieroglyph = ?', (hieroglyph, ))
        result = await cursor.fetchone()

        hieroglyph_id = result[0] # эта функция возвращает кортеж, fetchall() - список кортежей

        for usage in usages:
            await cursor.execute(
                '''INSERT INTO usages
                (hieroglyph_id, usage, reading, translation)
                VALUES (?, ?, ?, ?)''', (hieroglyph_id, usage['usage'], usage['reading'], usage['translation'])
            )

        await connection.commit()
        return True


async def edit_card_by_usage_id(usage_id: int,
                                new_reading: Optional[str] = None,
                                new_translation: Optional[str] = None,
                                db_path='japanese.db'):
    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()
        await cursor.execute('SELECT id FROM usages WHERE id = ?', (usage_id,))
        if not await cursor.fetchone():
            return False

        if new_reading:
            await cursor.execute('''
                UPDATE usages SET reading = ? WHERE id = ?
            ''', (new_reading, usage_id)
            )
        if new_translation:
            await cursor.execute('''
                UPDATE usages SET translation = ? WHERE id = ?
            ''', (new_translation, usage_id)
            )

        await connection.commit()
        return True


async def add_one_usage(hieroglyph: str,
                        new_usage: str,
                        reading: str,
                        translation: str,
                        db_path = 'japanese.db'):
    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()
        await cursor.execute('''
            SELECT id FROM hieroglyphs WHERE hieroglyph = ?
        ''', (hieroglyph, )
                       )
        result = await cursor.fetchone()
        if not result:
            return False

        hieroglyph_id = result[0]

        await cursor.execute('''
            INSERT INTO usages
                (hieroglyph_id, usage, reading, translation)
                VALUES (?, ?, ?, ?)
        ''', (hieroglyph_id, new_usage, reading, translation))

        await connection.commit()
        return True


async def delete_hieroglyph(hieroglyph: str, db_path = 'japanese.db'):
    async with aiosqlite.connect(db_path) as connection:
        cursor = await connection.cursor()

        await cursor.execute('SELECT id FROM hieroglyphs WHERE hieroglyph = ?', (hieroglyph,))
        result = await cursor.fetchone()

        if not result:
            return False

        hieroglyph_id = result[0]

        await cursor.execute('''
                    DELETE FROM usages WHERE hieroglyph_id = ?
                ''', (hieroglyph_id,)
                       )

        await cursor.execute('''
            DELETE FROM hieroglyphs WHERE hieroglyph = ?
        ''', (hieroglyph, )
                       )

        await connection.commit()
        return True