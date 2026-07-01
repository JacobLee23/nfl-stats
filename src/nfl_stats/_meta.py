"""
Metaclass definitions.
"""

class MultitonMeta(type):
    """
    Metaclass definition for multiton design pattern.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        key = cls.__instance_key__(*args, **kwargs)
        if (cls, key) not in cls._instances:
            cls._instances[(cls, key)] = super().__call__(*args, **kwargs)
        return cls._instances[(cls, key)]

    def __instance_key__(cls, *args, **kwargs):
        raise NotImplementedError

class SingletonMeta(MultitonMeta):
    """
    Metaclass definition for singleton design pattern.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    def __instance_key__(cls, *args, **kwargs):
        return None
