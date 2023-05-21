"""ZCS Lawn Mower Robot binary sensor platform."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_STATE,
)
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
    ATTR_ERROR,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ROBOT_SUPPORTED_FEATURES = (
    VacuumEntityFeature.STOP
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.LOCATE
    | VacuumEntityFeature.STATE
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
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: VacuumEntityDescription,
        imei: str,
        name: str,
    ) -> None:
        """Initialize the vacuum class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            imei=imei,
            name=name,
            entity_type="vacuum",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description
        self._attr_supported_features = ROBOT_SUPPORTED_FEATURES

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        if self._get_attribute(ATTR_STATE) == "fail":
            _attr_status = self._get_attribute(ATTR_ERROR, "unknown")
        else:
            _attr_status = self._get_attribute(ATTR_STATE)
        # TODO: Currently no way to map this status, but it would be the best way to
        #       present detailed error messages.
        self._additional_extra_state_attributes = {
            ATTR_STATUS: _attr_status,
        }

    @property
    def state(self) -> str:
        """Return the state of the lawn mower."""
        if self._get_attribute(ATTR_STATE) in ("work", "gotoarea", "bordercut"):
            return STATE_CLEANING
        if self._get_attribute(ATTR_STATE) == "charge":
            return STATE_DOCKED
        if self._get_attribute(ATTR_STATE) == "pause":
            return STATE_PAUSED
        if self._get_attribute(ATTR_STATE) == "gotostation":
            return STATE_RETURNING
        if self._get_attribute(ATTR_STATE) == "work_standby":
            return STATE_IDLE
        return STATE_ERROR

    @property
    def error(self) -> str:
        """Define an error message if the vacuum is in STATE_ERROR."""
        if self._get_attribute(ATTR_STATE) == "fail":
            return self._get_attribute(ATTR_ERROR, "unknown")
        return None

    async def async_start(self) -> None:
        """Start or resume the mowing task."""
        await self.coordinator.async_work_now(
            imei=self._imei,
        )

    async def async_pause(self) -> None:
        """Not supported."""
        LOGGER.warning("Method %s.pause is not supported.", DOMAIN)

    async def async_stop(self, **kwargs) -> None:
        """Command the lawn mower return to station until next schedule."""
        await self.async_return_to_base(**kwargs)

    async def async_return_to_base(self, **kwargs) -> None:
        """Command the lawn mower return to station until next schedule."""
        await self.coordinator.async_charge_now(
            imei=self._imei,
        )

    async def async_clean_spot(self, **kwargs: any) -> None:
        """Not supported."""
        LOGGER.warning("Method %s.clean_spot is not supported.", DOMAIN)

    async def async_locate(self, **kwargs: any) -> None:
        """Locate the lawn mower."""
        await self.coordinator.async_trace_position(
            imei=self._imei,
        )

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: any) -> None:
        """Not supported."""
        LOGGER.warning("Method %s.set_fan_speed is not supported.", DOMAIN)

    async def async_send_command(
        self,
        command: str,
        params: dict[str, any] | list[any] | None = None,
        **kwargs: any
    ) -> None:
        """Send a command to lawn mower."""
        await self.coordinator.async_custom_command(
            imei=self._imei,
            command=command,
            params=params,
        )
