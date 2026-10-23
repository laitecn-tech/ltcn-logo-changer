"""Constants for LTCN LOGO CHANGER."""

DOMAIN = "ltcn_logo_changer"
NAME = "LTCN LOGO CHANGER"
VERSION = "v0.8.0"
CONF_NAME = "brand_name"
CONF_UPLOAD = "icon_upload"
CONF_REVISION = "icon_revision"
DEFAULT_NAME = "LTCN AI HOME"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MAX_IMAGE_SIDE = 8192
ASSET_FORMAT_VERSION = "1"
ASSET_FILES = (
    "icon.png",
    "favicon.ico",
    "apple-touch-icon.png",
    "icon-192.png",
    "icon-512.png",
)
STORAGE_PARTS = ("www", DOMAIN)
ASSET_URL = f"/local/{DOMAIN}"
FRONTEND_URL = f"/{DOMAIN}_static"
NOTIFICATION_ID = f"{DOMAIN}_restart"
ACCEPTED_FILES = "image/png,image/jpeg,image/webp,image/x-icon,image/vnd.microsoft.icon,.ico"
