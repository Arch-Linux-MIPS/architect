import argparse
import base64
import json
import os
import rethinkdb
import shutil
import sys
import tarfile
import tempfile

from enum import Enum

from sh import gpg

from clientcmd import ClientCmd
from daemoncmd import DaemonCmd
from config import Config
from db import DB

class Cmd(Enum):
	ready = 1
	receive = 2
	source = 3

class ArchitectBuildDaemon(DaemonCmd):
	cmd_name = "build"

	def __init__(self, daemon):
		super().__init__(daemon)

		self._handlers = {
			Cmd.ready: ArchitectBuildDaemon.handle_ready,
			Cmd.receive: ArchitectBuildDaemon.handle_receive,
			Cmd.source: ArchitectBuildDaemon.handle_source,
		}

	def handle_ready(self, req):
		return {
			"pkgs": [{
				"id": p.id,
				"version": str(p.source.version),
			} for p in self._pkg_graph.ready_for_build() ],
		}

	def handle_receive(self, req):
		repo = None
		for r in self._pkg_graph.repos:
			if r.name == req["repository"]:
				repo = r
				break

		if repo is None:
			return { "error": "Unknown repository '{0}'".format(req["repository"]) }

		try:
			repo._dst.add_packages(req["packages"], tmp_dir=req["dir"])
		except Exception as e:
			return { "error": "Exception: {0}".format(str(e)) }

		try:
			db_result = DB.insert_build({
				"arch": self._pkg_graph.arch,
				"pkg": req["pkg"],
				"version": req["version"],
				"status": "success",
				"time_upload": rethinkdb.now(),
			})
			build_id = db_result["generated_keys"][0]
		except Exception as e:
			return { "error": "Failed DB insert: {0}".format(repr(e)) }

		try:
			log_dir_name = "{0}-{1}-{2}".format(
				req["pkg"].replace("/", "-"),
				req["version"],
				build_id
			)
			log_dir = os.path.join(Config.build_logs(), log_dir_name)
			os.mkdir(log_dir)

			for src_path in req["logs"]:
				dst_path = os.path.join(log_dir, os.path.basename(src_path))
				shutil.copyfile(src_path, dst_path)
		except Exception as e:
			return { "error": "Failed to copy logs: {0}".format(str(e)) }

		return {}

	def handle_source(self, req):
		( repo_name, _dummy, name ) = req["pkg"].partition("/")

		repo = None
		for r in self._pkg_graph.repos:
			if r.name == repo_name:
				repo = r
				break

		if repo is None:
			return { "error": "Unknown repository '{0}'".format(repo_name) }

		if name not in repo._pkgs:
			return { "error": "Unknown package '{0}'".format(name) }

		src = repo._pkgs[name].source
		if src is None:
			return { "error": "404" }

		srcball = src.get_sourceball()
		if src is None:
			return { "error": "404" }

		return {
			"srcball": base64.b64encode(srcball.getbuffer()).decode("utf-8"),
		}

	def run(self, req):
		stat = Cmd[req["bcmd"]]

		if not stat in self._handlers:
			return { "error": "Unknown subcommand" }

		return self._handlers[stat](self, req)

class ArchitectBuildClient(ClientCmd):
	def __init__(self):
		super().__init__()

		self._handlers = {
			Cmd.ready: ArchitectBuildClient.handle_ready,
			Cmd.receive: ArchitectBuildClient.handle_receive,
			Cmd.source: ArchitectBuildClient.handle_source,
		}

	def setup_args(subparsers):
		parser = subparsers.add_parser("build", help="Package build commands")
		parser.set_defaults(cmd=ArchitectBuildClient)

		subparsers = parser.add_subparsers(title="build-cmd")

		parser = subparsers.add_parser("ready", help="Determine packages ready for building")
		parser.set_defaults(bcmd=Cmd.ready)
		parser.add_argument("--json", action='store_true', help="Output as JSON")

		parser = subparsers.add_parser("receive", help="Receive a completed build")
		parser.set_defaults(bcmd=Cmd.receive)
		parser.add_argument("repository", type=str, help="Destination repository")
		parser.add_argument("source", type=str, help="Source package name")
		parser.add_argument("version", type=str, help="Package version")

		parser = subparsers.add_parser("source", help="Retrieve package source")
		parser.set_defaults(bcmd=Cmd.source)
		parser.add_argument("package", type=str, help="Package ID")
		parser.add_argument("version", type=str, help="Package version")

	def run(self, args):
		if not "bcmd" in args:
			print("No build-cmd specified")
			return 1

		if not args.bcmd in self._handlers:
			print("Unhandled subcommand")
			return 1

		return self._handlers[args.bcmd](self, args)

	def verify_sig(self, path, sig):
		try:
			gpg("--batch", "--no-tty", "--verify", sig, path)
			return True
		except:
			return False

	def handle_ready(self, args):
		reply = self.send({
			"cmd" : ArchitectBuildDaemon.cmd_name,
			"bcmd": args.bcmd.name,
		})

		if "error" in reply:
			print("Error: {0}".format(reply["error"]))
			return 1

		if "json" in args and args.json:
			print(json.dumps(reply, indent=4))
			return 0

		for pkg in reply["pkgs"]:
			print("{0} {1}".format(pkg["id"], pkg["version"]))

		return 0

	def handle_receive(self, args):
		with tempfile.TemporaryDirectory() as tmp_dir:
			with tarfile.open(fileobj=sys.stdin.buffer, mode="r|") as tar:
				tar.extractall(path=tmp_dir)

			packages = []
			logs = []

			for fname in os.listdir(tmp_dir):
				fpath = os.path.join(tmp_dir, fname)

				if not os.path.isfile(fpath):
					return { "error": "received non-file" }

				if fname.endswith(".pkg.tar.xz"):
					sigpath = "{0}.sig".format(fpath)
					if not self.verify_sig(fpath, sigpath):
						return { "error": "signature verification failed" }

					packages.append(fpath)
					continue

				if fname.endswith(".pkg.tar.xz.sig"):
					continue

				if fname.endswith(".log"):
					logs.append(fpath)
					continue

				return { "error": "unhandled file '{0}'".format(fpath) }

			reply = self.send({
				"cmd" : ArchitectBuildDaemon.cmd_name,
				"bcmd": args.bcmd.name,
				"repository": args.repository,
				"pkg": "{0}/{1}".format(args.repository, args.source),
				"version": args.version,
				"dir": tmp_dir,
				"packages": packages,
				"logs": logs,
			})

			if "error" in reply:
				print("Error: {0}".format(reply["error"]))
				return 1

		return 0

	def handle_source(self, args):
		reply = self.send({
			"cmd" : ArchitectBuildDaemon.cmd_name,
			"bcmd": args.bcmd.name,
			"pkg": args.package,
			"version": args.version,
		})

		if "error" in reply:
			print("Error: {0}".format(reply["error"]))
			return 1

		print(reply["srcball"])
		return 0
