class CollectionUtil(object):
    @staticmethod
    def sub(a, b):
        return list(set(a) - set(b))


class DDict(object):
    def to_dict(self):
        """
        Returns: dict
        """
        # convert all attributes to dict
        return self.__dict__

    def update(self, **kwargs):
        """
        Update attributes
        Args:
            **kwargs: attributes
        """
        self.__dict__.update(kwargs)
        return self
