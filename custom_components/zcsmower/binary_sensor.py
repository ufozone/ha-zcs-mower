"""ZCS Lawn Mower Robot binary sensor platform."""

from __future__ import annotations

from dataclasses import dataclass

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
    CONF_STANDBY_TIME_START,
    CONF_STANDBY_TIME_STOP,
    ATTR_CONNECTED,
    ATTR_LAST_COMM,
    ATTR_LAST_SEEN,
    ATTR_LAST_PULL,
    ATTR_NEXT_PULL,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import (
    ZcsMowerRobotEntity,
    ZcsMowerConfigEntity,
)


@dataclass(frozen=True, kw_only=True)
class ZcsMowerConfigBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes ZCS Lawn Mower Configuration binary sensor entity."""

    config_key: str


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

CONFIG_ENTITY_DESCRIPTIONS = (
    ZcsMowerConfigBinarySensorEntityDescription(
        key="mower_standby",
        translation_key="standby",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        config_key="standby",
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
            ZcsMowerRobotBinarySensorEntity(
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
    async_add_entities(
        [
            ZcsMowerConfigBinarySensorEntity(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in CONFIG_ENTITY_DESCRIPTIONS
        ],
        update_before_add=True,
    )


class ZcsMowerRobotBinarySensorEntity(ZcsMowerRobotEntity, BinarySensorEntity):
    """Representation of a ZCS Lawn Mower Robot binary sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
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
        """Return True if the binary_sensor is on."""
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

class ZcsMowerConfigBinarySensorEntity(ZcsMowerConfigEntity, BinarySensorEntity):
    """Representation of a ZCS Lawn Mower Configuration binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            entity_type="binary_sensor",
            entity_description=entity_description,
        )

    @property
    def is_on(self) -> bool:
        """Return True if the binary_sensor is on."""
        if self._config_key == "standby":
            return self.coordinator.is_standby_time()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if self._config_key == "standby":
            return (self.coordinator.hibernation_enable is False)

        return True

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra attributes."""
        if self._config_key == "standby":
            return {
                CONF_STANDBY_TIME_START: self.coordinator.next_standby_start(),
                CONF_STANDBY_TIME_STOP: self.coordinator.next_standby_stop(),
            }
