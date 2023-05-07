"""ZCS Lawn Mower Robot entity."""
from __future__ import annotations

from homeassistant.const import (
    ATTR_NAME,
    ATTR_IDENTIFIERS,
    ATTR_LOCATION,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SW_VERSION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_STATE,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    MANUFACTURER_DEFAULT,
    MANUFACTURER_MAP,
    ATTRIBUTION,
    ATTR_IMEI,
    ATTR_SERIAL,
    ATTR_WORKING,
    ATTR_ERROR,
    ATTR_CONNECTED,
    ATTR_LAST_COMM,
    ATTR_LAST_SEEN,
    ATTR_LAST_PULL,
    ROBOT_STATES,
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

        self._imei = imei
        self._name = name
        self._serial = None
        self._manufacturer = MANUFACTURER_DEFAULT
        self._model = None
        self._sw_version = None

        if entity_key:
            self._unique_id = slugify(f"{self._imei}_{self._name}_{entity_key}")
        else:
            self._unique_id = slugify(f"{self._imei}_{self._name}")

        self._state = 0
        self._working = False
        self._error = 0
        self._available = True
        self._location = {
            ATTR_LATITUDE: None,
            ATTR_LONGITUDE: None,
        }
        self._connected = False
        self._last_communication = None
        self._last_seen = None
        self._last_pull = None

        self._additional_extra_state_attributes = {}

        self.entity_id = f"{entity_type}.{self._unique_id}"

    def _get_attributes(self) -> dict:
        """Get the mower attributes of the current mower."""
        return self.coordinator.data[self._imei]

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
        return self._available

    @property
    def device_info(self):
        """Return the device info."""
        return {
            ATTR_IDENTIFIERS: {
                (DOMAIN, self._imei)
            },
            ATTR_NAME: self._name,
            ATTR_MANUFACTURER: self._manufacturer,
            ATTR_MODEL: self._model,
            ATTR_SW_VERSION: self._sw_version,
        }

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return axtra attributes."""
        _extra_state_attributes = {
            ATTR_IMEI: self._imei,
            ATTR_CONNECTED: self._connected,
            ATTR_LAST_COMM: self._last_communication,
            ATTR_LAST_SEEN: self._last_seen,
            ATTR_LAST_PULL: self._last_pull,
        }
        _extra_state_attributes.update(self._additional_extra_state_attributes)

        return _extra_state_attributes

    async def async_update(self) -> None:
        """Peform async_update."""
        self._update_handler()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_handler()
        self.async_write_ha_state()

    def _update_handler(self):
        """Handle updated data."""
        if self._imei not in self.coordinator.data:
            return None
        # Get this mower entity from coordinator
        mower = self.coordinator.data[self._imei]
        self._state = mower[ATTR_STATE] if mower[ATTR_STATE] < len(ROBOT_STATES) else 0
        self._working = mower[ATTR_WORKING]
        self._error = mower[ATTR_ERROR]
        self._available = self._state > 0
        if mower[ATTR_LOCATION] is not None:
            self._location = mower[ATTR_LOCATION]
        self._serial = mower[ATTR_SERIAL]
        if (
            self._serial is not None
            and len(self._serial) > 5
        ):
            if self._serial[0:2] in MANUFACTURER_MAP:
                self._manufacturer = MANUFACTURER_MAP[self._serial[0:2]]
            self._model = self._serial[0:6]
        self._sw_version = mower[ATTR_SW_VERSION]

        self._connected = mower[ATTR_CONNECTED]
        self._last_communication = mower[ATTR_LAST_COMM]
        self._last_seen = mower[ATTR_LAST_SEEN]
        self._last_pull = mower[ATTR_LAST_PULL]
        self._update_extra_state_attributes()
