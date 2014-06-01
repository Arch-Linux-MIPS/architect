import zmq

from cmd_loader import CmdLoader
from comm_base import CommBase
from config import Config
from db import DB
from pkggraph import PkgGraph

class Daemon(CommBase):
	def __init__(self):
		super().__init__()

		self._cmd_lookup = {}
		for cmd in CmdLoader.load("Daemon"):
			self._cmd_lookup[cmd.cmd_name] = cmd

		self._pkg_graph = { a: PkgGraph(a) for a in Config.architectures() }

		self._exit = False

	def do_connect(self):
		self._socket = self._zctx.socket(zmq.REP)
		self._socket.bind(Config.rpc_addr())

	def graph(self, arch):
		return self._pkg_graph.get(arch, None)

	def run(self):
		while not self._exit:
			msg = self.recv(timeout=0)

			print("Cmd: {0}".format({ k: msg.get(k, None) for k in ('cmd', 'arch') }))

			if not "arch" in msg:
				reply = { "error": "no arch specified" }
			else:
				pg = self.graph(msg["arch"])

				if pg is None:
					reply = { "error": "unsupported architecture" }
				elif not "cmd" in msg:
					reply = { "error": "no command specified" }
				elif not msg["cmd"] in self._cmd_lookup:
					reply = { "error": "unknown command" }
				else:
					try:
						reply = self._cmd_lookup[msg["cmd"]](self).invoke(pg, msg)
					except Exception as ex:
						reply = { "error": str(ex) }

			try:
				self.send(reply, response=False)
			except Exception as ex:
				print(ex)

		return 0
