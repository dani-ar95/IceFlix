import sqlite3

conn = sqlite3.connect("media.db")

c = conn.cursor()

c.execute("DROP TABLE media")
conn.commit()

c.execute("""CREATE TABLE media (
    id text,
    name text)""")


peli_1 = ("identificador1", "aventura comedia")
peli_2 = ("identificador2", "musical")
peli_3 = ("identificador3", "drama familiar")

c.execute("INSERT INTO media VALUES (?, ?)", (peli_1))
conn.commit()
c.execute("INSERT INTO media VALUES (?, ?)", (peli_2))
conn.commit()
c.execute("INSERT INTO media VALUES (?, ?)", (peli_3))
conn.commit()

conn.close()