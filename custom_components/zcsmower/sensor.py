"""ZCS Lawn Mower Robot sensor platform."""
from __future__ import annotations

from datetime import (
    date,
    datetime,
)

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_STATE,
    ATTR_ICON,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.helpers.entity import (
    Entity,
    EntityCategory,
)
from homeassistant.helpers.typing import StateType
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_CONNECT_EXPIRATION,
    ATTR_INFINITY_STATE,
    ATTR_INFINITY_EXPIRATION,
)
from .coordinator import ZcsDataUpdateCoordinator
from .entity import ZcsMowerRobotEntity

ROBOT_ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key=None,
        device_class=SensorDeviceClass.ENUM,
        translation_key="state",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=ATTR_CONNECT_EXPIRATION,
        icon="mdi:ev-station",
        device_class=SensorDeviceClass.TIMESTAMP,
        translation_key=ATTR_CONNECT_EXPIRATION,
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
            ZcsMowerRobotSensorEntity(
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


class ZcsMowerRobotSensorEntity(ZcsMowerRobotEntity, SensorEntity):
    """Representation of a ZCS Lawn Mower Robot sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        imei: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            entity_type="sensor",
            entity_description=entity_description,
            imei=imei,
        )

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        if self._entity_key == ATTR_CONNECT_EXPIRATION:
            # +Infinity state
            self._additional_extra_state_attributes.update({
                ATTR_INFINITY_STATE: (
                    self._get_attribute(ATTR_INFINITY_STATE) in ("active", "pending")
                    and self._get_attribute(ATTR_INFINITY_EXPIRATION) > dt_util.now()
                ),
            })
            # +Infinity expiration date
            if (_infinity_expiration := self._get_attribute(ATTR_INFINITY_EXPIRATION)) is not None:
                self._additional_extra_state_attributes.update({
                    ATTR_INFINITY_EXPIRATION: _infinity_expiration,
                })

    @property
    def icon(self) -> str:
        """Return the icon of the entity."""
        if self._entity_key is None:
            return self._get_attribute(ATTR_ICON)

        # Fallback
        return self.entity_description.icon

    @property
    def native_value(self) -> StateType | date | datetime:
        """Return the native value of the sensor."""
        if self._entity_key is None:
            return self._get_attribute(ATTR_STATE)
        elif self._entity_key == ATTR_CONNECT_EXPIRATION:
            return self._get_attribute(ATTR_CONNECT_EXPIRATION)
