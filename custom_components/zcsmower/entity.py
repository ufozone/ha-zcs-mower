"""ZCS Lawn Mower Robot entity."""
from __future__ import annotations

from datetime import datetime

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
from homeassistant.helpers.device_registry import (
    DeviceEntryType,
    DeviceInfo,
)
from homeassistant.helpers.entity import (
    EntityCategory,
    EntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    ATTR_IMEI,
    ATTR_SERIAL_NUMBER,
    ATTR_ERROR,
    ATTR_AVAILABLE,
    ATTRIBUTION,
    MANUFACTURER_DEFAULT,
)
from .coordinator import ZcsDataUpdateCoordinator


class ZcsMowerEntity(CoordinatorEntity):
    """ZCS Lawn Mower Robot entity class."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsDataUpdateCoordinator,
        entity_type: str,
        entity_description: EntityDescription,
        imei: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self.hass = hass
        self.config_entry = config_entry
        self.entity_description = entity_description

        self._imei = imei
        self._name = self._get_attribute(ATTR_NAME, imei)
        self._entity_key = entity_description.key
        if self._entity_key:
            self._unique_id = slugify(f"mower_{imei}_{self._entity_key}")
        else:
            self._unique_id = slugify(f"mower_{imei}")
        self._additional_extra_state_attributes = {}

        self.entity_id = f"{entity_type}.{self._unique_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, self._imei)
            },
            #connections={
            #    (ATTR_IMEI, self._imei)
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
        """Return the unique ID of the entity."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # If hibernation is enabled, all NOT config and diagnostic entities are not available
        if self.coordinator.hibernation_enable and self.entity_description.entity_category not in [EntityCategory.CONFIG, EntityCategory.DIAGNOSTIC]:
            return False

        return self._get_attribute(ATTR_AVAILABLE, False)

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra attributes."""
        _extra_state_attributes = self._additional_extra_state_attributes
        _extra_state_attributes.update(
            {
                ATTR_IMEI: self._imei,
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


class ZcsConfigEntity(CoordinatorEntity):
    """ZCS Configuration entity class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsDataUpdateCoordinator,
        entity_type: str,
        entity_description: EntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self.hass = hass
        self.config_entry = config_entry
        self.entity_description = entity_description

        self._name = config_entry.title
        self._entity_key = entity_description.key
        self._unique_id = slugify(f"{self._entity_key}_{config_entry.entry_id}")

        self.entity_id = f"{entity_type}.{self._unique_id}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={
                (DOMAIN, config_entry.entry_id)
            },
            name=config_entry.title,
            manufacturer=MANUFACTURER_DEFAULT,
        )
        self._config_key = entity_description.config_key

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return self._unique_id
