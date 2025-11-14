class DefaultKwargs(dict):
    def __init__(self, ref: dict):
        super().__init__(ref)

    def __call__(self, other: dict) -> "DefaultKwargs":
        for k, v in self.items():
            if other.get(k) is None:
                other[k] = v

        return DefaultKwargs(other)
