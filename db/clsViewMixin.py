class clsViewMixin:
    """Interdit CUD — à mixin sur toute classe entité-vue."""

    def insert(self):
        raise PermissionError(f"{self.__class__.__name__} est une vue — lecture seule.")

    def update(self):
        raise PermissionError(f"{self.__class__.__name__} est une vue — lecture seule.")

    def delete(self):
        raise PermissionError(f"{self.__class__.__name__} est une vue — lecture seule.")
