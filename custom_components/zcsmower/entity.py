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
        mower: dict[str, str],
        entity_type: str,
        entity_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.client = coordinator.client
        
        self._imei = mower["imei"]
        self._name = mower.get("name", self._imei)
        
        self._attr_unique_id = slugify(f"{self._name}_{entity_key}")
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, self.unique_id)
            },
            name=self._name,
            model=None,
            manufacturer=MANUFACTURER,
        )
        self.entity_id = f"{entity_type}.{self._attr_unique_id}"
        
        self._state = 0
        self._available = True
        self.attrs: dict[str, Any] = {
            ATTR_IMEI: self._imei,
        }
        
        # TODO
        LOGGER.error("Mower")
        LOGGER.error(self._imei)
        LOGGER.error(self._name)

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the icon of the entity."""
        return "mdi:robot-mower"

    #@property
    #def unique_id(self) -> str:
    #    """Return the unique ID of the sensor."""
    #    return self._attr_unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.attrs

    async def async_update(self) -> None:
        """Update all sensors."""
        LOGGER.error("async_update")
        LOGGER.error(self._name)
