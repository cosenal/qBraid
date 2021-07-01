"""Exceptions for errors raised while processing a device."""

from qbraid.exceptions import QbraidError


class DeviceError(QbraidError):
    """Base class for errors raised while processing a device."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)