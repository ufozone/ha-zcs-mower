"""ZCS Lawn Mower Robot button platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.helpers.entity import Entity

from .const import (
    DOMAIN,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ENTITY_DESCRIPTIONS = (
    ButtonEntityDescription(
        key="work_now",
        icon="mdi:state-machine",
        translation_key="work_now",
        device_class=ButtonDeviceClass.UPDATE,
    ),
    ButtonEntityDescription(
        key="charge_now",
        icon="mdi:ev-station",
        translation_key="charge_now",
        device_class=ButtonDeviceClass.UPDATE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup buttons from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            ZcsMowerButton(
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


class ZcsMowerButton(ZcsMowerEntity, ButtonEntity):
    """Representation of a ZCS Lawn Mower Robot button."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: ButtonEntityDescription,
        imei: str,
        name: str,
    ) -> None:
        """Initialize the button class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            imei=imei,
            name=name,
            entity_type="button",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description

    async def async_press(self) -> None:
        """Press the button."""
        await getattr(self.coordinator, f"async_{self._entity_key}")(
            imei=self._imei,
        )
