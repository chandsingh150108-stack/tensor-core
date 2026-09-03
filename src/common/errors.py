class UnsupportedFormatError(Exception):
    """Raised when a file format cannot be dispatched by the loader."""


class CorruptImageError(Exception):
    """Raised when an image binary body is corrupted or truncated."""


class FileNotFoundError(Exception):
    """Raised when a companion label file is missing."""
