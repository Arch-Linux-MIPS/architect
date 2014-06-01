import os
import requests
import tarfile
import urllib

from email.utils import formatdate

from config import Config
from repo import BinPkg
from repo import PkgDep
from repo import PkgVersion
from repo import SrcPkg
from repo import Repo
from utils import slugify

class BinaryRepo(Repo):
	def __init__(self, name, url):
		Repo.__init__(self, name)
		self.init_paths(name, url)
		self.read_packages()

	def init_paths(self, name, url):
		self._url_db = "{0}/{1}.db".format(url, name)
		self._url_src = "{0}/{1}.abs.tar.gz".format(url, name)

		cache_dir = os.path.join(Config.cache_dir(), slugify(url))
		if not os.path.isdir(cache_dir):
			os.makedirs(cache_dir, 0o755)

		self._cache_db = os.path.join(cache_dir, "db")
		self._cache_src = os.path.join(cache_dir, "src")

	def download(self, url, filename):
		headers = {}
		if os.path.exists(filename):
			mod = os.path.getmtime(filename)
			headers["If-Modified-Since"] = formatdate(timeval=mod, usegmt=True)

		req = requests.get(url, headers=headers)

		if req.status_code == 304:
			return False

		if req.status_code != 200:
			raise Exception()

		print("Downloading {0}".format(url))

		with open(filename, "wb") as file:
			for chunk in req.iter_content(4096):
				file.write(chunk)

		return True

	def refresh(self):
		self.download(self._url_src, self._cache_src)
		self.download(self._url_db, self._cache_db)

		self.read_packages()

	def read_packages(self):
		print("Reading {0}...".format(self._cache_db), end="", flush=True)

		if not os.path.exists(self._cache_db):
			print(" not found!")
			return False
		if not tarfile.is_tarfile(self._cache_db):
			print(" not a tar!")
			return False

		tar = tarfile.open(self._cache_db)
		pkg_info = {}
		self._pkgs = {}

		for info in tar.getmembers():
			if not info.isfile():
				continue

			( binpkg_name, file_name ) = info.name.split("/")

			pi = pkg_info.get(binpkg_name, {})
			with tar.extractfile(info) as file:
				pi[file_name] = [x.decode("utf-8").rstrip() for x in file.readlines()]

			if len(pi.keys() & { "desc", "depends" }) == 2:
				BinaryRepo.BinPkg(self, pi["desc"], pi["depends"])
				del pkg_info[binpkg_name]
				continue

			pkg_info[binpkg_name] = pi

		if len(pkg_info) != 0:
			raise Exception("Incomplete packages in DB")

		print(" done")

	class SrcPkg(SrcPkg):
		def __init__(self, repo, name, ver):
			SrcPkg.__init__(self, repo, name, ver)

	class BinPkg(BinPkg):
		def __init__(self, repo, desc, deps):
			desc = BinaryRepo.BinPkg.parse_arrays(desc)
			deps = BinaryRepo.BinPkg.parse_arrays(deps)

			name = desc["name"][0]
			ver = PkgVersion.parse(desc["version"][0])

			base = desc.get("base", [name])[0]
			srcpkg = repo._pkgs.get(base, None)
			if srcpkg is None:
				srcpkg = BinaryRepo.SrcPkg(repo, base, ver)
				repo._pkgs[base] = srcpkg

			BinPkg.__init__(self, srcpkg, name, ver)

			self._desc = desc.get("desc", [""])[0]
			self._deps = set([PkgDep(d) for d in deps.get("depends", [])])
			self._groups = set(desc.get("groups", []))

			srcpkg._pkgs[name] = self

			for d in deps.get("checkdepends", []):
				srcpkg._checkdeps.add(PkgDep(d))
			for d in deps.get("makedepends", []):
				srcpkg._makedeps.add(PkgDep(d))

		def parse_arrays(lines):
			ret = {}
			current = None
			current_name = None

			for l in lines:
				if len(l) == 0:
					if current is not None:
						ret[current_name] = current
					current = None
					continue

				if current is None:
					if not l.startswith("%") or not l.endswith("%"):
						raise Exception("Invalid start line '{0}'".format(l))
					current = []
					current_name = l.strip("%").lower()
					continue

				current.append(l)

			return ret
