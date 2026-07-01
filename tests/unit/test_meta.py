"""
Unit tests for :py:mod:`nfl_stats._meta`.
"""

from nfl_stats._meta import MultitonMeta
from nfl_stats._meta import SingletonMeta

class Multiton(metaclass=MultitonMeta):
    """
    A test class that follows the multiton design pattern

    .. py:attribute:: counter

        A count of the number of times `__init__()` has been invoked
    """
    counter = 0

    def __init__(self, key: str):
        """
        :param key: The key to associate with the created instance of the multiton class
        """
        Multiton.counter += 1
        self._key = key

    @classmethod
    def __instance_key__(cls, key: str) -> str:
        return key

    @property
    def key(self) -> str:
        """
        The key associated with the given instance of the multiton class
        """
        return self._key

class Singleton(metaclass=SingletonMeta):
    """
    A test class that follows the singleton design pattern

    .. py:attribute:: counter

        A count of the number of times `__init__()` has been invoked
    """
    counter = 0

    def __init__(self):
        Singleton.counter += 1

class SingletonWithKey(metaclass=SingletonMeta):
    """
    A test class that follows a singleton design pattern

    .. py:attribute:: counter

        A count of the number of times `__init__()` has been invoked
    """
    counter = 0

    def __init__(self, key: str):
        """
        :param key: The (dummy) key to associated with the created instance of the singleton class
        """
        SingletonWithKey.counter += 1
        self._key = key

    @classmethod
    def __instance_key__(cls, key: str) -> str:
        return key

    @property
    def key(self) -> str:
        """
        The (dummy) key associated with the given instance of the singleton class
        """
        return self._key

def test_multiton_meta():
    """
    Unit tests for :py:class:`nfl_stats._meta.MultitonMeta`
    """
    assert Multiton.counter == 0, "Unexpected invocation of __init__()"

    a1 = Multiton("a")
    assert Multiton.counter == 1, (
        "Initial invocation of __call__() with a given key should invoke __init__()"
    )
    a2 = Multiton("a")
    assert Multiton.counter == 1, (
        "Additional invocations of __call__() with the same key should not invoke __init__()"
    )
    assert a1 == a2, (
        "Invocations of __call__() with the same key should return the same instance"
    )

    b1 = Multiton("b")
    assert Multiton.counter == 2, (
        "Initial invocation of __call__() with a given key should invoke __init__()"
    )
    b2 = Multiton("b")
    assert Multiton.counter == 2, (
        "Addition invocations of __call__() with the same key should not invoke __init__()"
    )
    assert b1 == b2, (
        "Invocations of __call__() with the same key should return the same instance"
    )

    c1 = Multiton("c")
    assert Multiton.counter == 3, (
        "Initial invocation of __call__() with a given key should invoke __init__()"
    )
    c2 = Multiton("c")
    assert Multiton.counter == 3, (
        "Additional invocations of __call__() with the same key should not invoke __init__()"
    )
    assert c1 == c2, (
        "Invocations of __call__() with the same key should return the same instance"
    )

def test_singleton_meta():
    """
    Unit tests for :py:class:`nfl_stats._meta.SingletonMeta`
    """
    assert Singleton.counter == 0, "Unexpected invocation of __init__()"
    a1 = Singleton()
    assert Singleton.counter == 1, "Initial invocation of __call__() should invoke __init__()"
    a2 = Singleton()
    assert Singleton.counter == 1, (
        "Additional invocations of __call__() should not invoke __init__()"
    )
    assert a1 == a2, "Invocations of __call__() should return the same instance"

    assert SingletonWithKey.counter == 0, "Unexpected invocation of __init__()"
    b1 = SingletonWithKey("b1")
    assert SingletonWithKey.counter == 1, (
        "Initial invocation of __call__() should invoke __init__()"
    )
    b2 = SingletonWithKey("b2")
    assert SingletonWithKey.counter == 1, (
        "Additional invocations of __call__() should not invoke __init__()"
    )
    assert b1 == b2, "Invocations of __call__() should return the same instance"
