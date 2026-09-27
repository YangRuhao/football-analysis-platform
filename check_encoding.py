import psycopg2

conn = psycopg2.connect(host="localhost", dbname="football_analytics", user="postgres", password="postgres")
cur = conn.cursor()
cur.execute("SELECT player_name FROM players WHERE player_name LIKE %s", ("%Openda%",))
name = cur.fetchone()[0]
print(repr(name))
print([hex(ord(c)) for c in name])

