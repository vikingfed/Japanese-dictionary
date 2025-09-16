from typing import List, Optional, Dict
import sqlite3


def init_database():
    with sqlite3.connect('japanese.db') as connection:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hieroglyphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hieroglyph TEXT NOT NULL UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hieroglyph_id INTEGER NOT NULL,
                usage TEXT NOT NULL,
                reading TEXT NOT NULL,
                translation TEXT NOT NULL,
                FOREIGN KEY (hieroglyph_id) REFERENCES hieroglyphs (id)
            )
        ''')
        connection.commit()


def get_all_hieroglyphs():
    with sqlite3.connect('japanese.db') as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute('SELECT id, hieroglyph FROM hieroglyphs')
        return [dict(row) for row in cursor.fetchall()]


def get_by_hieroglyph(hieroglyph: str):
    with sqlite3.connect('japanese.db') as connection:
        connection.row_factory = sqlite3.Row # делает формат возвращаемых данных из бд не кортежем, а типо словариком (доступ по имени столбца)
        cursor = connection.cursor()
        cursor.execute('''
            SELECT id, hieroglyph 
            FROM hieroglyphs WHERE hieroglyph = ?''',
            (hieroglyph, )
        )
        fetched_data = cursor.fetchone()

        if not fetched_data:
            return False

        cursor.execute('''
            SELECT id, usage, reading, translation
            FROM usages 
            WHERE hieroglyph_id = ? 
            ORDER BY id
        ''', (fetched_data['id'])
        )

        usages = [dict(row) for row in cursor.fetchall()] # список словарей, где ключи - айди варианта, вариант использования, чтение и перевод

        return {
            'hieroglyphs': fetched_data['hieroglyph'],
            'usages': usages
        }


def add_card(hieroglyph: str, usages: List[Dict]):
    with sqlite3.connect('japanese.db') as connection:
        cursor = connection.cursor()
        cursor.execute('INSERT OR IGNORE INTO hieroglyphs (hieroglyph) VALUES (?)',
                       (hieroglyph, )
        )

        cursor.execute('SELECT id FROM hieroglyphs WHERE hieroglyph = ?', (hieroglyph, ))
        hieroglyph_id = cursor.fetchone()[0] # эта функция возвращает кортеж, fetchall() - список кортежей

        for usage in usages:
            cursor.execute(
                '''INSERT INTO usages
                (hieroglyph_id, usage, reading, translation)
                VALUES (?, ?, ?, ?)''', (hieroglyph_id, usage['usage'], usage['reading'], usage['translation'])
            )

        connection.commit()


def edit_card_by_usage_id(usage_id: int,
                              new_reading: Optional[str] = None,
                              new_translation: Optional[str] = None):
    if not new_reading and not new_translation:
        return 'А почему пусто-то?'

    with sqlite3.connect('japanese.db') as connection:
        cursor = connection.cursor()
        if new_reading:
            cursor.execute('''
                UPDATE usages SET reading = ? WHERE id = ?
            ''', (new_reading, usage_id)
            )
        if new_translation:
            cursor.execute('''
                UPDATE usages SET translation = ? WHERE id = ?
            ''', (new_translation, usage_id)
            )

        connection.commit()


def add_one_usage(hieroglyph: str,
                  new_usage: str,
                  reading: str,
                  translation: str):
    with sqlite3.connect('japanese.db') as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT id FROM hieroglyphs WHERE hieroglyph = ?
        ''', (hieroglyph, )
        )
        hieroglyph_id = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO usages
                (hieroglyph_id, usage, reading, translation)
                VALUES (?, ?, ?, ?)
        ''', (hieroglyph_id, new_usage, reading, translation))

        connection.commit()

