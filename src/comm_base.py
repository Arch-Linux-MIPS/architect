from datetime import datetime

import zmq

class CommBase:
	def __init__(self):
		self._socket = None
		self._zctx = zmq.Context()

	def connect(self):
		if self._socket is not None:
			return

		self.do_connect()

	def json_serialisable(obj):
		if isinstance(obj, datetime):
			return obj.isoformat()

		raise Exception("Unable to serialise object {0}".format(repr(obj)))

	def send(self, obj, response=True):
		self.connect()
		self._socket.send_json(obj, default=CommBase.json_serialisable)
		if response:
			return self.recv()

	def recv(self, timeout=30000):
		self.connect()
		if timeout != 0:
			poller = zmq.Poller()
			poller.register(self._socket, zmq.POLLIN)

			if not poller.poll(timeout):
				return { "error": "Receive Timeout" }

		return self._socket.recv_json()
