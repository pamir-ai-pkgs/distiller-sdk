import os

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("distiller-sdk")
except PackageNotFoundError:
    __version__ = "dev"


def get_library_path():
    """
    Get the correct library path for native libraries.

    Returns:
        str: Path to the library directory
    """
    # First check if we're in a Debian package installation
    debian_path = "/opt/distiller-sdk/lib"
    if os.path.exists(debian_path):
        return debian_path

    # Fall back to relative path for development
    return os.path.join(os.path.dirname(__file__), "hardware", "eink", "lib")
