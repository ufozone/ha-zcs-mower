"""ZCS Lawn Mower Robot sensor platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.helpers.entity import Entity
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
    async_add_entities: Entity,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            ZcsMowerDeviceTracker(coordinator, imei, name)
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


class ZcsMowerDeviceTracker(ZcsMowerEntity, TrackerEntity):
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
            entity_type="device_tracker",
            entity_key="location",
        )
    
    @property
    def latitude(self) -> Optional[float]:
        """Return latitude value of the device."""
        location = self._location.get("latitude", None)
        return location if location else None

    @property
    def longitude(self) -> Optional[float]:
        """Return longitude value of the device."""
        location = self._location.get("longitude", None)
        return location if location else None

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS

    @property
    def device_class(self):
        return None