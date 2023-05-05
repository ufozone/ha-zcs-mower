"""ZCS Lawn Mower Robot binary sensor platform."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from .const import (
    LOGGER,
    DOMAIN,
    ROBOT_ERRORS,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="error",
        translation_key="error",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup sensors from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            ZcsMowerBinarySensor(
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
    """Set up the sensor binary platform."""
    # TODO
    LOGGER.debug("async_setup_platform")


class ZcsMowerBinarySensor(ZcsMowerEntity, BinarySensorEntity):
    """Representation of a ZCS Lawn Mower Robot binary sensor."""

    def __init__(
        self,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
        imei: str,
        name: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(
            coordinator=coordinator,
            imei=imei,
            name=name,
            entity_type="binary_sensor",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description

    def update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        if self._state == 4:
            if self._error in ROBOT_ERRORS:
                _reason = ROBOT_ERRORS[self._error]
            else:
                _reason = "unknown"
            self._additional_extra_state_attributes = {
                "reason": _reason,
            }

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return self._state == 4
