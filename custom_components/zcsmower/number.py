"""ZCS Lawn Mower Robot number platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    UnitOfTime,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.helpers.entity import Entity

from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerRobotEntity

ROBOT_ENTITY_DESCRIPTIONS = (
    NumberEntityDescription(
        key="work_for",
        icon="mdi:clock-outline",
        native_max_value=1439,
        native_min_value=1,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        translation_key="work_for",
    ),
    NumberEntityDescription(
        key="charge_for",
        icon="mdi:clock-outline",
        native_max_value=10079,
        native_min_value=1,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        translation_key="charge_for",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup numbers from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        [
            ZcsMowerRobotDurationNumberEntity(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                entity_description=entity_description,
                imei=imei,
            )
            for imei in coordinator.mowers
            for entity_description in ROBOT_ENTITY_DESCRIPTIONS
        ],
        update_before_add=True,
    )


class ZcsMowerRobotNumberEntity(ZcsMowerRobotEntity, NumberEntity):
    """Representation of a ZCS Lawn Mower Robot number."""

    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: NumberEntityDescription,
        imei: str,
    ) -> None:
        """Initialize the number class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            entity_type="number",
            entity_description=entity_description,
            imei=imei,
        )

class ZcsMowerRobotDurationNumberEntity(ZcsMowerRobotNumberEntity):
    """Representation of a ZCS Lawn Mower Robot number for command with duration."""

    _attr_native_value: float = 60

    async def async_set_native_value(self, value: float) -> None:
        """Change the value."""
        duration = int(value)
        await getattr(self.coordinator, f"async_{self._entity_key}")(
            imei=self._imei,
            duration=duration,
        )
