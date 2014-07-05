from binaryrepo import BinaryRepo
from config import Config
from destrepo import DestRepo
from gitsourcerepo import GitSourceRepo

class PkgGraph:
	class Pkg:
		def __init__(self, pkg_id):
			self._id = pkg_id
			self._spkgs = []
			self._dpkg = None

		@property
		def id(self):
			return self._id

		@property
		def current_build(self):
			return self._dpkg

		@property
		def source(self):
			if len(self._spkgs) == 0:
				return None
			return self._spkgs[-1]

		@property
		def built(self):
			return self._dpkg is not None

		@property
		def excluded(self):
			if len(self._spkgs) == 0:
				return False
			return self._spkgs[-1].excluded

		@property
		def removed(self):
			return len(self._spkgs) == 0

		@property
		def out_of_date(self):
			if len(self._spkgs) == 0:
				return False
			if self._spkgs[-1].excluded:
				return False
			if self._dpkg is None:
				return False
			return self._dpkg.version < self._spkgs[-1].version

		@property
		def up_to_date(self):
			if len(self._spkgs) == 0:
				return False
			if self._spkgs[-1].excluded:
				return False
			if self._dpkg is None:
				return False
			return self._dpkg.version >= self._spkgs[-1].version

		@property
		def source_outdated(self):
			if len(self._spkgs) < 2:
				return False
			if self._spkgs[-1].excluded:
				return False

			ver = self._spkgs[0].version
			for spkg in self._spkgs[1:]:
				if spkg.version < ver:
					return True
				ver = spkg.version

			return False

		@property
		def upstream_version(self):
			if len(self._spkgs) == 0:
				return None
			return self._spkgs[0].version

	class Repo:
		def __init__(self, graph, cfg):
			self._graph = graph
			self._name = cfg["name"]

			self._src = []
			for c in cfg["src"]:
				if "binary" in c:
					self._src.append(BinaryRepo(self._name, c["binary"]))
				elif "source-git" in c:
					self._src.append(GitSourceRepo(self._name, c["source-git"]))
				else:
					raise Exception("unknown repo type: {0}".format(c))

			self._dst = DestRepo(self._name, cfg["dst"], graph._arch)

			self.gen_lists()

		def refresh(self):
			for s in self._src:
				s.refresh()

			self._dst.refresh()
			self.gen_lists()

		def gen_lists(self):
			self._pkgs = {}

			for src in self._src:
				for spkg in src.packages:
					p = self._pkgs.get(spkg.name, None)
					if p is None:
						p = PkgGraph.Pkg(spkg.id)
						self._pkgs[spkg.name] = p

					p._spkgs.append(spkg)

			for dpkg in self._dst.packages:
				p = self._pkgs.get(dpkg.name, None)
				if p is None:
					p = PkgGraph.Pkg(dpkg.id)
					self._pkgs[dpkg.name] = p

				p._dpkg = dpkg

		@property
		def name(self):
			return self._name

		@property
		def packages(self):
			return self._pkgs.values()

		@property
		def out_of_date(self):
			return [ p for p in self._pkgs.values() if p.out_of_date ]

		@property
		def not_built(self):
			return [ p for p in self._pkgs.values() if not p.built ]

		@property
		def removed(self):
			return [ p for p in self._pkgs.values() if p.removed ]

		@property
		def up_to_date(self):
			return [ p for p in self._pkgs.values() if p.up_to_date ]

		@property
		def build_required(self):
			for p in self._pkgs.values():
				if (not p.built) or p.out_of_date:
					yield p

	def __init__(self, arch):
		self._arch = arch
		self.repos = [ PkgGraph.Repo(self, c) for c in Config.repos() ]
		self.gen_graph()

	@property
	def arch(self):
		return self._arch

	@property
	def packages(self):
		return self._pkgs.values()

	def refresh(self):
		for repo in self.repos:
			repo.refresh()
		self.gen_graph()

	def gen_graph(self):
		self._pkgs = {}

		for repo in self.repos:
			for pkg in repo.packages:
				self._pkgs[pkg.id] = pkg
