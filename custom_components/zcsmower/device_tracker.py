"""ZCS Lawn Mower Robot sensor platform."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_LOCATION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.recorder import (
    get_instance,
    history,
)
from homeassistant.helpers.entity import (
    Entity,
    EntityDescription,
)
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    LOCATION_HISTORY_DAYS,
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
            imei=imei,
            entity_type="device_tracker",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description

        get_instance(self.hass).async_add_executor_job(
            self._get_location_history,
        )

    def _get_location_history(self) -> None:
        # Getting history with history.get_last_state_changes can cause instability
        # because it has to scan the table to find the last number_of_states states
        # because the metadata_id_last_updated_ts index is in ascending order.
        history_list = history.state_changes_during_period(
            self.hass,
            start_time=dt_util.now() - timedelta(days=LOCATION_HISTORY_DAYS),
            entity_id=self.entity_id,
            no_attributes=False,
            include_start_time_state=True,
        )
        self.coordinator.init_location_history(
            imei=self._imei,
        )
        for state in history_list.get(self.entity_id, []):
            latitude = state.attributes.get(ATTR_LATITUDE, None)
            longitude = state.attributes.get(ATTR_LONGITUDE, None)
            if latitude and longitude:
                self.coordinator.add_location_history(
                    imei=self._imei,
                    location=(latitude, longitude),
                )
        # Always update HA states after getting location history.
        self.hass.async_create_task(
            self.coordinator._async_update_listeners()
        )

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
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS

    @property
    def device_class(self):
        """Return Device Class."""
        return None
