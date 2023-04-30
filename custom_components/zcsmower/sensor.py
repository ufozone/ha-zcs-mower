"""ZCS Lawn Mower Robot sensor platform."""
from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientError
from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorEntityDescription
from homeassistant.const import (
    ATTR_NAME,
    CONF_NAME,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from .api_client import ZcsMowerApiClient
from .coordinator import ZcsMowerDataUpdateCoordinator

import voluptuous as vol

from .const import (
    API_BASE_URI,
    API_APP_TOKEN,
    CONF_CLIENT_KEY,
    CONF_IMEI,
    CONF_MOWERS,
    ATTR_IMEI,
    LOGGER,
    DOMAIN,
)

# Time between updating data from ZCS API
SCAN_INTERVAL = timedelta(minutes=1)

MOWER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IMEI): cv.string,
        vol.Optional(CONF_NAME): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CLIENT_KEY): cv.string,
        vol.Required(CONF_MOWERS): vol.All(cv.ensure_list, [MOWER_SCHEMA]),
    }
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator.config = coordinator.config
    
    # Update our config to include new mowers and remove those that have been removed.
    if config_entry.options:
        coordinator.config.update(config_entry.options)
    
    sensors = [ZcsMowerSensor(coordinator, mower) for mower in coordinator.config[CONF_MOWERS]]
    async_add_entities(sensors, update_before_add=True)


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    
    #client = ZcsMowerApiClient(
    #    session=async_get_clientsession(hass),
    #    options={
    #        "endpoint": API_BASE_URI,
    #        "app_id": config[CONF_CLIENT_KEY],
    #        "app_token": API_APP_TOKEN,
    #        "thing_key": config[CONF_CLIENT_KEY]
    #    }
    #)
    #sensors = [ZcsMowerSensor(client, mower) for mower in config[CONF_MOWERS]]
    #async_add_entities(sensors, update_before_add=True)


class ZcsMowerSensor(Entity):
    """Representation of a ZCS Lawn Mower Robot sensor."""

    def __init__(
            self,
            coordinator: ZcsMowerDataUpdateCoordinator,
            mower: dict[str, str]
        ):
        super().__init__()
        self.coordinator = coordinator
        self.client = coordinator.client
        self._imei = mower["imei"]
        self._name = mower.get("name", self._imei)
        self._state = None
        self._available = True
        self.attrs: dict[str, Any] = {
            ATTR_NAME: self._name,
            ATTR_IMEI: self._imei,
        }

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._imei

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> str | None:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.attrs

    async def async_update(self) -> None:
        """Update all sensors."""
        try:
            
            
            
            
            # Set state to short commit sha.
            self._state = "test"
            self._available = True
        except (aiohttp.ClientError, socket.gaierror):
            self._available = False
            LOGGER.exception(
                "Error retrieving data from ZCS API for sensor %s", self.name
            )

