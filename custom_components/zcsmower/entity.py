"""ZCS Lawn Mower Robot entity."""
from __future__ import annotations

from datetime import (
    datetime,
)

from homeassistant.core import (
    callback,
    HomeAssistant,
)
from homeassistant.const import (
    ATTR_NAME,
    ATTR_STATE,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SW_VERSION,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    ATTR_IMEI,
    ATTR_SERIAL_NUMBER,
    ATTR_ERROR,
    ATTR_AVAILABLE,
    ATTR_CONNECTED,
    ATTR_LAST_COMM,
    ATTR_LAST_SEEN,
    ATTR_LAST_PULL,
    ATTR_NEXT_PULL,
    ATTRIBUTION,
)
from .coordinator import ZcsMowerDataUpdateCoordinator


class ZcsMowerEntity(CoordinatorEntity):
    """ZCS Lawn Mower Robot class."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        imei: str,
        entity_type: str,
        entity_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self.hass = hass
        self.config_entry = config_entry

        self._imei = imei
        self._name = self._get_attribute(ATTR_NAME, imei)
        self._entity_type = entity_type
        self._entity_key = entity_key
        if entity_key:
            self._unique_id = slugify(f"mower_{imei}_{entity_key}")
        else:
            self._unique_id = slugify(f"mower_{imei}")
        self._additional_extra_state_attributes = {}

        self.entity_id = f"{entity_type}.{self._unique_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, self._imei)
            },
            #connections={
            #    ("gsm", self._imei)
            #},
            name=self._name,
            model=self._get_attribute(ATTR_MODEL),
            manufacturer=self._get_attribute(ATTR_MANUFACTURER),
            sw_version=self._get_attribute(ATTR_SW_VERSION),
            serial_number=self._get_attribute(ATTR_SERIAL_NUMBER),
            suggested_area="Garden",
        )

    def _get_attribute(
        self,
        attr: str,
        default_value: any | None = None,
    ) -> any:
        """Get attribute of the current mower."""
        return self.coordinator.data.get(self._imei, {}).get(attr, default_value)

    def _get_next_pull(
        self,
    ) -> datetime | None:
        """Get attribute of the current mower."""
        return self.coordinator.next_pull

    def _get_localized_status(
        self,
    ) -> str:
        """Get localized status of the current mower."""
        assert self.platform
        if self._get_attribute(ATTR_STATE) == "fail":
            _status = self._get_attribute(ATTR_ERROR, "unknown")
            _name_translation_key = (
                f"component.{self.platform.platform_name}.entity"
                f".sensor.error.state.{_status}"
            )
        else:
            _status = self._get_attribute(ATTR_STATE, "unknown")
            _name_translation_key = (
                f"component.{self.platform.platform_name}.entity"
                f".sensor.state.state.{_status}"
            )
        # HA > 2023.6.3
        if hasattr(self.platform, "platform_translations"):
            _localized_status: str = self.platform.platform_translations.get(_name_translation_key, _status)
        # HA <= 2023.6.3
        elif hasattr(self.platform, "entity_translations"):
            _localized_status: str = self.platform.entity_translations.get(_name_translation_key, _status)
        # HA < 2023.4.0
        else:
            _localized_status = _status
        return _localized_status

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        self._additional_extra_state_attributes = {}

    def _update_handler(self) -> None:
        """Handle updated data."""
        self._update_extra_state_attributes()

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._get_attribute(ATTR_AVAILABLE, False)

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra attributes."""
        _extra_state_attributes = self._additional_extra_state_attributes
        _extra_state_attributes.update(
            {
                ATTR_IMEI: self._imei,
                ATTR_CONNECTED: self._get_attribute(ATTR_CONNECTED),
                ATTR_LAST_COMM: self._get_attribute(ATTR_LAST_COMM),
                ATTR_LAST_SEEN: self._get_attribute(ATTR_LAST_SEEN),
                ATTR_LAST_PULL: self._get_attribute(ATTR_LAST_PULL),
                ATTR_NEXT_PULL: self._get_next_pull(),
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
