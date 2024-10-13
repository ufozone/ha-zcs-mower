"""ZCS Lawn Mower Robot switch platform."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.helpers.entity import (
    Entity,
    EntityCategory,
)

from .const import (
    CONF_HIBERNATION_ENABLE,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsConfigEntity


@dataclass(frozen=True, kw_only=True)
class ZcsConfigSwitchEntityDescription(SwitchEntityDescription):
    """Describes ZCS Lawn Mower Robot switch entity."""

    config_key: str


ENTITY_DESCRIPTIONS = (
    ZcsConfigSwitchEntityDescription(
        key="mower_hibernation",
        translation_key="hibernation",
        entity_category=EntityCategory.CONFIG,
        config_key=CONF_HIBERNATION_ENABLE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup sensors from a config entry created in the integrations UI."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        [
            ZcsConfigSwitchEntity(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                entity_description=entity_description,
            )
            for entity_description in ENTITY_DESCRIPTIONS
        ],
        update_before_add=True,
    )


class ZcsConfigSwitchEntity(ZcsConfigEntity, SwitchEntity):
    """Representation of a ZCS configuration switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            entity_type="switch",
            entity_description=entity_description,
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return bool(self.config_entry.options.get(self._config_key, False))

    async def async_turn_on(self, **kwargs: any) -> None:
        """Turn the entity on."""
        await self.coordinator.async_set_entry_option(
            self._config_key,
            True,
        )

    async def async_turn_off(self, **kwargs: any) -> None:
        """Turn the entity off."""
        await self.coordinator.async_set_entry_option(
            self._config_key,
            False,
        )
