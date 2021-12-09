import sqlite3

conn = sqlite3.connect("media.db")

c = conn.cursor()

c.execute("DROP TABLE media")
conn.commit()

c.execute("""CREATE TABLE media (
    id text, 
    tags text,
    name text,
    proxy text)""")


peli_1 = ("identificador1", "aventura comedia", "Las maravillosas aventuras de Homero y Bartolo", "insertar proxy")
peli_2 = ("identificador2", "musical", "Cantando LaLaLa", "insertar proxy")
peli_3 = ("identificador3", "drama familiar", "Los 3 cerditos versión carne y hueso", "insertar proxy")

c.execute("INSERT INTO media VALUES (?, ?, ?, ?)", (peli_1))
conn.commit()
c.execute("INSERT INTO media VALUES (?, ?, ?, ?)", (peli_2))
conn.commit()
c.execute("INSERT INTO media VALUES (?, ?, ?, ?)", (peli_3))
conn.commit()

conn.close()