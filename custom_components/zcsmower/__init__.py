"""ZCS Lawn Mower Robot integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
)
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
    CONF_STANDBY_TIME_START,
    CONF_STANDBY_TIME_STOP,
    CONF_UPDATE_INTERVAL_WORKING,
    CONF_UPDATE_INTERVAL_STANDBY,
    CONF_UPDATE_INTERVAL_IDLING,
    CONF_TRACE_POSITION_ENABLE,
    CONF_WAKE_UP_INTERVAL_DEFAULT,
    CONF_WAKE_UP_INTERVAL_INFINITY,
    CONF_MAP_ENABLE,
    CONF_MAP_HISTORY_ENABLE,
    CONF_MAP_IMAGE_PATH,
    CONF_MAP_MARKER_PATH,
    CONF_MAP_GPS_TOP_LEFT,
    CONF_MAP_GPS_BOTTOM_RIGHT,
    CONF_MAP_ROTATION,
    CONF_MAP_POINTS,
    CONF_MAP_DRAW_LINES,
    CONF_MOWERS,
    STANDBY_TIME_START_DEFAULT,
    STANDBY_TIME_STOP_DEFAULT,
    UPDATE_INTERVAL_WORKING_DEFAULT,
    UPDATE_INTERVAL_STANDBY_DEFAULT,
    UPDATE_INTERVAL_IDLING_DEFAULT,
    MAP_POINTS_DEFAULT,
    ROBOT_WAKE_UP_INTERVAL_DEFAULT,
    ROBOT_WAKE_UP_INTERVAL_INFINITY,
)
from .services import async_setup_services
from .coordinator import ZcsMowerDataUpdateCoordinator
from .api import ZcsMowerApiAuthenticationError

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up ZCS Lawn Mower Robot component."""
    await async_setup_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    try:
        coordinator = ZcsMowerDataUpdateCoordinator(
            hass=hass,
            config_entry=config_entry,
        )
        await coordinator.initialize()
        await coordinator.async_config_entry_first_refresh()
    except ZcsMowerApiAuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        raise ConfigEntryNotReady from err

    config_entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    config_entry.async_on_unload(
        config_entry.add_update_listener(async_reload_entry)
    )
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    LOGGER.info("Migrating from version %s", config_entry.version)

    if config_entry.version < 5:
        config_entry.version = 5
        hass.config_entries.async_update_entry(
            config_entry,
            title=str(config_entry.title),
            data={},
            options={
                CONF_CLIENT_KEY: config_entry.options.get(CONF_CLIENT_KEY, ""),
                CONF_MAP_ENABLE: config_entry.options.get(CONF_MAP_ENABLE, False),
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

    if config_entry.version < 9:
        config_entry.version = 9
        _options = dict(config_entry.options)
        _options.update(
            {
                CONF_TRACE_POSITION_ENABLE: config_entry.options.get(CONF_TRACE_POSITION_ENABLE, False),
                CONF_WAKE_UP_INTERVAL_DEFAULT: config_entry.options.get(CONF_WAKE_UP_INTERVAL_DEFAULT, ROBOT_WAKE_UP_INTERVAL_DEFAULT),
                CONF_WAKE_UP_INTERVAL_INFINITY: config_entry.options.get(CONF_WAKE_UP_INTERVAL_INFINITY, ROBOT_WAKE_UP_INTERVAL_INFINITY),
                CONF_STANDBY_TIME_START: STANDBY_TIME_START_DEFAULT,
                CONF_STANDBY_TIME_STOP: STANDBY_TIME_STOP_DEFAULT,
                CONF_UPDATE_INTERVAL_WORKING: config_entry.options.get("uptade_interval_working", UPDATE_INTERVAL_WORKING_DEFAULT),
                CONF_UPDATE_INTERVAL_STANDBY: config_entry.options.get("uptade_interval_idling", UPDATE_INTERVAL_STANDBY_DEFAULT),
                CONF_UPDATE_INTERVAL_IDLING: UPDATE_INTERVAL_IDLING_DEFAULT,
            }
        )
        _options.pop("trace_position_interval_default")
        _options.pop("trace_position_interval_infinity")
        _options.pop("uptade_interval_working")
        _options.pop("uptade_interval_idling")

        hass.config_entries.async_update_entry(
            config_entry,
            title=str(config_entry.title),
            data={},
            options=_options,
        )

    if config_entry.version < 10:
        config_entry.version = 10

        if (gps_top_left := config_entry.options.get(CONF_MAP_GPS_TOP_LEFT, None)) == "":
            gps_top_left = None

        if (gps_bottom_right := config_entry.options.get(CONF_MAP_GPS_BOTTOM_RIGHT, None)) == "":
            gps_bottom_right = None

        _options = dict(config_entry.options)
        _options.update(
            {
                CONF_MAP_ENABLE: config_entry.options.get("camera_enable", CONF_MAP_ENABLE),
                CONF_MAP_GPS_TOP_LEFT: gps_top_left,
                CONF_MAP_GPS_BOTTOM_RIGHT: gps_bottom_right,
                CONF_MAP_ROTATION: 0.0,
            }
        )
        _options.pop("camera_enable")

        hass.config_entries.async_update_entry(
            config_entry,
            title=str(config_entry.title),
            data={},
            options=_options,
        )

    LOGGER.info("Migration to version %s successful", config_entry.version)
    return True
