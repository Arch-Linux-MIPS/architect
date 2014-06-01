import zmq

from comm_base import CommBase
from config import Config

class ClientCmd(CommBase):
	def do_connect(self):
		self._socket = self._zctx.socket(zmq.REQ)
		self._socket.setsockopt(zmq.LINGER, 0)
		self._socket.connect(Config.rpc_addr())

	def send(self, obj, response=True):
		obj["arch"] = Config.architectures()[0]
		return super().send(obj, response=response)
