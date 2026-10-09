"""Type-restricted unpickler with basic module allowlisting.
NOTE: Python pickle deserialization is fundamentally not safe against malicious data.
This restriction serves only as basic defense-in-depth against accidental arbitrary execution.
Always treat untrusted pickle files with caution.
"""

import io
import pickle
from typing import Any, Set, Tuple


class PickleSecurityError(Exception):
    """Raised when an unlisted class or module is encountered during unpickling."""

    def __init__(self, module: str, name: str):
        super().__init__(
            f"Blocked unlisted module/class in pickle: '{module}.{name}'. "
            "Only common standard library, NumPy, and Pandas data types are allowed."
        )
        self.module = module
        self.name = name


# Default whitelist of safe standard modules and types
SAFE_MODULES: Set[str] = {
    "builtins",
    "_codecs",
    "collections",
    "datetime",
    "decimal",
    "fractions",
    "uuid",
    "math",
    "pathlib",
}

SAFE_BUILTINS: Set[str] = {
    "int",
    "float",
    "complex",
    "str",
    "bytes",
    "bytearray",
    "bool",
    "list",
    "dict",
    "set",
    "frozenset",
    "tuple",
    "slice",
    "range",
    "NoneType",
    "Ellipsis",
    "True",
    "False",
}

SAFE_NUMPY_MODULES: Set[str] = {
    "numpy",
    "numpy.core.multiarray",
    "numpy._core.multiarray",
    "numpy.core.numeric",
    "numpy._core.numeric",
    "numpy.dtypes",
    "numpy._core.dtypes",
}

SAFE_PANDAS_PREFIXES: Tuple[str, ...] = (
    "pandas.core",
    "pandas._libs",
    "pandas",
)

SAFE_PYARROW_MODULES: Set[str] = {
    "pyarrow",
    "pyarrow.lib",
}


class SafeUnpickler(pickle.Unpickler):
    """Unpickler that restricts class resolution strictly to a known safe whitelist."""

    def __init__(self, *args, allow_numpy: bool = True, allow_pandas: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_numpy = allow_numpy
        self.allow_pandas = allow_pandas

    def find_class(self, module: str, name: str) -> Any:
        # Check standard builtins
        if module == "builtins":
            if name in SAFE_BUILTINS:
                return getattr(__import__(module), name)
            raise PickleSecurityError(module, name)

        if module in ("_codecs", "codecs") and name in ("encode", "decode"):
            # Allowed for some string/bytes decoding in pickle
            import _codecs
            return getattr(_codecs, name)

        if module == "datetime":
            import datetime
            if hasattr(datetime, name):
                return getattr(datetime, name)
            raise PickleSecurityError(module, name)

        if module == "collections":
            import collections
            if name in ("OrderedDict", "defaultdict", "deque", "Counter"):
                return getattr(collections, name)
            raise PickleSecurityError(module, name)

        if module == "decimal" and name == "Decimal":
            import decimal
            return decimal.Decimal

        if module == "uuid" and name == "UUID":
            import uuid
            return uuid.UUID

        if module == "pathlib":
            import pathlib
            if name in ("Path", "PurePath", "PosixPath", "WindowsPath", "PurePosixPath", "PureWindowsPath"):
                return getattr(pathlib, name)
            raise PickleSecurityError(module, name)

        # Check NumPy
        if self.allow_numpy:
            if module in SAFE_NUMPY_MODULES or module.startswith("numpy."):
                # Disallow arbitrary execution from numpy (e.g. numpy.testing)
                if not module.startswith(("numpy.testing", "numpy.distutils", "numpy.f2py")):
                    try:
                        mod = __import__(module, fromlist=[name])
                        return getattr(mod, name)
                    except (ImportError, AttributeError):
                        pass

        # Check Pandas
        if self.allow_pandas:
            if any(module == prefix or module.startswith(prefix + ".") for prefix in SAFE_PANDAS_PREFIXES):
                if not module.startswith(("pandas.testing", "pandas.io.clipboard")):
                    try:
                        mod = __import__(module, fromlist=[name])
                        return getattr(mod, name)
                    except (ImportError, AttributeError):
                        pass

        # Check PyArrow
        if module in SAFE_PYARROW_MODULES or module.startswith("pyarrow."):
            if not module.startswith(("pyarrow.jvm", "pyarrow.flight", "pyarrow.substrait")):
                try:
                    mod = __import__(module, fromlist=[name])
                    return getattr(mod, name)
                except (ImportError, AttributeError):
                    pass

        # Deny all other modules (e.g. os, subprocess, posix, nt, sys, __main__, etc.)
        raise PickleSecurityError(module, name)


def safe_load_pickle(data: bytes | io.BytesIO, allow_numpy: bool = True, allow_pandas: bool = True) -> Any:
    """Safely load pickle data ensuring only whitelisted classes can be instantiated.

    Args:
        data: Raw bytes or BytesIO stream of pickle content.
        allow_numpy: Whether to allow safe NumPy data types.
        allow_pandas: Whether to allow safe Pandas data types.

    Returns:
        The deserialized Python object.

    Raises:
        PickleSecurityError: If an unauthorized class is encountered.
        pickle.UnpicklingError: If pickle data is invalid.
    """
    stream = io.BytesIO(data) if isinstance(data, bytes) else data
    unpickler = SafeUnpickler(stream, allow_numpy=allow_numpy, allow_pandas=allow_pandas)
    return unpickler.load()
