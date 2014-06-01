from clientcmd import ClientCmd
from daemoncmd import DaemonCmd

class ArchitectRefreshDaemon(DaemonCmd):
	cmd_name = "refresh"

	def run(self, req):
		self.graph.refresh()
		return {}

class ArchitectRefreshClient(ClientCmd):
	def setup_args(subparsers):
		parser = subparsers.add_parser("refresh", help="Refresh packages")
		parser.set_defaults(cmd=ArchitectRefreshClient)

	def run(self, args):
		reply = self.send({ "cmd" : ArchitectRefreshDaemon.cmd_name })

		if "error" in reply:
			print("Error: {0}".format(reply["error"]))
			return 1

		return 0
