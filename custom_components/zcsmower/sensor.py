"""ZCS Lawn Mower Robot sensor platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Update our config to include new mowers and remove those that have been removed.
    if config_entry.options:
        coordinator.config.update(config_entry.options)
    
    sensors = [ZcsMowerSensor(coordinator, mower) for mower in coordinator.config[CONF_MOWERS]]
    async_add_devices(sensors)
    #async_add_devices(sensors, update_before_add=True)


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    
    # TODO
    LOGGER.error("async_setup_platform")
    LOGGER.error(config_entry)


class ZcsMowerSensor(ZcsMowerEntity, SensorEntity):
    """Representation of a ZCS Lawn Mower Robot sensor."""

    def __init__(
        self,
        coordinator: ZcsMowerDataUpdateCoordinator,
        mower: dict[str, str],
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(
            coordinator=coordinator,
            mower=mower,
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
