"""ZCS Lawn Mower Robot sensor platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from .const import (
    LOGGER,
    DOMAIN,
    CONF_MOWERS,
    ROBOT_STATES,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            ZcsMowerSensor(coordinator, imei, name)
            for imei, name in coordinator.mowers.items()
        ],
        update_before_add=True
    )


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    
    # TODO
    LOGGER.debug("async_setup_platform")
    LOGGER.debug(config_entry)


class ZcsMowerSensor(ZcsMowerEntity, SensorEntity):
    """Representation of a ZCS Lawn Mower Robot sensor."""

    def __init__(
        self,
        coordinator: ZcsMowerDataUpdateCoordinator,
        imei: str,
        name: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(
            coordinator=coordinator,
            imei=imei,
            name=name,
            entity_type="sensor",
            entity_key="state",
        )
    
    @property
    def state(self) -> str | None:
        return ROBOT_STATES[self._state]["name"]
    
    @property
    def icon(self) -> str:
        """Return the icon of the entity."""
        return ROBOT_STATES[self._state]["icon"]
    
    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return ROBOT_STATES[0]["name"]