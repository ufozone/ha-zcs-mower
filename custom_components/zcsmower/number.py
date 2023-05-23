"""ZCS Lawn Mower Robot number platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTime,
)
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.helpers.entity import Entity

from .const import (
    LOGGER,
    DOMAIN,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ENTITY_DESCRIPTIONS = (
    NumberEntityDescription(
        key="work_for",
        name="Work for",
        icon="mdi:clock-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        translation_key="_",
    ),
    NumberEntityDescription(
        key="charge_for",
        name="Charge for",
        icon="mdi:clock-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        translation_key="_",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup numbers from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            ZcsMowerDurationNumberEntity(
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


class ZcsMowerNumberEntity(ZcsMowerEntity, NumberEntity):
    """Representation of a ZCS Lawn Mower Robot number."""

    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: NumberEntityDescription,
        imei: str,
        name: str,
    ) -> None:
        """Initialize the number class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            imei=imei,
            name=name,
            entity_type="number",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description

class ZcsMowerDurationNumberEntity(ZcsMowerNumberEntity):
    """Representation of a ZCS Lawn Mower Robot number for command with duration."""

    _attr_native_value: float = 60
    _attr_native_min_value: float = 1
    _attr_native_max_value: float = 1439
    _attr_native_step: float = 1

    async def async_set_native_value(self, value: float) -> None:
        """Change the value."""
        duration = int(value)
        await getattr(self.coordinator, f"async_{self._entity_key}")(
            imei=self._imei,
            duration=duration,
        )
