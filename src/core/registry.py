from typing import Dict, Callable, TypeVar, Generic, List

T = TypeVar("T")

class Registry(Generic[T]): 
    """
    Class made for ease of building predefined instances of things like our tools or agentic setups
    (see the implementation in action in a tool definitions file or in agents/definitions to understand how to use it)

    """

    def __init__(self, kind: str):
        self._kind = kind
        self._entries:  Dict[str, Callable[..., T]] = {}

    def register(self, name: str):
        """
        this can be called either as a decorator or with another function wrapped around it to basically register a
        single string and how to build the object we want associated with it easily 
        Args: 
            name (str): string associated with the object type that will be built
        """
        def _decorator(factory: Callable[..., T]) -> Callable[..., T]:
            if name in self._entries:
                raise ValueError(f"{self._kind}: '{name}' is already registered")
            self._entries[name] = factory
            return factory
        return _decorator

    def get(self, name:str) -> Callable[..., T]:
        """
        Returns the factory function needed to build the instance of the object associate diwth this type (probably
        shouldnt be called directly)

        Args:
            name (str): the name associated with the object instance / type being built

        Returns (Callable[..., t]): the function needed to build the class / type associated with this registry entry
        """
        if name not in self._entries:
            raise KeyError(f"Unknown {self._kind} '{name}' not in registered: {sorted(self._entries)}")
        return self._entries[name]

    def create(self, name: str, /, **kwargs) -> T:
        """
        Creates the object associated with this type by calling get along with passed kwargs to the factory function

        Args:
            name (str): name associated with the object instance / type being built
            kwargs (dict): keyword arguments to be passed into the factory function that builds the type instance

        Returns (T): The instance of 

        """
        return self.get(name)(**kwargs)

    def names(self) -> List[str]:
        """
        lists the registered strings that map to factory functions in this registry

        Returns (List[str]): the sorted list containing the strings that have been saved inthis registry
        """
        return sorted(self._entries)
