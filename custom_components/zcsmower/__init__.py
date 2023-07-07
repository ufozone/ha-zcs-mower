"""ZCS Lawn Mower Robot integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_NAME,
)
from homeassistant.helpers import (
    config_validation as cv,
)

from .const import (
    LOGGER,
    DOMAIN,
    PLATFORMS,
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
from .coordinator import ZcsMowerDataUpdateCoordinator

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up ZCS Lawn Mower Robot component."""
    hass.data.setdefault(DOMAIN, {})

    await async_setup_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator = ZcsMowerDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()

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

    if config_entry.version < 6:
        config_entry.version = 6
        _mowers = dict(config_entry.options.get(CONF_MOWERS, []))
        for _imei, _name in _mowers.items():
            _mowers[_imei] = {
                ATTR_NAME: _name,
            }
        _options = dict(config_entry.options)
        _options.update(
            {
                CONF_MOWERS: _mowers,
            }
        )
        hass.config_entries.async_update_entry(
            config_entry,
            title=str(config_entry.title),
            data={},
            options=_options,
        )

    LOGGER.info("Migration to version %s successful", config_entry.version)
    return True
