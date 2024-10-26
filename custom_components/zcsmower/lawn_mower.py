"""ZCS Lawn Mower Robot lawn mower platform."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_STATE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityEntityDescription,
    LawnMowerEntityFeature,
)
from homeassistant.helpers.entity import Entity

from .const import (
    LOGGER,
    DOMAIN,
    ATTR_STATUS,
)
from .coordinator import ZcsDataUpdateCoordinator
from .entity import ZcsRobotEntity

ROBOT_SUPPORTED_FEATURES = (
    LawnMowerEntityFeature.START_MOWING
    | LawnMowerEntityFeature.DOCK
)
ROBOT_ENTITY_DESCRIPTIONS = (
    LawnMowerEntityEntityDescription(
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
            ZcsRobotLawnMowerEntity(
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


class ZcsRobotLawnMowerEntity(ZcsRobotEntity, LawnMowerEntity):
    """Representation of a ZCS Lawn Mower Robot entity."""

    _attr_name = None

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsDataUpdateCoordinator,
        entity_description: LawnMowerEntityEntityDescription,
        imei: str,
    ) -> None:
        """Initialize the lawn mower class."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            entity_type="lawn_mower",
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
    def state(self) -> str:
        """Return the state of the lawn mower."""
        if self._get_attribute(ATTR_STATE) in ("work", "gotoarea", "gotostation", "bordercut", "mapping_started", "mapping_ended"):
            return LawnMowerActivity.MOWING
        if self._get_attribute(ATTR_STATE) == "charge":
            return LawnMowerActivity.DOCKED
        if self._get_attribute(ATTR_STATE) in ("pause", "work_standby"):
            return LawnMowerActivity.PAUSED
        return LawnMowerActivity.ERROR

    @property
    def error(self) -> str | None:
        """Define an error message if the vacuum is in STATE_ERROR."""
        if self._get_attribute(ATTR_STATE) == "fail":
            return self._get_localized_status()
        return None

    async def async_start_mowing(self) -> None:
        """Start or resume the mowing task."""
        await self.coordinator.async_work_now(
            imei=self._imei,
        )

    async def async_dock(self) -> None:
        """Command the lawn mower return to station until next schedule."""
        await self.coordinator.async_charge_now(
            imei=self._imei,
        )

    async def async_pause(self) -> None:
        """Not supported."""
        LOGGER.warning("Method %s.lawn_mower.pause is not supported.", DOMAIN)
