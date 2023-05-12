"""Adds config flow for ZCS Lawn Mower Robot."""
from __future__ import annotations

from copy import deepcopy

from homeassistant.core import (
    callback,
    HomeAssistant,
    HassJob,
)
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
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
    async_get_clientsession,
)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    LOGGER,
    DOMAIN,
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


async def validate_auth(client_key: str, hass: HomeAssistant) -> None:
    """Validate client key.

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

async def validate_imei(imei: str, client_key: str, hass: HassJob) -> None:
    """Validate a lawn mower IMEI.

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

    data: dict[str, any] | None
    options: dict[str, any] | None

    async def async_step_user(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Invoke when a user initiates a flow via the user interface."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(user_input[CONF_CLIENT_KEY], self.hass)
            except ValueError as exception:
                LOGGER.info(exception)
                errors["base"] = "invalid_key"
            except ZcsMowerApiAuthenticationError as exception:
                LOGGER.error(exception)
                errors["base"] = "auth"
            except (ZcsMowerApiCommunicationError, ZcsMowerApiError) as exception:
                LOGGER.error(exception)
                errors["base"] = "connection"
            except Exception as exception:
                LOGGER.exception(exception)
                errors["base"] = "connection"

            if not errors:
                # Input is valid, set data
                self.data = user_input
                self.options = {
                    CONF_MOWERS: {}
                }
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

    async def async_step_mower(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Second step in config flow to add a lawn mower."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Validate the IMEI
            try:
                await validate_imei(
                    imei=user_input[CONF_IMEI],
                    client_key=self.data[CONF_CLIENT_KEY],
                    hass=self.hass
                )
            except ValueError as exception:
                LOGGER.info(exception)
                errors["base"] = "invalid_imei"
            except Exception as exception:
                LOGGER.exception(exception)
                errors["base"] = "connection"

            if not errors:
                # Input is valid, set data.
                self.options[CONF_MOWERS][user_input[CONF_IMEI]] = user_input.get(
                    CONF_NAME,
                    user_input[CONF_IMEI],
                )
                # If user ticked the box show this form again so
                # they can add an additional lawn mower.
                if user_input.get("add_another", False):
                    return await self.async_step_mower()

                # User is done adding lawn mowers, create the config entry.
                return self.async_create_entry(
                    title=self.data[CONF_NAME],
                    data=self.data,
                    options=self.options,
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
        """Initialize options flow."""
        self.config_entry = config_entry
        self.data = dict(config_entry.data)
        self.options = dict(config_entry.options)

    async def async_step_init(
        self,
        user_input: dict[str, any] = None
    ) -> dict[str, any]:
        """Manage the options for the custom component."""
        errors: dict[str, str] = {}
        mowers: dict = self.options[CONF_MOWERS]
        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)

        if user_input is not None:
            updated_mowers = deepcopy(self.config_entry.options[CONF_MOWERS])
            mowers_remove = [
                _imei
                for _imei in mowers
                if _imei not in user_input[CONF_MOWERS]
            ]
            for _imei in mowers_remove:
                device = device_registry.async_get_device({(DOMAIN, _imei)})
                if not device:
                    continue
                entries = er.async_entries_for_device(
                    registry=entity_registry,
                    device_id=device.id,
                    include_disabled_entities=False,
                )
                [
                    entity_registry.async_remove(e.entity_id)
                    for e in entries
                ]
                device_registry.async_remove_device(device.id)
                updated_mowers.pop(_imei)

            # add new lawn mower
            if user_input.get(CONF_IMEI):
                try:
                    # Validate the imei.
                    client_key = self.config_entry.data[CONF_CLIENT_KEY]
                    await validate_imei(
                        imei=user_input[CONF_IMEI],
                        client_key=client_key,
                        hass=self.hass
                    )
                except ValueError as exception:
                    LOGGER.info(exception)
                    errors["base"] = "invalid_imei"
                except Exception as exception:
                    LOGGER.exception(exception)
                    errors["base"] = "connection"

                if not errors:
                    # Add the new lawn mower
                    updated_mowers[user_input[CONF_IMEI]] = user_input.get(
                        CONF_NAME,
                        user_input[CONF_IMEI],
                    )
            self.options[CONF_MOWERS] = updated_mowers

            if not errors:
                # Value of data will be set on the options property of our
                # config_entry instance.
                self.options.update()
                return self.async_create_entry(
                    title=self.data[CONF_NAME],
                    data=self.options,
                )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MOWERS,
                        default=list(mowers.keys())
                    ): cv.multi_select(
                        mowers,
                    ),
                    vol.Optional(CONF_IMEI): cv.string,
                    vol.Optional(CONF_NAME): cv.string,
                }
            ),
            errors=errors,
        )
