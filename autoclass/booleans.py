from abc import abstractmethod, ABCMeta


class Boolean(metaclass=ABCMeta):
    """
    An abstract base class for booleans, similar to what is available in numbers
    see https://docs.python.org/3.5/library/numbers.html
    """
    __slots__ = ()

    @abstractmethod
    def __bool__(self):
        """Return a builtin bool instance. Called for bool(self)."""

    @abstractmethod
    def __and__(self, other):
        """self & other"""

    @abstractmethod
    def __rand__(self, other):
        """other & self"""

    @abstractmethod
    def __xor__(self, other):
        """self ^ other"""

    @abstractmethod
    def __rxor__(self, other):
        """other ^ self"""

    @abstractmethod
    def __or__(self, other):
        """self | other"""

    @abstractmethod
    def __ror__(self, other):
        """other | self"""

    @abstractmethod
    def __invert__(self):
        """~self"""

# register bool and numpy bool_ as virtual subclasses
# so that issubclass(bool, Boolean) = issubclass(np.bool_, Boolean) = True
Boolean.register(bool)

try:
    import numpy as np
    Boolean.register(np.bool_)
except ImportError:
    # silently escape
    pass
