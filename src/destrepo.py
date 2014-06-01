import os

from binaryrepo import BinaryRepo

class DestRepo(BinaryRepo):
	def __init__(self, name, path, arch):
		self._arch = arch
		BinaryRepo.__init__(self, name, path)

	def init_paths(self, name, path):
		self._cache_db = os.path.join(path, "os", self._arch, "{0}.db.tar.gz".format(self._name))
		self._cache_src = None

	def download(self, url, filename):
		raise Exception()

	def refresh(self):
		self.read_packages()
