import sqlite3

conn = sqlite3.connect("media.db")

c = conn.cursor()

c.execute("""CREATE TABLE media (
    id text, 
    tag text,
    name text,""")

conn.commit()
conn.close()    