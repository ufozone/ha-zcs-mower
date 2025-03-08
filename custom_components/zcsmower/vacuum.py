"""ZCS Lawn Mower Robot vacuum platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_STATE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.vacuum import (
    ATTR_STATUS,
    StateVacuumEntity,
    StateVacuumEntityDescription,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.helpers.entity import Entity

from .const import (
    LOGGER,
    DOMAIN,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerRobotEntity

ROBOT_SUPPORTED_FEATURES = (
    VacuumEntityFeature.STOP
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.LOCATE
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.STATUS
    | VacuumEntityFeature.START
    | VacuumEntityFeature.MAP
)
ROBOT_ENTITY_DESCRIPTIONS = (
    StateVacuumEntityDescription(
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
    coordinator = config_entry.runtime_data
    async_add_entities(
        [
            ZcsMowerRobotVacuumEntity(
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


class ZcsMowerRobotVacuumEntity(ZcsMowerRobotEntity, StateVacuumEntity):
    """Representation of a ZCS Lawn Mower Robot vacuum."""

    _attr_name = None
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: StateVacuumEntityDescription,
        imei: str,
    ) -> None:
        """Initialize the vacuum class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            entity_type="vacuum",
            entity_description=entity_description,
            imei=imei,
        )
        self._attr_supported_features = ROBOT_SUPPORTED_FEATURES

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        self._additional_extra_state_attributes = {
            ATTR_STATUS: self._get_localized_status(),
        }

    @property
    def activity(self) -> VacuumActivity | None:
        """Return the state of the lawn mower."""
        if self._get_attribute(ATTR_STATE) in ("work", "gotoarea", "bordercut", "mapping_started"):
            return VacuumActivity.CLEANING
        if self._get_attribute(ATTR_STATE) == "charge":
            return VacuumActivity.DOCKED
        if self._get_attribute(ATTR_STATE) == "pause":
            return VacuumActivity.PAUSED
        if self._get_attribute(ATTR_STATE) in ("gotostation", "mapping_ended"):
            return VacuumActivity.RETURNING
        if self._get_attribute(ATTR_STATE) == "work_standby":
            return VacuumActivity.IDLE
        return VacuumActivity.ERROR

    @property
    def error(self) -> str | None:
        """Define an error message if the vacuum is in STATE_ERROR."""
        if self._get_attribute(ATTR_STATE) == "fail":
            return self._get_localized_status()
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
