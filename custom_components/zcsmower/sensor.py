"""ZCS Lawn Mower Robot sensor platform."""
from __future__ import annotations

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
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_CONNECT_EXPIRATION,
    ATTR_INFINITY_STATE,
    ATTR_INFINITY_EXPIRATION,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key=None,
        device_class=SensorDeviceClass.ENUM,
        translation_key="state",
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
            ZcsMowerSensorEntity(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                entity_description=entity_description,
                imei=imei,
            )
            for imei in coordinator.mowers
            for entity_description in ENTITY_DESCRIPTIONS
        ],
        update_before_add=True,
    )


class ZcsMowerSensorEntity(ZcsMowerEntity, SensorEntity):
    """Representation of a ZCS Lawn Mower Robot sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
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
        # Data expiration date
        if (_connect_expiration := self._get_attribute(ATTR_CONNECT_EXPIRATION)) is not None:
            self._additional_extra_state_attributes.update({
                ATTR_CONNECT_EXPIRATION: _connect_expiration,
            })
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
        return self._get_attribute(ATTR_ICON)

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return self._get_attribute(ATTR_STATE)
