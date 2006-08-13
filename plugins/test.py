import plugin

def plugin_test(identity):
	identity.send("test received")

plugin.register("!test",plugin_test)
