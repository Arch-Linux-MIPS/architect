class PkgVersion:
	def __init__(self, epoch=None, ver="0", rel=0):
		self._epoch = epoch
		self._ver = ver
		self._rel = rel

	def __eq__(self, other):
		if self._epoch != other._epoch:
			return False
		if self._ver != other._ver:
			return False
		if self._rel != other._rel:
			return False
		return True

	def __gt__(self, other):
		sepoch = self._epoch if self._epoch is not None else 0
		oepoch = other._epoch if other._epoch is not None else 0
		if sepoch > oepoch:
			return True
		if sepoch < oepoch:
			return False

		if self._ver > other._ver:
			return True
		if self._ver < other._ver:
			return False

		if self._rel > other._rel:
			return True
		if self._rel < other._rel:
			return False

		# equal
		return False

	def __ge__(self, other):
		return self == other or self > other

	def __hash__(self):
		return hash((self._epoch, self._ver, self._rel))

	def __str__(self):
		s = self._ver

		if self._epoch is not None:
			s = "{0}:{1}".format(self._epoch, s)

		if self._rel is not None:
			s = "{0}-{1:g}".format(s, self._rel)

		return s

	@property
	def epoch(self):
		return self._epoch

	@property
	def ver(self):
		return self._ver

	@property
	def rel(self):
		return self._rel
	
	def parse(s):
		epoch = None
		ver = s
		rel = None

		if ":" in ver:
			(epoch, _dummy, ver) = ver.partition(":")
			epoch = int(epoch)

		if "-" in ver:
			(ver, _dummy, rel) = ver.partition("-")
			rel = float(rel)

		return PkgVersion(epoch, ver, rel)

class PkgDep:
	NO_VERSION = 0
	EQUAL = 1
	LESSER = 2,
	GREATER = 3,
	LESSER_EQUAL = 4
	GREATER_EQUAL = 5

	def __init__(self, str_dep):
		ver = None

		if ">=" in str_dep:
			( self.name, ver ) = str_dep.rsplit(">=", maxsplit=1)
			self.op = PkgDep.GREATER_EQUAL
		elif "<=" in str_dep:
			( self.name, ver ) = str_dep.rsplit("<=", maxsplit=1)
			self.op = PkgDep.LESSER_EQUAL
		elif ">" in str_dep:
			( self.name, ver ) = str_dep.rsplit(">", maxsplit=1)
			self.op = PkgDep.GREATER
		elif "<" in str_dep:
			( self.name, ver ) = str_dep.rsplit("<", maxsplit=1)
			self.op = PkgDep.LESSER
		elif "=" in str_dep:
			( self.name, ver ) = str_dep.rsplit("=", maxsplit=1)
			self.op = PkgDep.EQUAL
		else:
			self.name = str_dep
			self.op = PkgDep.NO_VERSION

		self._ver = PkgVersion.parse(ver) if ver is not None else None

	def __eq__(self, other):
		if self.name != other.name:
			return False
		if self.op != other.op:
			return False
		if self._ver != other._ver:
			return False
		return True

	def __hash__(self):
		return hash((self.name, self.op, self._ver))

	@property
	def version(self):
		return self._ver

class BinPkg:
	def __init__(self, src, name, ver, desc=""):
		self._deps = set()
		self._desc = desc
		self._groups = set()
		self._name = name
		self._optdeps = set()
		self._src = src
		self._ver = ver

	@property
	def depends(self):
		return self._deps

	@property
	def desc(self):
		return self._desc

	@property
	def groups(self):
		return self._groups

	@property
	def name(self):
		return self._name

	@property
	def optdepends(self):
		return self._optdeps

	@property
	def src(self):
		return self._src

	@property
	def version(self):
		return self._ver

class SrcPkg:
	def __init__(self, repo, name, ver):
		self._checkdeps = set()
		self._makedeps = set()
		self._name = name
		self._pkgs = {}
		self._repo = repo
		self._ver = ver

	@property
	def binaries(self):
		return self._pkgs.values()

	@property
	def checkdepends(self):
		return self._checkdeps

	@property
	def id(self):
		return "{0}/{1}".format(self._repo.name, self._name)

	@property
	def makedepends(self):
		return self._makedeps

	@property
	def name(self):
		return self._name

	@property
	def version(self):
		return self._ver

	@property
	def excluded(self):
		return False

class Repo:
	def __init__(self, name):
		self._name = name
		self._pkgs = {}

	@property
	def name(self):
		return self._name

	@property
	def packages(self, want_dict=False):
		if want_dict:
			return self._pkgs
		return self._pkgs.values()

	def refresh(self):
		raise Exception()
