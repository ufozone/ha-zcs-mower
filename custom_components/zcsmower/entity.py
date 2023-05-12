"""ZCS Lawn Mower Robot entity."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.const import (
    ATTR_NAME,
    ATTR_STATE,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SW_VERSION,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    ATTRIBUTION,
    ATTR_IMEI,
    ATTR_AVAILABLE,
    ATTR_CONNECTED,
    ATTR_LAST_COMM,
    ATTR_LAST_SEEN,
    ATTR_LAST_PULL,
)
from .coordinator import ZcsMowerDataUpdateCoordinator


class ZcsMowerEntity(CoordinatorEntity):
    """ZCS Lawn Mower Robot class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: ZcsMowerDataUpdateCoordinator,
        imei: str,
        name: str,
        entity_type: str,
        entity_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self._imei = imei
        self._name = name
        self._entity_type = entity_type
        self._entity_key = entity_key
        if entity_key:
            self._unique_id = slugify(f"{self._imei}_{self._name}_{entity_key}")
        else:
            self._unique_id = slugify(f"{self._imei}_{self._name}")
        self._additional_extra_state_attributes = {}

        self.entity_id = f"{entity_type}.{self._unique_id}"

    def _get_attribute(
        self,
        attr: str,
        default_value: any | None = None,
    ) -> any:
        """Get attribute of the current mower."""
        return self.coordinator.data.get(self._imei, {}).get(attr, default_value)

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        self._additional_extra_state_attributes = {}

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._get_attribute(ATTR_AVAILABLE, False)

    @property
    def device_info(self):
        """Return the device info."""
        return {
            ATTR_IDENTIFIERS: {
                (DOMAIN, self._imei)
            },
            ATTR_NAME: self._name,
            ATTR_MANUFACTURER: self._get_attribute(ATTR_MANUFACTURER),
            ATTR_MODEL: self._get_attribute(ATTR_MODEL),
            ATTR_SW_VERSION: self._get_attribute(ATTR_SW_VERSION),
        }

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return axtra attributes."""
        _extra_state_attributes = self._additional_extra_state_attributes
        _extra_state_attributes.update(
            {
                ATTR_IMEI: self._imei,
                ATTR_CONNECTED: self._get_attribute(ATTR_CONNECTED),
                ATTR_LAST_COMM: self._get_attribute(ATTR_LAST_COMM),
                ATTR_LAST_SEEN: self._get_attribute(ATTR_LAST_SEEN),
                ATTR_LAST_PULL: self._get_attribute(ATTR_LAST_PULL),
            }
        )
        return _extra_state_attributes

    async def async_update(self) -> None:
        """Peform async_update."""
        self._update_handler()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_handler()
        self.async_write_ha_state()

    def _update_handler(self) -> None:
        """Handle updated data."""
        self._update_extra_state_attributes()
