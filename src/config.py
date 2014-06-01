import json
import os

class Config:
	_json = {}

	def load(filename):
		fp = None
		success = False

		try:
			fp = open(filename, "r")
			Config._json = json.load(fp)
			success = True
		except:
			Config._json = {}

		if fp is not None:
			fp.close()

		return success

	def get_path(name):
		return os.path.expanduser(Config._json[name]) if name in Config._json else ""

	def architectures():
		return Config._json.get("architectures", [])

	def cache_dir():
		return Config.get_path("cache_dir")

	def db_host():
		return Config._json.get("db_host", "localhost")

	def db_name():
		return Config._json.get("db_name", "archlinuxmips")

	def db_port():
		return Config._json.get("db_port", 28015)

	def rpc_addr():
		return Config._json.get("rpc_addr", "tcp://127.0.0.1:7773")

	def repos():
		return Config._json.get("repos", [])
