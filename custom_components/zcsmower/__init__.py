"""ZCS Lawn Mower Robot integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import async_get
#from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    LOGGER,
    DOMAIN,
    PLATFORMS,
    API_BASE_URI,
    API_APP_TOKEN,
    CONF_CLIENT_KEY,
    CONF_IMEI,
    CONF_MOWERS,
    SERVICE_SET_PROFILE,
    SERVICE_SET_PROFILE_SCHEMA,
    SERVICE_WORK_UNTIL,
    SERVICE_WORK_UNTIL_SCHEMA,
    SERVICE_BORDER_CUT,
    SERVICE_BORDER_CUT_SCHEMA,
    SERVICE_CHARGE_UNTIL,
    SERVICE_CHARGE_UNTIL_SCHEMA,
    SERVICE_TRACE_POSITION,
    SERVICE_TRACE_POSITION_SCHEMA,
)
from .api import ZcsMowerApiClient
from .coordinator import ZcsMowerDataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up  ZCS Lawn Mower Robot component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator = ZcsMowerDataUpdateCoordinator(
        mowers=entry.options[CONF_MOWERS],
        hass=hass,
        client=ZcsMowerApiClient(
            session=async_get_clientsession(hass),
            options={
                "endpoint": API_BASE_URI,
                "app_id": entry.data[CONF_CLIENT_KEY],
                "app_token": API_APP_TOKEN,
                "thing_key": entry.data[CONF_CLIENT_KEY]
            }
        ),
    )
    await coordinator.async_config_entry_first_refresh()

    # Forward the setup to platforms.
    #hass.async_create_task(
    #    hass.config_entries.async_forward_entry_setup(entry, PLATFORMS)
    #)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    async def async_handle_set_profile(call) -> None:
        """Handle the service call."""
        LOGGER.debug(call.data)

    async def async_handle_work_until(call) -> None:
        """Handle the service call."""
        LOGGER.debug(call.data)
        area = call.data.get("area")
        LOGGER.debug(area)

    async def async_handle_border_cut(call) -> None:
        """Handle the service call."""
        LOGGER.debug(call.data)

    async def async_handle_charge_until(call) -> None:
        """Handle the service call."""
        LOGGER.debug(call.data)

    async def async_handle_trace_position(call) -> None:
        """Handle the service call."""
        LOGGER.debug(call.data)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PROFILE,
        async_handle_set_profile,
        schema=SERVICE_SET_PROFILE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_WORK_UNTIL,
        async_handle_work_until,
        schema=SERVICE_WORK_UNTIL_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BORDER_CUT,
        async_handle_border_cut,
        schema=SERVICE_BORDER_CUT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CHARGE_UNTIL,
        async_handle_charge_until,
        schema=SERVICE_CHARGE_UNTIL_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TRACE_POSITION,
        async_handle_trace_position,
        schema=SERVICE_TRACE_POSITION_SCHEMA
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove config entry from domain.
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

async def async_setup_services(hass):
    def call_service(service, targets, data):
        LOGGER.debug(service)
        LOGGER.debug(targets)
        LOGGER.debug(data)
        #browsers = hass.data[DOMAIN][DATA_BROWSERS]

        #if isinstance(targets, str):
        #    targets = [targets]

        # If no targets were specified, send to all browsers
        #if len(targets) == 0:
        #    targets = browsers.keys()

        #for target in targets:
        #    if target not in browsers:
        #        continue
        #    browser = browsers[target]
        #    hass.create_task(browser.send(service, **data))

    def handle_service(call):
        service = call.service
        data = {**call.data}
        device_ids = data.pop("device_id", [])
        if isinstance(device_ids, str):
            device_ids = [device_ids]
        device_ids = set(device_ids)
        
        LOGGER.debug(service)
        LOGGER.debug(data)
        LOGGER.debug(device_ids)
        
        dr = async_get(hass)
        for device_id in device_ids:
             device = dr.async_get(device_id)
             if not device:
                 continue
             identifiers = list(device.identifiers)[0]
             
             LOGGER.debug(DOMAIN)
             
             if identifiers[1] is not DOMAIN:
                 continue
             imei = identifiers[1]
             LOGGER.debug(DOMAIN)
             LOGGER.debug(device)
             LOGGER.debug(imei)

        #call_service(service, browsers, data)

    for service in SERVICES:
        hass.services.async_register(DOMAIN, service, handle_service)