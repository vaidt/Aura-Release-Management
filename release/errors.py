"""Errors shared by the RM-0 command-line interfaces."""


class RMError(Exception):
    """Base class for expected release-management failures."""


class VerificationError(RMError):
    """A release or verification gate failed."""


class RefusalError(RMError):
    """The requested operation lacks required control-plane inputs."""
