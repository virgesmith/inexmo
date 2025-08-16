class X:
    @classmethod
    def class_method(cls: type) -> str:
        return cls.__name__
