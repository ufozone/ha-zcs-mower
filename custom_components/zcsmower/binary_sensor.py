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
from homeassistant.helpers.entity import Entity

from .const import (
    DOMAIN,
    ATTR_ERROR,
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
            ZcsMowerBinarySensorEntity(
                hass=hass,
                config_entry=config_entry,
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


class ZcsMowerBinarySensorEntity(ZcsMowerEntity, BinarySensorEntity):
    """Representation of a ZCS Lawn Mower Robot binary sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
        imei: str,
        name: str,
    ) -> None:
        """Initialize the binary sensor class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            imei=imei,
            name=name,
            entity_type="binary_sensor",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        if self._entity_key == "error":
            if self._get_attribute(ATTR_STATE) == "fail":
                assert self.platform
                _error = self._get_attribute(ATTR_ERROR, "unknown")
                _name_translation_key = (
                    f"component.{self.platform.platform_name}.entity"
                    f".sensor.error.state.{_error}"
                )
                _error_reason: str = self.platform.entity_translations.get(_name_translation_key, _error)
                self._additional_extra_state_attributes = {
                    "reason": _error_reason,
                }

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        if self._entity_key == "error":
            return self._get_attribute(ATTR_STATE) == "fail"
