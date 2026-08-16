"""
Simple dynamic registry: discovers tool modules under tools/ and exposes them by key.
Each tool file should expose a callable `run()` and optional `TOOL_META` dict.
"""
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / 'tools'

_registry = {}


def _load_module_from_path(module_key, path):
    spec = importlib.util.spec_from_file_location(module_key, str(path))
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


def discover_and_register():
    """Scan tools/ for .py files (excluding __init__.py), load modules and register any with run()."""
    _registry.clear()
    if not TOOLS_DIR.exists():
        return _registry
    for py in TOOLS_DIR.rglob('*.py'):
        if py.name == '__init__.py':
            continue
        rel = py.relative_to(TOOLS_DIR)
        module_key = '.'.join(['tools'] + list(rel.with_suffix('').parts))
        mod = _load_module_from_path(module_key, py)
        if not mod:
            continue
        run_fn = getattr(mod, 'run', None)
        meta = getattr(mod, 'TOOL_META', {})
        if callable(run_fn):
            _registry[module_key] = {
                'module': mod,
                'run': run_fn,
                'meta': meta,
                'path': str(py)
            }
    return _registry


def list_tools():
    return {k: {**{'meta': v['meta'], 'path': v['path']}} for k, v in _registry.items()}


def get_tool(module_key):
    return _registry.get(module_key)
