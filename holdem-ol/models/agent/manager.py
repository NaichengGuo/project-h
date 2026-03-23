import importlib


class AgentSpec(object):

    def __init__(self, agent_name, entry_point=None):
        self._entry_point = None
        self.agent_name = agent_name
        self.entry_point_name = entry_point

    def make(self, config=None):
        if self._entry_point is None:
            mod_name, class_name = self.entry_point_name.split(':')
            self._entry_point = getattr(importlib.import_module(mod_name), class_name)
        env = self._entry_point(config)
        return env


class AgentRegistry(object):

    def __init__(self):

        self.agent_specs = {}

    def register(self, agent_name, entry_point):
        if agent_name in self.agent_specs:
            raise ValueError('Cannot re-register agent_name: {}'.format(agent_name))
        self.agent_specs[agent_name] = AgentSpec(agent_name, entry_point)

    def make(self, agent_name, config=None):
        #print(f'check agent_specs:{self.agent_specs}')
        if agent_name not in self.agent_specs:
            raise ValueError('Cannot find agent_name: {}'.format(agent_name))
        return self.agent_specs[agent_name].make(config)


# Have a global registry
_registry = AgentRegistry()


def register_agent(agent_name, entry_point):
    return _registry.register(agent_name, entry_point)


def make_agent(agent_name, config=None):
    return _registry.make(agent_name, config)
