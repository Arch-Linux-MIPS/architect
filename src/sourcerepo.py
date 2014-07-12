import json
import os
import subprocess

from sh import bash

from config import Config
from repo import BinPkg
from repo import PkgDep
from repo import PkgVersion
from repo import SrcPkg
from repo import Repo
from utils import slugify

class SourceRepo(Repo):
	_parse_script = os.path.join(
		os.path.dirname(os.path.realpath(__file__)),
		"spkg-parse.sh")

	def __init__(self, name):
		Repo.__init__(self, name)

	def read_sources(self):
		print("Reading {0}".format(self._repo))

		self._pkgs = {}
		parser_mtime = os.path.getmtime(SourceRepo._parse_script)

		for dir_name in os.listdir(self._repo):
			if dir_name.startswith("."):
				continue

			if os.path.exists(os.path.join(self._repo, dir_name, "EXCLUDE")):
				spkg = SourceRepo.ExcludedSrcPkg(self, dir_name)
				self._pkgs[spkg.name] = spkg
				continue

			pkgbuild = os.path.join(self._repo, dir_name, "PKGBUILD")
			if not os.path.exists(pkgbuild):
				print("ERROR: {0} not found".format(pkgbuild))
				continue

			cache = os.path.join(self._cache, slugify(dir_name))

			if not os.path.exists(cache):
				reread = True
			else:
				cache_mtime = os.path.getmtime(cache)

				if cache_mtime < parser_mtime:
					reread = True
				elif cache_mtime < os.path.getmtime(pkgbuild):
					reread = True
				else:
					reread = False

			if reread:
				pkg_json = SourceRepo.parse_pkgbuild(pkgbuild)
				with open(cache, "w") as fp:
					json.dump(pkg_json, fp)
			else:
				with open(cache, "r") as fp:
					pkg_json = json.load(fp)

			spkg = SourceRepo.SrcPkg(self, pkg_json)
			self._pkgs[spkg.name] = spkg

	def parse_pkgbuild(pkgbuild):
		json_str = bash(SourceRepo._parse_script, pkgbuild).stdout.decode('utf-8')
		return json.loads(json_str)

	def get_sourceball(self, name, ver):
		return None

	class ExcludedSrcPkg(SrcPkg):
		def __init__(self, repo, name):
			SrcPkg.__init__(self, repo, name, None)

		@property
		def excluded(self):
			return True

	class SrcPkg(SrcPkg):
		def __init__(self, repo, json):
			if "base" in json:
				name = json["base"]
			else:
				name = json["packages"][0]["name"]

			ver = json["ver"]
			rel = float(json["rel"])
			epoch = int(json["epoch"]) if "epoch" in json else None
			ver = PkgVersion(epoch, ver, rel)

			super().__init__(repo, name, ver)

			self._checkdeps = set([PkgDep(d) for d in json.get("checkdepends", [])])
			self._makedeps = set([PkgDep(d) for d in json.get("makedepends", [])])

			for pkg_json in json["packages"]:
				bpkg = SourceRepo.BinPkg(self, pkg_json)
				self._pkgs[bpkg.name] = bpkg

	class BinPkg(BinPkg):
		def __init__(self, src, json):
			super().__init__(src, json["name"], src.version)
			self._deps = set([PkgDep(d) for d in json.get("depends", [])])
			self._desc = json.get("desc", "")
			self._groups = set(json.get("groups", []))
