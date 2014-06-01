import argparse

from enum import Enum

from clientcmd import ClientCmd
from daemon import Daemon
from daemoncmd import DaemonCmd

class Cmd(Enum):
	start = 1
	stop = 2

class ArchitectDaemonDaemon(DaemonCmd):
	cmd_name = "daemon"

	def run(self, req):
		cmd = Cmd[req["daemon-cmd"]]

		if cmd == Cmd.stop:
			self.daemon._exit = True
			return {}

		return { "error": "Unknown cmd {0}".format(cmd) }

class ArchitectDaemonClient(ClientCmd):

	def setup_args(subparsers):
		parser = subparsers.add_parser("daemon", help="Control the architect daemon")
		parser.set_defaults(cmd=ArchitectDaemonClient)

		subparsers = parser.add_subparsers(title="daemon-cmd")

		parser = subparsers.add_parser("start", help="Start the daemon")
		parser.set_defaults(dcmd=Cmd.start)

		parser = subparsers.add_parser("stop", help="Stop the daemon")
		parser.set_defaults(dcmd=Cmd.stop)

	def run(self, args):
		if not "dcmd" in args:
			print("No command specified")
			return 1

		if args.dcmd == Cmd.start:
			# This is handled a little differently to other commands
			# since it's not communicating with the daemon - instead
			# this process will be the daemon
			return Daemon().run()

		if args.dcmd == Cmd.stop:
			ret = self.send({
				"cmd": ArchitectDaemonDaemon.cmd_name,
				"daemon-cmd": Cmd.stop.name,
			})
			return not "error" in ret

		print("Unknown command {0}".format(args.dcmd))
		return 1
