from smolagents import Tool
from core.events import EventWatcher

class WrappedTool(Tool):
    """
    A wrapper around the basic tool class that smolagents uses which is connected to an event watcher that logs what it 
    gets used for 
    """
    def __init__(self, wrapped_tool: Tool, watcher: EventWatcher):
        self._wrapped = wrapped_tool
        self._watcher = watcher

        self.name = wrapped_tool.name
        self.description = wrapped_tool.description
        self.inputs = wrapped_tool.inputs
        self.output_type = wrapped_tool.output_type

        self.skip_forward_signature_validation = True # this is for smolagents to not blow up when i try to make the
                                                      # forward functoin for this class take arbitrary args
        super().__init__()


    def forward(self, *args, **kwargs):
        """
        the exposed forward function so that smolagents knows how to use this (wrapped with the watcher so we can get
        the input/results out as well)
        """
        return self._watcher("tool", self.name, self._wrapped.forward, *args, **kwargs)

