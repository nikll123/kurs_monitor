import sqlite3

conn = sqlite3.connect('kursdb.db')

c = conn.cursor()

# res = c.execute("""
# SELECT * FROM kurs WHERE currency = 'SEK'
# """)

# for r in res.fetchmany(5):
    # print (r)

res = c.execute("""
UPDATE kurs SET currency = 'SEK' WHERE id=654
""")

conn.commit()

res = c.execute("""
SELECT * FROM kurs WHERE currency = 'CHF'
""")

for r in res.fetchall():
    print (r)

conn.close()

