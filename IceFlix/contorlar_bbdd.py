import sqlite3

conn = sqlite3.connect("media.db")

c = conn.cursor()

c.execute("""CREATE TABLE media (
    id text, 
    tag text,
    name text)""")


peli_1=("identificador1","aventura comedia", "Las maravillosas aventuras de Homero y Bartolo")
peli_2=("identificador2","musical", "Cantando LaLaLa")
peli_3=("identificador3","drama familiar", "Los 3 cerditos versión carne y hueso")

c.execute("INSERT INTO media VALUES (?, ?, ?)", (peli_1))
conn.commit()
c.execute("INSERT INTO media VALUES (?, ?, ?)", (peli_2))
conn.commit()
c.execute("INSERT INTO media VALUES (?, ?, ?)", (peli_3))
conn.commit()

conn.close()    