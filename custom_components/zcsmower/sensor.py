"""ZCS Lawn Mower Robot sensor platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from .const import (
    LOGGER,
    DOMAIN,
    ROBOT_STATES,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity


ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="state",
        translation_key="state",
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            ZcsMowerSensor(
                coordinator=coordinator,
                entity_description=entity_description,
                imei=imei,
                name=name,
            )
            for imei, name in coordinator.mowers.items()
            for entity_description in ENTITY_DESCRIPTIONS
        ],
        update_before_add=True,
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
        entity_description: SensorEntityDescription,
        imei: str,
        name: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(
            coordinator=coordinator,
            imei=imei,
            name=name,
            entity_type="sensor",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description

    @property
    def icon(self) -> str:
        """Return the icon of the entity."""
        return ROBOT_STATES[self._state]["icon"]

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return ROBOT_STATES[self._state]["name"]
