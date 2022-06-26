#!/usr/bin/python3
import sqlite3
from os import path, rename
DB_PATH = path.join(path.dirname(__file__), "media.db")


if __name__ == '__main__':
    conn = sqlite3.connect(DB_PATH)
    ddbb_cursor = conn.cursor()
    ddbb_cursor.execute("""CREATE TABLE media (
                        media_id text,
                        media_name text,
                        username text,
                        tags text,
                        provider text)
                        """)
    #ddbb_cursor.execute("DROP TABLE media")
    #conn.execute("INSERT INTO media VALUES ('ID2', 'video2', 'paco', 'melon sandia pruebo', 'Non')")
    # conn.execute("INSERT INTO media VALUES ('ID2', 'video2', 'vicente', 'naranja fruta pueblo', 'Non')")
    # conn.execute("INSERT INTO media VALUES ('ID3', 'video3', 'vicente', '1 2 3', 'Non')")
    # conn.execute("INSERT INTO media VALUES ('ID4', 'video4', 'vicente', 'a b c', 'Non')")
    
    #ddbb_cursor.execute("SELECT media_id, tags from media where username='vicente'")
    #ddbb_cursor.execute("SELECT * from media")
    # conn.commit()
    query = ddbb_cursor.fetchall()
    conn.close()
    print(query)
