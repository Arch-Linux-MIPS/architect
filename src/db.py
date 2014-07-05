import rethinkdb as r

from config import Config

class DB:
	def connect():
		conn = r.connect(Config.db_host(), Config.db_port())
		conn.use(Config.db_name())
		return conn

	def recent_builds(n=10, show_all=False):
		with DB.connect() as conn:
			q = r.table("builds")

			if not show_all:
				q = q.group("pkg").max("time_start").ungroup()["reduction"]

			q = q.order_by(r.desc("time_start")).limit(n)

			return list(q.run(conn))

	def insert_build(build):
		with DB.connect() as conn:
			return r.table("builds").insert(build).run(conn)
