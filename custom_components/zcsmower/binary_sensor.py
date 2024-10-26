"""ZCS Lawn Mower Robot binary sensor platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_STATE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import (
    Entity,
    EntityCategory,
)

from .const import (
    ATTR_CONNECTED,
    ATTR_LAST_COMM,
    ATTR_LAST_SEEN,
    ATTR_LAST_PULL,
    ATTR_NEXT_PULL,
)
from .coordinator import ZcsDataUpdateCoordinator
from .entity import ZcsRobotEntity

ROBOT_ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="error",
        translation_key="error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="connection",
        translation_key="connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup sensors from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        [
            ZcsRobotBinarySensorEntity(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                entity_description=entity_description,
                imei=imei,
            )
            for imei in coordinator.mowers
            for entity_description in ROBOT_ENTITY_DESCRIPTIONS
        ],
        update_before_add=True,
    )


class ZcsRobotBinarySensorEntity(ZcsRobotEntity, BinarySensorEntity):
    """Representation of a ZCS Lawn Mower Robot binary sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
        imei: str,
    ) -> None:
        """Initialize the binary sensor class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            entity_type="binary_sensor",
            entity_description=entity_description,
            imei=imei,
        )

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        if self._entity_key == "error":
            if self.is_on:
                self._additional_extra_state_attributes = {
                    "reason": self._get_localized_status(),
                }
        elif self._entity_key == "connection":
            self._additional_extra_state_attributes = {
                ATTR_LAST_COMM: self._get_attribute(ATTR_LAST_COMM),
                ATTR_LAST_SEEN: self._get_attribute(ATTR_LAST_SEEN),
                ATTR_LAST_PULL: self._get_attribute(ATTR_LAST_PULL),
                ATTR_NEXT_PULL: self._get_next_pull(),
            }

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        if self._entity_key == "error":
            return self._get_attribute(ATTR_STATE) in (
                "fail",
                "nosignal",
                "expired",
                "renewed",
                "hot_temperature",
            )
        elif self._entity_key == "connection":
            return (self._get_attribute(ATTR_CONNECTED) is True)
