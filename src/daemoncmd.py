class DaemonCmd:
	def __init__(self, daemon):
		self._daemon = daemon

	@property
	def daemon(self):
		return self._daemon

	@property
	def graph(self):
		return self._pkg_graph

	def invoke(self, pkg_graph, req):
		self._pkg_graph = pkg_graph
		return self.run(req)

	def run(self, req):
		raise Exception("run() not overridden")
