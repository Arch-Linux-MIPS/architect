import os
import subprocess

from config import Config
from sourcerepo import SourceRepo
from utils import slugify

class GitSourceRepo(SourceRepo):
	def __init__(self, name, url):
		SourceRepo.__init__(self, name)
		self._url = url

		cache_dir = os.path.join(Config.cache_dir(), slugify(url))
		self._repo = os.path.join(cache_dir, "repo")
		self._cache = os.path.join(cache_dir, "cache")
		if not os.path.isdir(self._cache):
			os.makedirs(self._cache, 0o755)

		if os.path.exists(self._repo):
			self.read_sources()

	def git_clone(self):
		print("Clone {0}".format(self._url))

		pgit = subprocess.Popen(["git", "clone", self._url, "repo"],
					cwd=os.path.dirname(self._repo),
					stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		try:
			sout, serr = pgit.communicate()
		except Exception as ex:
			sout = ""
			serr = str(ex)

		if pgit.returncode != 0:
			raise Exception("git returned {0}".format(pgit.returncode))

	def git_update(self):
		print("Update {0}".format(self._repo))

		pgit = subprocess.Popen(["git", "pull"], cwd=self._repo,
					stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		try:
			sout, serr = pgit.communicate()
		except Exception as ex:
			sout = ""
			serr = str(ex)

		if pgit.returncode != 0:
			raise Exception("git returned {0}".format(pgit.returncode))

	def refresh(self):
		if os.path.exists(self._repo):
			self.git_update()
		else:
			self.git_clone()

		self.read_sources()
