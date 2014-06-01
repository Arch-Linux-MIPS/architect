import argparse
import json
import re

from clientcmd import ClientCmd
from daemoncmd import DaemonCmd
from config import Config

class ArchitectDumpDaemon(DaemonCmd):
	cmd_name = "dump"

	def run(self, req):
		pkgs = []
		prog = re.compile(req["pattern"])

		for pkg in self.graph.packages:
			if prog.search(pkg.id) is not None:
				pkgs.append(pkg)

		pi = []
		for pkg in pkgs:
			spkg = pkg.source
			if spkg is None:
				spkg = pkg.current_build

			si = {
				"checkdeps": [ d.name for d in spkg.checkdepends ],
				"id": spkg.id,
				"makedeps": [ d.name for d in spkg.makedepends ],
				"name": spkg.name,
				"version": str(spkg.version),
			}

			if pkg.excluded or pkg.removed:
				del si["version"]

			bpkg = pkg.current_build
			if bpkg is not None:
				si["version-built"] = str(bpkg.version)

			si["status"] = []

			if pkg.excluded:
				si["status"].append("excluded")
			elif not pkg.built:
				si["status"].append("not-built")
			elif pkg.removed:
				si["status"].append("removed")
			elif pkg.up_to_date:
				si["status"].append("up-to-date")
			elif pkg.out_of_date:
				si["status"].append("out-of-date")
			else:
				si["status"].append("error-unknown")

			if pkg.source_outdated:
				si["status"].append("source-outdated")
				si["version-upstream"] = str(pkg.upstream_version)

			bins = []
			for bpkg in spkg.binaries:
				bi = {
					"deps": [ d.name for d in bpkg.depends ],
					"desc": bpkg.desc,
					"groups": [ g for g in bpkg.groups ],
					"name": bpkg.name,
				}
				bins.append(bi)

			si["binaries"] = bins
			pi.append(si)

		return { "pkgs": pi }

class ArchitectDumpClient(ClientCmd):
	def setup_args(subparsers):
		parser = subparsers.add_parser("dump", help="Dump package information")
		parser.set_defaults(cmd=ArchitectDumpClient)
		parser.add_argument("--json", action='store_true', help="Output as JSON")
		parser.add_argument("pattern", type=str, help="The pattern to match package IDs against")

	def run(self, args):
		reply = self.send({
			"cmd" : ArchitectDumpDaemon.cmd_name,
			"pattern": args.pattern,
		})

		if "error" in reply:
			print("Error: {0}".format(reply["error"]))
			return 1

		if "json" in args and args.json:
			print(json.dumps(reply, indent=4))
			return 0

		first = True
		for spkg in reply["pkgs"]:
			if not first:
				print("")

			self.print_spkg(spkg)
			first = False

		if first:
			print("No matching package found")

		return 0

	def print_spkg(self, spkg):
		print("{0}:".format(spkg["id"]))

		print("  Name:               {0}".format(spkg["name"]))
		if "version-upstream" in spkg:
			print("  Upstream Version:   {0}".format(spkg["version-upstream"]))
		if "version" in spkg:
			print("  Current Version:    {0}".format(spkg["version"]))
		if "version-built" in spkg:
			print("  Built Version:      {0}".format(spkg["version-built"]))
		print("  Status:             {0}".format(",".join(spkg["status"])))

		if len(spkg["makedeps"]) > 0:
			print("  Make Dependencies:  {0}".format(", ".join(spkg["makedeps"])))
		if len(spkg["checkdeps"]) > 0:
			print("  Check Dependencies: {0}".format(", ".join(spkg["checkdeps"])))

		if len(spkg["binaries"]) > 0:
			print("  Binaries:")

			first = True
			for bpkg in spkg["binaries"]:
				if not first:
					print("")

				self.print_bpkg(bpkg)
				first = False

	def print_bpkg(self, bpkg):
		print("    Name:             {0}".format(bpkg["name"]))
		print("    Description:      {0}".format(bpkg["desc"]))

		if len(bpkg["groups"]) > 0:
			print("    Groups:           {0}".format(", ".join(bpkg["groups"])))

		if len(bpkg["deps"]) > 0:
			print("    Dependencies:     {0}".format(", ".join(bpkg["deps"])))
