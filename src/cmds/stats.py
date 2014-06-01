import argparse
import json

from enum import Enum

from clientcmd import ClientCmd
from daemoncmd import DaemonCmd
from db import DB

class Stats(Enum):
	recent_builds = 1

class StatsFormat(Enum):
	json = 1
	html = 2

class ArchitectStatsDaemon(DaemonCmd):
	cmd_name = "stats"

	def __init__(self, daemon):
		super().__init__(daemon)

		self._handlers = {
			Stats.recent_builds: ArchitectStatsDaemon.handle_recent_builds,
		}

	def handle_recent_builds(self, req):
		show_all = "all" in req and req["all"]

		return { "builds": DB.recent_builds(req["count"], show_all=show_all) }

	def run(self, req):
		stat = Stats[req["stat"]]

		if not stat in self._handlers:
			return { "error": "Unknown stat" }

		return self._handlers[stat](self, req)

class ArchitectStatsClient(ClientCmd):
	def __init__(self):
		super().__init__()

		self._text_printers = {
			Stats.recent_builds: ArchitectStatsClient.print_recent_builds,
		}

	def setup_args(subparsers):
		parser = subparsers.add_parser("stats", help="Output statistics")
		parser.set_defaults(cmd=ArchitectStatsClient)

		subparsers = parser.add_subparsers(title="stat")

		parser = subparsers.add_parser("recent-builds", help="Recently build packages")
		parser.set_defaults(stat=Stats.recent_builds)
		parser.add_argument("--count", type=int, default=10,
				    help="The number of packages to list")
		parser.add_argument("--json", action='store_true', help="Output as JSON")

	def run(self, args):
		if not "stat" in args:
			print("No stat specified")
			return 1

		req = {
			"cmd" : ArchitectStatsDaemon.cmd_name,
			"stat": args.stat.name,
		}

		if args.stat == Stats.recent_builds:
			req["count"] = args.count

		reply = self.send(req)

		if "error" in reply:
			print("Error: {0}".format(reply["error"]))
			return 1

		if "json" in args and args.json:
			print(json.dumps(reply, indent=4))
			return 0

		if not args.stat in self._text_printers:
			print("No text printer for stat")
			return 1

		self._text_printers[args.stat](self, reply)
		return 0

	def print_recent_builds(self, json):
		for build in json["builds"]:
			print("{0} {1}".format(build["pkg"], build["version"]))
