try:
    from ._build_version import VERSION
except ImportError:
    VERSION = "dev"
