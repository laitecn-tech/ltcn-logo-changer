"""Native Home Assistant forms: a name and one uploaded image."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    ACCEPTED_FILES,
    ASSET_URL,
    CONF_NAME,
    CONF_REVISION,
    CONF_UPLOAD,
    DEFAULT_NAME,
    DOMAIN,
    NAME,
    STORAGE_PARTS,
)
from .images import ImageValidationError, assets_exist, convert_icon, validate_name


def _schema(name: str, *, require_upload: bool) -> vol.Schema:
    upload_key = vol.Required if require_upload else vol.Optional
    return vol.Schema({
        vol.Required(CONF_NAME, default=name): selector.TextSelector(),
        upload_key(CONF_UPLOAD): selector.FileSelector(
            selector.FileSelectorConfig(accept=ACCEPTED_FILES)
        ),
    })


def _convert_upload(hass, file_id: str) -> str:
    """Keep the file-upload context, processing and cleanup on one executor."""
    with process_uploaded_file(hass, file_id) as uploaded:
        return convert_icon(uploaded, Path(hass.config.path(*STORAGE_PARTS)))


async def _settings(hass, user_input: dict[str, Any], previous: dict | None = None) -> dict:
    name = validate_name(user_input.get(CONF_NAME))
    previous = previous or {}
    revision = previous.get(CONF_REVISION)
    if file_id := user_input.get(CONF_UPLOAD):
        try:
            revision = await hass.async_add_executor_job(_convert_upload, hass, file_id)
        except ImageValidationError:
            raise
        except ValueError as exc:
            raise ImageValidationError("upload_expired") from exc
        except OSError as exc:
            raise ImageValidationError("storage_error") from exc
    elif not await hass.async_add_executor_job(
        assets_exist, Path(hass.config.path(*STORAGE_PARTS)), revision
    ):
        raise ImageValidationError("upload_required")
    return {CONF_NAME: name, CONF_REVISION: revision, "enabled": True}


class LogoChangerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up one brand for this Home Assistant."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LogoChangerOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self._async_current_entries(include_ignore=False):
            return self.async_abort(reason="single_instance_allowed")
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            try:
                settings = await _settings(self.hass, user_input)
            except ImageValidationError as exc:
                errors["base"] = exc.code
            else:
                return self.async_create_entry(title=NAME, data=settings)
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(
                str((user_input or {}).get(CONF_NAME, DEFAULT_NAME)), require_upload=True
            ),
            errors=errors,
        )


class LogoChangerOptionsFlow(config_entries.OptionsFlow):
    """Persist pending changes without hot-reloading the frontend."""

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(step_id="init", menu_options=["configure", "reset"])

    async def async_step_configure(self, user_input=None):
        current = {**self.config_entry.data, **self.config_entry.options}
        root = Path(self.hass.config.path(*STORAGE_PARTS))
        has_icon = await self.hass.async_add_executor_job(
            assets_exist, root, current.get(CONF_REVISION)
        )
        errors = {}
        if user_input is not None:
            try:
                settings = await _settings(self.hass, user_input, current)
            except ImageValidationError as exc:
                errors["base"] = exc.code
            else:
                return self.async_create_entry(title="", data=settings)
        return self.async_show_form(
            step_id="configure",
            data_schema=_schema(
                str((user_input or current).get(CONF_NAME, DEFAULT_NAME)),
                require_upload=not has_icon,
            ),
            description_placeholders={
                "preview": (
                    f"![Logo]({ASSET_URL}/{current[CONF_REVISION]}/icon-192.png)"
                    if has_icon else ""
                )
            },
            errors=errors,
        )

    async def async_step_reset(self, user_input=None):
        if user_input is not None:
            current = {**self.config_entry.data, **self.config_entry.options}
            # Retain the last image so restoring the custom brand is simple.
            current["enabled"] = False
            return self.async_create_entry(title="", data=current)
        return self.async_show_form(step_id="reset", data_schema=vol.Schema({}))
