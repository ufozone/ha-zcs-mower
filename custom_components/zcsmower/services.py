"""Services Registry for ZCS Lawn Mower Robot integration."""

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
)
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_LOCATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
)
from homeassistant.helpers.device_registry import async_get
from homeassistant.helpers.service import (
    verify_domain_control,
)

from .const import (
    DOMAIN,
    SERVICE_SET_PROFILE,
    SERVICE_SET_PROFILE_SCHEMA,
    SERVICE_WORK_NOW,
    SERVICE_WORK_NOW_SCHEMA,
    SERVICE_WORK_FOR,
    SERVICE_WORK_FOR_SCHEMA,
    SERVICE_WORK_UNTIL,
    SERVICE_WORK_UNTIL_SCHEMA,
    SERVICE_BORDER_CUT,
    SERVICE_BORDER_CUT_SCHEMA,
    SERVICE_CHARGE_NOW,
    SERVICE_CHARGE_NOW_SCHEMA,
    SERVICE_CHARGE_FOR,
    SERVICE_CHARGE_FOR_SCHEMA,
    SERVICE_CHARGE_UNTIL,
    SERVICE_CHARGE_UNTIL_SCHEMA,
    SERVICE_TRACE_POSITION,
    SERVICE_TRACE_POSITION_SCHEMA,
    SERVICE_KEEP_OUT,
    SERVICE_KEEP_OUT_SCHEMA,
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up ZCS Lawn Mower Robot services."""
    if hass.services.async_services().get(DOMAIN):
        return

    @verify_domain_control(hass, DOMAIN)
    async def async_handle_service(call: ServiceCall) -> None:
        """Call correct HomematicIP Cloud service."""
        service = call.service
        data = {**call.data}
        device_ids = data.pop(CONF_DEVICE_ID, [])
        if isinstance(device_ids, str):
            device_ids = [device_ids]
        device_ids = set(device_ids)

        targets = {}
        dr = async_get(hass)
        for device_id in device_ids:
            device = dr.async_get(device_id)
            if not device:
                continue
            identifiers = list(device.identifiers)[0]
            if identifiers[0] != DOMAIN:
                continue
            config_entry_id = list(device.config_entries)[0]
            if config_entry_id not in hass.data[DOMAIN]:
                continue
            targets[identifiers[1]] = hass.data[DOMAIN][config_entry_id]

        if service == SERVICE_SET_PROFILE:
            await _async_set_profile(hass, targets, data)
        elif service == SERVICE_WORK_NOW:
            await _async_work_now(hass, targets, data)
        elif service == SERVICE_WORK_FOR:
            await _async_work_for(hass, targets, data)
        elif service == SERVICE_WORK_UNTIL:
            await _async_work_until(hass, targets, data)
        elif service == SERVICE_BORDER_CUT:
            await _async_border_cut(hass, targets, data)
        elif service == SERVICE_CHARGE_NOW:
            await _async_charge_now(hass, targets, data)
        elif service == SERVICE_CHARGE_FOR:
            await _async_charge_for(hass, targets, data)
        elif service == SERVICE_CHARGE_UNTIL:
            await _async_charge_until(hass, targets, data)
        elif service == SERVICE_TRACE_POSITION:
            await _async_trace_position(hass, targets, data)
        elif service == SERVICE_KEEP_OUT:
            await _async_keep_out(hass, targets, data)

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_SET_PROFILE,
        service_func=async_handle_service,
        schema=SERVICE_SET_PROFILE_SCHEMA
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_WORK_NOW,
        service_func=async_handle_service,
        schema=SERVICE_WORK_NOW_SCHEMA
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_WORK_FOR,
        service_func=async_handle_service,
        schema=SERVICE_WORK_FOR_SCHEMA
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_WORK_UNTIL,
        service_func=async_handle_service,
        schema=SERVICE_WORK_UNTIL_SCHEMA
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_BORDER_CUT,
        service_func=async_handle_service,
        schema=SERVICE_BORDER_CUT_SCHEMA
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_CHARGE_NOW,
        service_func=async_handle_service,
        schema=SERVICE_CHARGE_NOW_SCHEMA
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_CHARGE_FOR,
        service_func=async_handle_service,
        schema=SERVICE_CHARGE_FOR_SCHEMA
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_CHARGE_UNTIL,
        service_func=async_handle_service,
        schema=SERVICE_CHARGE_UNTIL_SCHEMA
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_TRACE_POSITION,
        service_func=async_handle_service,
        schema=SERVICE_TRACE_POSITION_SCHEMA
    )
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_KEEP_OUT,
        service_func=async_handle_service,
        schema=SERVICE_KEEP_OUT_SCHEMA
    )

async def _async_set_profile(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_set_profile(
                imei,
                data.get("profile"),
            )
        )

async def _async_work_now(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_work_now(
                imei,
                data.get("area"),
            )
        )

async def _async_work_for(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_work_for(
                imei,
                data.get("duration"),
                data.get("area"),
            )
        )

async def _async_work_until(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_work_until(
                imei,
                data.get("hours"),
                data.get("minutes"),
                data.get("area"),
            )
        )

async def _async_border_cut(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_border_cut(
                imei,
            )
        )

async def _async_charge_now(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_charge_now(
                imei,
            )
        )

async def _async_charge_for(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_charge_for(
                imei,
                data.get("duration"),
            )
        )

async def _async_charge_until(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_charge_until(
                imei,
                data.get("hours"),
                data.get("minutes"),
                data.get("weekday"),
            )
        )

async def _async_trace_position(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_trace_position(
                imei,
            )
        )

async def _async_keep_out(
    hass: HomeAssistant,
    targets: dict[str, any],
    data: dict[str, any],
) -> None:
    """Handle the service call."""
    for imei, coordinator in targets.items():
        hass.async_create_task(
            coordinator.async_keep_out(
                imei,
                data.get(CONF_LOCATION, {}).get(CONF_LATITUDE),
                data.get(CONF_LOCATION, {}).get(CONF_LONGITUDE),
                data.get(CONF_LOCATION, {}).get(CONF_RADIUS),
                data.get("hours", None),
                data.get("minutes", None),
                data.get("index", None),
            )
        )
