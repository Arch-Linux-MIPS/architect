class CmdLoader:
	_list = [
		"daemon",
		"dump",
		"refresh",
		"stats",
	]

	def load(suffix):
		for name in CmdLoader._list:
			camel = name[0:1].upper() + name[1:]
			class_name = "Architect{0}{1}".format(camel, suffix)
			mod = __import__(
				"cmds.{0}".format(name),
				fromlist=[ class_name ]
			)
			yield getattr(mod, class_name)
