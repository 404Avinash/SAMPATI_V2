"""
Compatibility shim: redirect all 'backend.app.*' imports to 'app.*'.

The original SAMPATI source was structured as backend/app/... and compiled
with that import path. This package makes the pyc files loadable from the
current repo layout where the backend/ wrapper is absent.
"""
import sys
import importlib
import importlib.abc
import importlib.machinery
import types


class _BackendRedirectFinder(importlib.abc.MetaPathFinder):
    """Maps backend.app.X -> app.X via find_spec (Python 3.4+ API)."""

    def find_spec(self, fullname, path, target=None):
        if fullname == "backend" or not fullname.startswith("backend."):
            return None
        real_name = fullname[len("backend."):]  # "backend.app.engine" -> "app.engine"
        try:
            real_spec = importlib.util.find_spec(real_name)
        except (ModuleNotFoundError, ValueError):
            return None
        if real_spec is None:
            return None
        # Return a spec that loads the real module and registers under both names
        return importlib.machinery.ModuleSpec(
            fullname,
            _AliasLoader(real_name),
            origin=real_spec.origin,
            is_package=real_spec.submodule_search_locations is not None,
        )


class _AliasLoader(importlib.abc.Loader):
    def __init__(self, real_name):
        self._real = real_name

    def create_module(self, spec):
        return None  # use default

    def exec_module(self, module):
        real = importlib.import_module(self._real)
        # Copy real module's namespace into alias module
        module.__dict__.update(real.__dict__)
        # Also register the real module under the alias name
        sys.modules[module.__name__] = real
        real.__name__ = real.__name__  # keep original name


import importlib.util

# Install once
if not any(isinstance(f, _BackendRedirectFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _BackendRedirectFinder())
