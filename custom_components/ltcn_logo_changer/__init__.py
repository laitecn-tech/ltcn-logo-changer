"""LTCN LOGO CHANGER: safe uploads and restart-applied branding."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from homeassistant.components import persistent_notification
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CoreState
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv

from .branding import Branding
from .const import (
    CONF_NAME, CONF_REVISION, DOMAIN, FRONTEND_URL, NAME,
    NOTIFICATION_ID, STORAGE_PARTS,
)
from .images import ImageValidationError, assets_exist, validate_name
from .legacy import LegacyConflictError, async_isolate_legacy

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass
class Runtime:
    registered: bool = False
    entry_id: str | None = None
    branding: Branding | None = None


def _state(hass) -> Runtime:
    return hass.data.setdefault(DOMAIN, Runtime())


def _notify_restart(hass) -> None:
    chinese = str(hass.config.language).lower().startswith("zh")
    persistent_notification.async_create(
        hass,
        (
            "品牌设置已保存。请重启 Home Assistant，然后完全退出并重新打开手机 App 或刷新网页。\n\n"
            "图标已自动转换并保存，无需移动文件。"
            if chinese else
            "Brand settings saved. Restart Home Assistant, then reopen the mobile App "
            "or reload the page. Your icon has been converted and saved automatically."
        ),
        title=NAME, notification_id=NOTIFICATION_ID,
    )


async def async_setup(hass, config) -> bool:
    _state(hass)
    return True


async def _options_updated(hass, entry) -> None:
    """Save now; retain the active startup brand until a real restart."""
    _notify_restart(hass)


async def async_setup_entry(hass, entry: ConfigEntry) -> bool:
    state = _state(hass)
    if state.entry_id is not None and state.entry_id != entry.entry_id:
        raise ConfigEntryError(translation_domain=DOMAIN, translation_key="single_instance")
    settings = {**entry.data, **entry.options}
    if not state.registered:
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                FRONTEND_URL, str(Path(__file__).parent / "frontend"), cache_headers=False
            )
        ])
        state.registered = True
    entry.async_on_unload(entry.add_update_listener(_options_updated))
    if hass.state is CoreState.running:
        _notify_restart(hass)
        state.entry_id = entry.entry_id
        return True

    # Isolate the known old plugin even when restoring defaults, or it would
    # immediately replace the Home Assistant defaults again.
    try:
        await async_isolate_legacy(hass)
    except LegacyConflictError as exc:
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="legacy_conflict"
        ) from exc

    if settings.get("enabled", True):
        try:
            settings[CONF_NAME] = validate_name(settings.get(CONF_NAME))
        except ImageValidationError as exc:
            raise ConfigEntryError(
                translation_domain=DOMAIN, translation_key="invalid_settings"
            ) from exc
        if not await hass.async_add_executor_job(
            assets_exist, Path(hass.config.path(*STORAGE_PARTS)), settings.get(CONF_REVISION)
        ):
            raise ConfigEntryError(
                translation_domain=DOMAIN, translation_key="missing_icons"
            )
        state.branding = Branding.install(hass, settings)
    persistent_notification.async_dismiss(hass, NOTIFICATION_ID)
    state.entry_id = entry.entry_id
    return True


async def async_unload_entry(hass, entry: ConfigEntry) -> bool:
    state = _state(hass)
    if state.entry_id == entry.entry_id:
        if state.branding:
            state.branding.remove(hass)
        state.branding = None
        state.entry_id = None
    persistent_notification.async_dismiss(hass, NOTIFICATION_ID)
    return True
