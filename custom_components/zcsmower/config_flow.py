"""Adds config flow for Ambrogio."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from homeassistant.core import callback
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
    CONN_CLASS_CLOUD_POLL,
)
from homeassistant.const import (
    CONF_NAME
)
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get,
)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    LOGGER,
    DOMAIN,
    PLATFORMS,
    API_BASE_URI,
    API_APP_TOKEN,
    CONF_CLIENT_KEY,
    CONF_IMEI,
    CONF_MOWERS,
)
from .api import (
    ZcsMowerApiClient,
    ZcsMowerApiAuthenticationError,
    ZcsMowerApiCommunicationError,
    ZcsMowerApiError,
)


async def validate_auth(client_key: str, hass: core.HomeAssistant) -> None:
    """
    Validates client key.

    Raises a ValueError if the client key is invalid.
    """
    if len(client_key) != 28:
        raise ValueError
    
    client = ZcsMowerApiClient(
        session=async_create_clientsession(hass),
        options={
            "endpoint": API_BASE_URI,
            "app_id": client_key,
            "app_token": API_APP_TOKEN,
            "thing_key": client_key
        }
    )
    await client.check_api_client()

async def validate_imei(imei: str, client_key: str, hass: core.HassJob) -> None:
    """
    Validates a lawn mower IMEI.
    
    Raises a ValueError if the IMEI is invalid.
    """
    if len(imei) != 15:
        raise ValueError
    
    client = ZcsMowerApiClient(
        session=async_get_clientsession(hass),
        options={
            "endpoint": API_BASE_URI,
            "app_id": client_key,
            "app_token": API_APP_TOKEN,
            "thing_key": client_key
        }
    )
    await client.check_robot(
        imei=imei
    )

class ZcsMowerConfigFlow(ConfigFlow, domain=DOMAIN):
    """ZCS Lawn Mower config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL
    
    data: Optional[dict[str, Any]]
    
    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Invoked when a user initiates a flow via the user interface."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(user_input[CONF_CLIENT_KEY], self.hass)
            except ZcsMowerApiAuthenticationError as exception:
                LOGGER.error(exception)
                errors["base"] = "auth"
            except ZcsMowerApiCommunicationError as exception:
                LOGGER.error(exception)
                errors["base"] = "connection"
            except ZcsMowerApiError as exception:
                LOGGER.exception(exception)
                errors["base"] = "connection"
            if not errors:
                # Input is valid, set data
                self.data = user_input
                self.data[CONF_MOWERS] = {}
                
                # Return the form of the next step
                return await self.async_step_mower()
            
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME),
                    ): cv.string,
                    vol.Required(
                        CONF_CLIENT_KEY,
                        default=(user_input or {}).get(CONF_CLIENT_KEY),
                    ): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_mower(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Second step in config flow to add a lawn mower."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # Validate the IMEI
            try:
                await validate_imei(
                    imei=user_input[CONF_IMEI],
                    client_key=self.data[CONF_CLIENT_KEY],
                    hass=self.hass
                )
            except Exception:
                errors["base"] = "invalid_imei"
            
            if not errors:
                # Input is valid, set data.
                self.data[CONF_MOWERS][user_input[CONF_IMEI]] = user_input.get(CONF_NAME, user_input[CONF_IMEI])
                
                # If user ticked the box show this form again so
                # they can add an additional lawn mower.
                if user_input.get("add_another", False):
                    return await self.async_step_mower()
                
                # User is done adding lawn mowers, create the config entry.
                return self.async_create_entry(
                    title=self.data[CONF_NAME],
                    data=self.data
                )
            
        return self.async_show_form(
            step_id="mower",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_IMEI
                    ): cv.string,
                    vol.Optional(
                        CONF_NAME
                    ): cv.string,
                    vol.Optional(
                        "add_another"
                    ): cv.boolean,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry
        self.data = dict(config_entry.data)

    async def async_step_init(
        self,
        user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}
        # Grab all configured lawn mowers from the entity registry so we can populate
        # the multi-select dropdown that will allow a user to remove a lawn mower.
        entity_registry = async_get(self.hass)
        entries = async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )
        # Default value for our multi-select
        all_mowers = {
            e.entity_id: e.original_name
            for e in entries
        }
        mower_map = {
            e.entity_id: e 
            for e in entries
        }
        
        if user_input is not None:
            updated_mowers = deepcopy(self.config_entry.data[CONF_MOWERS])

            # Remove any unchecked lawn mowers
            removed_entities = [
                entity_id
                for entity_id in mower_map.keys()
                if entity_id not in user_input["mowers"]
            ]
            for entity_id in removed_entities:
                # Unregister from HA
                entity_registry.async_remove(entity_id)
                # Remove from our configured mowers.
                entry = mower_map[entity_id]
                entry_imei = entry.unique_id
                updated_mowers = [e for e in updated_mowers if e["imei"] != entry_imei]

            if user_input.get(CONF_IMEI):
                try:
                    # Validate the imei.
                    client_key = self.config_entry.data[CONF_CLIENT_KEY]
                    await validate_imei(
                        imei=user_input[CONF_IMEI],
                        client_key=client_key,
                        hass=self.hass
                    )
                except Exception:
                    errors["base"] = "invalid_imei"

                if not errors:
                    # Add the new lawn mower
                    updated_mowers[user_input[CONF_IMEI]] = user_input.get(CONF_NAME, user_input[CONF_IMEI])
            
            self.data[CONF_MOWERS] = updated_mowers
            
            if not errors:
                # Value of data will be set on the options property of our config_entry instance.
                self.data.update(user_input)
                return self.async_create_entry(
                    title="",
                    data=self.data,
                )
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("mowers", default=list(all_mowers.keys())): cv.multi_select(
                        all_mowers
                    ),
                    vol.Optional(CONF_IMEI): cv.string,
                    vol.Optional(CONF_NAME): cv.string,
                }
            ),
            errors=errors
        )
