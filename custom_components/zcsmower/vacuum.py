"""ZCS Lawn Mower Robot binary sensor platform."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.vacuum import (
    ATTR_STATUS,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_PAUSED,
    STATE_IDLE,
    STATE_RETURNING,
    STATE_ERROR,
    StateVacuumEntity,
    VacuumEntityDescription,
    VacuumEntityFeature,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from .const import (
    LOGGER,
    DOMAIN,
    ROBOT_STATES,
    ROBOT_ERRORS,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ROBOT_SUPPORTED_FEATURES = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.LOCATE
    | VacuumEntityFeature.STATUS
    | VacuumEntityFeature.START
)
ENTITY_DESCRIPTIONS = (
    VacuumEntityDescription(
        key="",
        icon="mdi:robot-mower",
        translation_key="mower",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup sensors from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            ZcsMowerVacuum(
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


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor binary platform."""
    # TODO
    LOGGER.debug("async_setup_platform")


class ZcsMowerVacuum(ZcsMowerEntity, StateVacuumEntity):
    """Representation of a ZCS Lawn Mower Robot vacuum."""

    def __init__(
        self,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: VacuumEntityDescription,
        imei: str,
        name: str,
    ) -> None:
        """Initialize the vacuum class."""
        super().__init__(
            coordinator=coordinator,
            imei=imei,
            name=name,
            entity_type="vacuum",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description
        self._attr_supported_features = ROBOT_SUPPORTED_FEATURES

    def update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        self._additional_extra_state_attributes = {
            ATTR_STATUS: ROBOT_STATES[self._state]["name"],
        }

    @property
    def state(self) -> str:
        """Return the state of the lawn mower."""
        if self._state in (2, 7, 8):
            return STATE_CLEANING
        if self._state == 1:
            return STATE_DOCKED
        if self._state == 3:
            return STATE_PAUSED
        if self._state == 6:
            return STATE_RETURNING
        if self._state == 11:
            return STATE_IDLE
        return STATE_ERROR

    @property
    def error(self) -> str:
        """Define an error message if the vacuum is in STATE_ERROR."""
        if self._state == 4:
            mower_attributes = AutomowerEntity.get_mower_attributes(self)
            return ROBOT_ERRORS.get(self._error, "unknown")
        return None
