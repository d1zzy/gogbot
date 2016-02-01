import importlib

# Plugins package.
_PACKAGE = 'plugins'

# Map of plugin name -> imported python module object for that plugin.
_PLUGINS = {}

def GetPlugin(name):
    module = _PLUGINS.get(name, None)
    if module is None:
        module = importlib.import_module('%s.%s' % (_PACKAGE, name))
        if not getattr(module, 'Handler'):
            raise Exeption('plugin "%s" missing "Handler" class' % name)
        _PLUGINS[name] = module
    return module
