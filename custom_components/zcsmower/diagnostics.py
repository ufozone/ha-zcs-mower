"""Diagnostics support for ZCS Lawn Mower Robot."""
from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_LOCATION,
)

from .const import (
    DOMAIN,
    CONF_CLIENT_KEY,
    CONF_MAP_GPS_TOP_LEFT,
    CONF_MAP_GPS_BOTTOM_RIGHT,
    CONF_MOWERS,
    ATTR_IMEI,
    ATTR_SERIAL_NUMBER,
    ATTR_LOCATION_HISTORY,
)

TO_REDACT = {
    CONF_CLIENT_KEY,
    CONF_MAP_GPS_TOP_LEFT,
    CONF_MAP_GPS_BOTTOM_RIGHT,
    CONF_MOWERS,
    ATTR_IMEI,
    ATTR_SERIAL_NUMBER,
    ATTR_LOCATION,
    ATTR_LOCATION_HISTORY,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, any]:
    """Return diagnostics of the config entry and lawn mower data."""
    coordinator = config_entry.runtime_data
    diagnostics_data = {
        "config_entry_data": async_redact_data(config_entry.as_dict(), TO_REDACT),
        "coordinator_data": async_redact_data(coordinator.data, TO_REDACT),
    }
    return diagnostics_data
