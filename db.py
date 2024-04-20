import sqlite3
from typing import Optional, List


def get_figure_id_by_name(name: str) -> Optional[int]:
    cursor = get_db_connection().cursor()
    cursor.execute(f"SELECT * FROM rhetorical_figures WHERE name LIKE ?", (name,))
    row = cursor.fetchone()
    if row is None:
        return None
    else:
        return row["figure_id"]


def link_text_with_figures(text_id: int, figure_ids: List[int]) -> None:
    con = get_db_connection()

    links: List[(int, int)] = []  # (text_id, figure_id)
    for figure_id in figure_ids:
        assert isinstance(text_id, int) and text_id >= 0
        assert isinstance(figure_id, int) and figure_id >= 0
        links.append((text_id, figure_id))

    con.executemany("INSERT INTO annotations (text_id, figure_id, verified) VALUES (?, ?, 0)", links)
    con.commit()


def save_new_text(text: str, context: str, author: str, source: str) -> int:
    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("INSERT INTO texts (text, context, author, source) VALUES (?, ?, ?, ?)",
                   (text.strip(), context.strip(), author.strip(), source.strip()))
    new_id = cursor.lastrowid
    con.commit()

    return new_id


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn
