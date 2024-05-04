"""ZCS Lawn Mower Robot sensor platform."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_LOCATION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.device_tracker import (
    SourceType,
    TrackerEntity,
)
from homeassistant.components.recorder import get_instance
from homeassistant.helpers.entity import (
    Entity,
    EntityDescription,
)
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ENTITY_DESCRIPTIONS = (
    EntityDescription(
        key=None,
        icon="mdi:robot-mower",
        translation_key="location",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup device tracker from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            ZcsMowerTrackerEntity(
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


class ZcsMowerTrackerEntity(ZcsMowerEntity, TrackerEntity):
    """Representation of a ZCS Lawn Mower Robot sensor."""

    _attr_name = None

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: EntityDescription,
        imei: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            entity_type="device_tracker",
            entity_description=entity_description,
            imei=imei,
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()

        # Load Recorder after loading entity
        await get_instance(self.hass).async_add_executor_job(
            self.coordinator.get_location_history,
            self.entity_id,
            self._imei,
        )

    @property
    def location_accuracy(self):
        """Return the gps accuracy of the device."""
        return 10

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        location = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LATITUDE, None)
        return location if location else None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        location = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LONGITUDE, None)
        return location if location else None

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def device_class(self):
        """Return Device Class."""
        return None
