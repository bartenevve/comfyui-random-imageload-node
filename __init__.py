from .nodes import LoadRandomImage
from . import routes  # noqa: F401  registers the aiohttp routes on import

NODE_CLASS_MAPPINGS = {
    "LoadRandomImage": LoadRandomImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadRandomImage": "Load Random Image \U0001f3b2",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
