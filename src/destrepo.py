import os
import shutil
import tempfile

from sh import repo_add

from binaryrepo import BinaryRepo

class DestRepo(BinaryRepo):
	def __init__(self, name, path, arch):
		self._arch = arch
		BinaryRepo.__init__(self, name, path)

	def init_paths(self, name, path):
		self._pkg_dir = os.path.join(path, "os", self._arch)
		self._cache_db = os.path.join(self._pkg_dir, "{0}.db.tar.gz".format(self._name))
		self._cache_src = None

	def download(self, url, filename):
		raise Exception()

	def refresh(self):
		self.read_packages()

	def _pkg_repo_path(self, src_path):
		return os.path.join(self._pkg_dir, os.path.basename(src_path))

	def add_packages(self, packages, tmp_dir=None):
		if tmp_dir is None:
			with tempfile.TemporaryDirectory() as td:
				return self.add_packages(packages, tmp_dir=td)

		for src_path in packages:
			if os.path.exists(self._pkg_repo_path(src_path)):
				raise Exception("package {0} already exists".format(
					os.path.basename(src_path)))

		for src_path in packages:
			shutil.copyfile(src_path, self._pkg_repo_path(src_path))

		repo_add(self._cache_db, packages)
