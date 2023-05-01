"""ZCS Lawn Mower Robot entity"""
from __future__ import annotations

from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    LOGGER,
    DOMAIN,
    MANUFACTURER,
    ATTR_IMEI,
)
from .coordinator import ZcsMowerDataUpdateCoordinator


class ZcsMowerEntity(CoordinatorEntity):
    """BlueprintEntity class."""

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

        self.coordinator = coordinator
        self.client = coordinator.client
        
        self._imei = imei
        self._name = name
        self._serial = None
        self._serial = None
        self._unique_id = slugify(f"{self._imei}_{self._name}")
        
        self.entity_id = f"{entity_type}.{self._unique_id}"
        
        self._state = 0
        self._available = True
        self.attrs: dict[str, Any] = {
            ATTR_IMEI: self._imei,
        }

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the icon of the entity."""
        return "mdi:robot-mower"

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
            "identifiers": {
                (DOMAIN, self._imei)
            },
            "name": self._name,
            "model": self._model,
            "manufacturer": MANUFACTURER,
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.attrs

    async def async_update(self) -> None:
        
        # TODO
        LOGGER.debug("async_update")
        LOGGER.debug(self._name)
        
        self._update_handler();
    
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        
        # TODO
        LOGGER.debug("_handle_coordinator_update")
        LOGGER.debug(self._name)
        
        self._update_handler();
        self.async_write_ha_state()
    
    def _update_handler(self):
        if self._imei in self.coordinator.data:
            robot = self.coordinator.data[self._imei]
            self._state = robot["state"]
            self._location = robot["location"]
            self._serial = robot["serial"]
            if len(self._serial) > 0:
                self._model = self._serial[0:8]
