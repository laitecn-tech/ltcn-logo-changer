"""Isolate the known legacy favicon hooks without changing user configuration."""

from __future__ import annotations

from dataclasses import dataclass
import dis
import inspect
import logging
import sys
from types import CodeType, FunctionType, ModuleType
from typing import Any

from homeassistant.components import frontend

_LOGGER = logging.getLogger(__name__)
_LEGACY_MODULE = "custom_components.favicon"
_ISOLATION_ATTRIBUTE = "_ltcn_logo_changer_isolation"


class LegacyConflictError(RuntimeError):
    """An unrecognized branding hook must be removed before taking ownership."""


@dataclass(frozen=True)
class _Isolation:
    hass: Any
    apply_hooks: FunctionType
    remove_hooks: FunctionType


def _known_remove_hooks(hass):
    """Reference implementation of the verified legacy removal operation."""
    data = hass.data[DOMAIN]
    frontend.IndexView.get_template = data["get_template"]
    frontend.add_manifest_json_key("icons", data["manifest_icons"].copy())
    frontend.add_manifest_json_key("name", "Home Assistant")
    frontend.add_manifest_json_key("short_name", "Assistant")
    return True


# Used only by the reference code above. Its code is compared, never executed.
DOMAIN = "favicon"


def _code_shape(code: CodeType) -> tuple:
    """Compare executable structure while ignoring paths and source line numbers."""
    instructions = tuple(
        (
            instruction.opname,
            _code_shape(instruction.argval)
            if isinstance(instruction.argval, CodeType)
            else instruction.argval,
        )
        for instruction in dis.get_instructions(code)
        # Python can emit PUSH_NULL separately for known imported modules.
        # LOAD_ATTR's resolved argval already removes its equivalent flag.
        if instruction.opname not in {"RESUME", "CACHE", "PUSH_NULL", "NOP"}
    )
    return (
        code.co_argcount,
        code.co_posonlyargcount,
        code.co_kwonlyargcount,
        code.co_varnames,
        code.co_freevars,
        code.co_cellvars,
        instructions,
    )


async def _blocked_apply_hooks(hass):
    """Keep later legacy options updates from reclaiming the frontend."""
    return True


def _blocked_remove_hooks(hass):
    """Keep deleting a legacy entry from removing the new branding."""
    return True


def _legacy_function(value: Any, name: str) -> bool:
    return (
        isinstance(value, FunctionType)
        and value.__module__ == _LEGACY_MODULE
        and value.__name__ == name
    )


def _validate_legacy(module: ModuleType, hass: Any) -> None:
    """Fail closed if another integration or an unknown favicon version owns it."""
    data = hass.data.get(DOMAIN)
    if not isinstance(data, dict):
        raise LegacyConflictError("Legacy favicon state is not recognized")
    apply_hooks = getattr(module, "apply_hooks", None)
    remove_hooks = getattr(module, "remove_hooks", None)
    if (
        not _legacy_function(apply_hooks, "apply_hooks")
        or not inspect.iscoroutinefunction(apply_hooks)
        or apply_hooks.__globals__ is not module.__dict__
        or not _legacy_function(remove_hooks, "remove_hooks")
        or remove_hooks.__globals__ is not module.__dict__
        or _code_shape(remove_hooks.__code__)
        != _code_shape(_known_remove_hooks.__code__)
        or remove_hooks.__globals__.get("frontend") is not frontend
        or remove_hooks.__globals__.get("DOMAIN") != DOMAIN
    ):
        raise LegacyConflictError("Legacy favicon hooks are not recognized")

    baseline = data.get("get_template")
    if (
        not isinstance(baseline, FunctionType)
        or baseline.__module__ != frontend.__name__
        or baseline.__qualname__ != "IndexView.get_template"
        or baseline.__globals__ is not frontend.__dict__
        or not isinstance(data.get("manifest_icons"), list)
    ):
        raise LegacyConflictError("Legacy favicon has no safe native baseline")

    current = frontend.IndexView.get_template
    if current is baseline:
        return
    if (
        not isinstance(current, FunctionType)
        or current.__module__ != _LEGACY_MODULE
        or current.__qualname__ != "apply_hooks.<locals>._get_template"
    ):
        raise LegacyConflictError("Another integration owns the frontend template")
    try:
        closure = dict(
            zip(
                current.__code__.co_freevars,
                (cell.cell_contents for cell in (current.__closure__ or ())),
                strict=True,
            )
        )
    except ValueError as err:
        raise LegacyConflictError("Legacy favicon template closure is invalid") from err
    if closure.get("data") is not data:
        raise LegacyConflictError("Legacy favicon template state is not recognized")


def _clear_template_caches(hass: Any) -> None:
    """Discard templates already modified by the old hooks."""
    for resource in hass.http.app.router.resources():
        if isinstance(resource, frontend.IndexView):
            resource._template_cache = None
    render = getattr(frontend, "_async_render_index_cached", None)
    clear_cache = getattr(render, "cache_clear", None)
    if clear_cache is not None:
        clear_cache()


async def async_isolate_legacy(hass: Any) -> bool:
    """Remove known old hooks once, keeping them dormant until HA restarts.

    Return False when favicon has not loaded, or True after isolation. Unknown
    hooks raise LegacyConflictError before anything is changed. This deliberately
    does not edit YAML, config entries, source files, or the user's icon files.
    """
    module = sys.modules.get(_LEGACY_MODULE)
    if module is None:
        return False
    previous = getattr(module, _ISOLATION_ATTRIBUTE, None)
    if previous is not None:
        if (
            isinstance(previous, _Isolation)
            and previous.hass is hass
            and module.apply_hooks is _blocked_apply_hooks
            and module.remove_hooks is _blocked_remove_hooks
        ):
            return True
        raise LegacyConflictError("Legacy favicon changed after isolation")
    if DOMAIN not in hass.data:
        # Importing an integration does not mean its async_setup has run.
        return False
    _validate_legacy(module, hass)
    original_apply = module.apply_hooks
    original_remove = module.remove_hooks
    try:
        original_remove(hass)
        # The old plugin restores an obsolete short name. Normalize only its
        # exact known default pair, leaving any other branding untouched.
        if (
            frontend.MANIFEST_JSON["name"] == "Home Assistant"
            and frontend.MANIFEST_JSON["short_name"] == "Assistant"
        ):
            frontend.add_manifest_json_key("short_name", "Home Assistant")
        _clear_template_caches(hass)
    except Exception as err:
        raise LegacyConflictError("Legacy favicon could not be safely detached") from err
    module.apply_hooks = _blocked_apply_hooks
    module.remove_hooks = _blocked_remove_hooks
    setattr(
        module,
        _ISOLATION_ATTRIBUTE,
        _Isolation(hass, original_apply, original_remove),
    )
    _LOGGER.warning(
        "LTCN LOGO CHANGER isolated the legacy favicon hooks for this HA session. "
        "Legacy configuration and files are unchanged. Remove the old Favicon "
        "changer integration to complete migration; otherwise removing LTCN "
        "LOGO CHANGER and restarting HA can reactivate the old integration."
    )
    return True
