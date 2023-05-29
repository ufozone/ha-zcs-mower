"""ZCS Lawn Mower Robot integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    LOGGER,
    DOMAIN,
    PLATFORMS,
    API_BASE_URI,
    API_APP_TOKEN,
    CONF_CLIENT_KEY,
    CONF_CAMERA_ENABLE,
    CONF_MAP_HISTORY_ENABLE,
    CONF_MAP_IMAGE_PATH,
    CONF_MAP_MARKER_PATH,
    CONF_MAP_GPS_TOP_LEFT,
    CONF_MAP_GPS_BOTTOM_RIGHT,
    CONF_MAP_POINTS,
    CONF_MAP_DRAW_LINES,
    CONF_MOWERS,
    MAP_POINTS_DEFAULT,
)
from .services import async_setup_services
from .api import ZcsMowerApiClient
from .coordinator import ZcsMowerDataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up ZCS Lawn Mower Robot component."""
    hass.data.setdefault(DOMAIN, {})

    await async_setup_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = ZcsMowerDataUpdateCoordinator(
        mowers=entry.options[CONF_MOWERS],
        hass=hass,
        client=ZcsMowerApiClient(
            session=async_get_clientsession(hass),
            options={
                "endpoint": API_BASE_URI,
                "app_id": entry.options[CONF_CLIENT_KEY],
                "app_token": API_APP_TOKEN,
                "thing_key": entry.options[CONF_CLIENT_KEY]
            }
        ),
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove config entry from domain.
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    LOGGER.info("Migrating from version %s", config_entry.version)

    if config_entry.version < 3:
        config_entry.version = 3
        hass.config_entries.async_update_entry(
            config_entry,
            title=str(config_entry.title),
            data={},
            options={
                CONF_CLIENT_KEY: config_entry.data.get(CONF_CLIENT_KEY, ""),
                CONF_CAMERA_ENABLE: False,
                CONF_MAP_IMAGE_PATH: "",
                CONF_MAP_MARKER_PATH: "",
                CONF_MAP_GPS_TOP_LEFT: "",
                CONF_MAP_GPS_BOTTOM_RIGHT: "",
                CONF_MOWERS: config_entry.data.get(CONF_MOWERS, {}),
            },
        )
    if config_entry.version < 4:
        config_entry.version = 4
        _options = dict(config_entry.options)
        _options.update(
            {
                CONF_MAP_POINTS: config_entry.options.get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT),
                CONF_MAP_DRAW_LINES: True,
            }
        )
        hass.config_entries.async_update_entry(
            config_entry,
            title=str(config_entry.title),
            data={},
            options=_options,
        )
    if config_entry.version < 5:
        config_entry.version = 5
        hass.config_entries.async_update_entry(
            config_entry,
            title=str(config_entry.title),
            data={},
            options={
                CONF_CLIENT_KEY: config_entry.options.get(CONF_CLIENT_KEY, ""),
                CONF_CAMERA_ENABLE: config_entry.options.get(CONF_CAMERA_ENABLE, False),
                CONF_MAP_IMAGE_PATH: config_entry.options.get("img_path_map", ""),
                CONF_MAP_MARKER_PATH: config_entry.options.get("img_path_marker", ""),
                CONF_MAP_GPS_TOP_LEFT: config_entry.options.get("gps_top_left", ""),
                CONF_MAP_GPS_BOTTOM_RIGHT: config_entry.options.get("gps_bottom_right", ""),
                CONF_MAP_HISTORY_ENABLE: config_entry.options.get(CONF_MAP_HISTORY_ENABLE, True),
                CONF_MAP_POINTS: config_entry.options.get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT),
                CONF_MAP_DRAW_LINES: config_entry.options.get("draw_lines", True),
                CONF_MOWERS: config_entry.options.get(CONF_MOWERS, {}),
            },
        )

    LOGGER.info("Migration to version %s successful", config_entry.version)
    return True
