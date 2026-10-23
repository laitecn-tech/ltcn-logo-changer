"""Apply a startup snapshot through Home Assistant's frontend APIs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from urllib.parse import urlencode

from homeassistant.components import frontend

from .const import ASSET_URL, CONF_NAME, CONF_REVISION, FRONTEND_URL, VERSION


@dataclass
class Branding:
    """The URLs/manifest values owned by one loaded config entry."""

    module_url: str
    original_manifest: dict
    applied_manifest: dict

    @classmethod
    def install(cls, hass, settings: dict) -> Branding:
        name = settings[CONF_NAME]
        base = f"{ASSET_URL}/{settings[CONF_REVISION]}"
        values = {
            "name": name,
            "short_name": name[:24],
            "icons": [
                {"src": f"{base}/icon-{size}.png", "sizes": f"{size}x{size}",
                 "type": "image/png", "purpose": "any"}
                for size in (192, 512)
            ],
        }
        original = {key: deepcopy(frontend.MANIFEST_JSON[key]) for key in values}
        url = f"{FRONTEND_URL}/branding.js?" + urlencode({
            "v": VERSION, "name": name, "revision": settings[CONF_REVISION],
        })
        try:
            for key, value in values.items():
                frontend.add_manifest_json_key(key, value)
            frontend.add_extra_js_url(hass, url)
        except Exception:
            for key, value in original.items():
                frontend.add_manifest_json_key(key, value)
            raise
        return cls(url, original, deepcopy(values))

    def remove(self, hass) -> None:
        frontend.remove_extra_js_url(hass, self.module_url)
        for key, value in self.original_manifest.items():
            # Do not erase another component's subsequent intentional change.
            if frontend.MANIFEST_JSON[key] == self.applied_manifest[key]:
                frontend.add_manifest_json_key(key, deepcopy(value))
