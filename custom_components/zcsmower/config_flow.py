"""Adds config flow for ZCS Lawn Mower Robot."""
from __future__ import annotations

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
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    selector,
)
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
    async_get_clientsession,
)
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

    VERSION = 2
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    data: dict[str, any] | None

    async def async_step_user(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Invoke when a user initiates a flow via the user interface."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(
                    client_key=user_input[CONF_CLIENT_KEY],
                    hass=self.hass,
                )
            except ValueError as exception:
                LOGGER.info(exception)
                errors["base"] = "key_invalid"
            except ZcsMowerApiAuthenticationError as exception:
                LOGGER.error(exception)
                errors["base"] = "auth_failed"
            except ZcsMowerApiCommunicationError as exception:
                LOGGER.error(exception)
                errors["base"] = "communication_failed"
            except (Exception, ZcsMowerApiError) as exception:
                LOGGER.exception(exception)
                errors["base"] = "connection_failed"

            if not errors:
                # Input is valid, set data
                self.data = {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_CLIENT_KEY: user_input[CONF_CLIENT_KEY],
                    CONF_MOWERS: {},
                }
                # Return the form of the next step
                return await self.async_step_mower()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_CLIENT_KEY,
                        default=(user_input or {}).get(CONF_CLIENT_KEY, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
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
                errors["base"] = "imei_invalid"
            except ZcsMowerApiCommunicationError as exception:
                LOGGER.error(exception)
                errors["base"] = "communication_failed"
            except (Exception, ZcsMowerApiError) as exception:
                LOGGER.exception(exception)
                errors["base"] = "connection_failed"

            if not errors:
                # Input is valid, set data.
                self.data[CONF_MOWERS][user_input[CONF_IMEI]] = user_input.get(
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
                )
        return self.async_show_form(
            step_id="mower",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_IMEI,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        CONF_NAME,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        "add_another",
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ZcsMowerOptionsFlowHandler(config_entry)


class ZcsMowerOptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.data = dict(config_entry.data)

    async def async_step_init(
        self,
        user_input: dict | None = None
    ) -> FlowResult:
        """Show options menu for the ZCS Lawn Mower Robot component."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "add",
                "change",
                "delete",
                "settings",
            ],
        )

    async def async_step_add(
        self,
        user_input: dict | None = None
    ) -> FlowResult:
        """Add a lawn mower to the garage."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_IMEI] in self.data[CONF_MOWERS]:
                errors["base"] = "imei_exists"
            elif (
                user_input[CONF_NAME]
                and user_input[CONF_NAME] in self.data[CONF_MOWERS].values()
            ):
                errors["base"] = "name_exists"
            else:
                # Validate the IMEI
                try:
                    await validate_imei(
                        imei=user_input[CONF_IMEI],
                        client_key=self.data[CONF_CLIENT_KEY],
                        hass=self.hass,
                    )
                except ValueError as exception:
                    LOGGER.info(exception)
                    errors["base"] = "imei_invalid"
                except ZcsMowerApiCommunicationError as exception:
                    LOGGER.error(exception)
                    errors["base"] = "communication_failed"
                except (Exception, ZcsMowerApiError) as exception:
                    LOGGER.exception(exception)
                    errors["base"] = "connection_failed"

            if not errors:
                # Input is valid, set data
                self.data[CONF_MOWERS][user_input[CONF_IMEI]] = user_input.get(
                    CONF_NAME,
                    user_input[CONF_IMEI],
                )
                return self.async_create_entry(
                    title=self.data[CONF_NAME],
                    data=self.data,
                )

        return self.async_show_form(
            step_id="add",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_IMEI,
                        default=(user_input or {}).get(CONF_IMEI, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_change(
        self,
        user_input: dict | None = None
    ) -> FlowResult:
        """Change a lawn mower from the garage."""
        errors: dict[str, str] = {}
        last_step = False
        form_schema = {
            vol.Required(
                CONF_IMEI,
                default=(user_input or {}).get(CONF_IMEI, ""),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(
                            value=imei,
                            label=f"{name} ({imei})",
                        )
                        for imei, name in self.data[CONF_MOWERS].items()
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key=CONF_IMEI,
                    multiple=False,
                )
            ),
        }
        if user_input is not None:
            if user_input[CONF_IMEI] not in self.data[CONF_MOWERS]:
                errors["base"] = "imei_not_exists"
            else:
                last_step = True
                mower_imei = user_input[CONF_IMEI]
                if CONF_NAME not in user_input:
                    mower_name = self.data[CONF_MOWERS][mower_imei]
                else:
                    mower_name = user_input[CONF_NAME]
                    if (
                        mower_name != self.data[CONF_MOWERS][mower_imei]
                        and mower_name in self.data[CONF_MOWERS].values()
                    ):
                        errors["base"] = "name_exists"

                    if not errors:
                        device_registry = dr.async_get(self.hass)
                        device = device_registry.async_get_device({(DOMAIN, mower_imei)})
                        if not device:
                            return self.async_abort(reason="device_error")
                        LOGGER.debug(device)

                        entity_registry = er.async_get(self.hass)
                        entries = er.async_entries_for_device(
                            registry=entity_registry,
                            device_id=device.id,
                            include_disabled_entities=False,
                        )
                        [
                            entity_registry.async_update_entity(
                                e.entity_id,
                                original_name=mower_name,
                            )
                            for e in entries
                        ]
                        device_registry.async_update_device(
                            device.id,
                            name=mower_name,
                        )
                        self.data[CONF_MOWERS][mower_imei] = mower_name

                        # Input is valid, set data
                        return self.async_create_entry(
                            title=self.data[CONF_NAME],
                            data=self.data,
                        )
                form_schema.update(
                    {
                        vol.Required(
                            CONF_NAME,
                            default=mower_name,
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(
                                type=selector.TextSelectorType.TEXT
                            ),
                        ),
                    }
                )
        return self.async_show_form(
            step_id="change",
            data_schema=vol.Schema(form_schema),
            errors=errors,
            last_step=last_step,
        )

    async def async_step_delete(
        self,
        user_input: dict | None = None
    ) -> FlowResult:
        """Delete a lawn mower from the garage."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if len(self.data[CONF_MOWERS]) == 1:
                errors["base"] = "last_mower"
            elif user_input[CONF_IMEI] not in self.data[CONF_MOWERS]:
                errors["base"] = "imei_not_exists"
            elif user_input["confirm"] is not True:
                errors["base"] = "delete_not_confirmed"

            if not errors:
                device_registry = dr.async_get(self.hass)
                device = device_registry.async_get_device({(DOMAIN, user_input[CONF_IMEI])})
                if not device:
                    return self.async_abort(reason="device_error")
                LOGGER.debug(device)

                entity_registry = er.async_get(self.hass)
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
                self.data[CONF_MOWERS].pop(user_input[CONF_IMEI])

                # Input is valid, set data
                return self.async_create_entry(
                    title=self.data[CONF_NAME],
                    data=self.data,
                )
        return self.async_show_form(
            step_id="delete",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_IMEI,
                        default=(user_input or {}).get(CONF_IMEI, ""),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=imei,
                                    label=f"{name} ({imei})",
                                )
                                for imei, name in self.data[CONF_MOWERS].items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            translation_key=CONF_IMEI,
                            multiple=False,
                        )
                    ),
                    vol.Required(
                        "confirm",
                        default=False,
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_settings(
        self,
        user_input: dict | None = None
    ) -> FlowResult:
        """Manage the ZCS Lawn Mower Robot settings."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(
                    client_key=user_input[CONF_CLIENT_KEY],
                    hass=self.hass,
                )
            except ValueError as exception:
                LOGGER.info(exception)
                errors["base"] = "key_invalid"
            except ZcsMowerApiAuthenticationError as exception:
                LOGGER.error(exception)
                errors["base"] = "auth_failed"
            except (ZcsMowerApiCommunicationError, ZcsMowerApiError) as exception:
                LOGGER.error(exception)
                errors["base"] = "connection_failed"
            except Exception as exception:
                LOGGER.exception(exception)
                errors["base"] = "connection_failed"

            if not errors:
                # Input is valid, set data
                self.data.update(
                    {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_CLIENT_KEY: user_input[CONF_CLIENT_KEY],
                    }
                )
                return self.async_create_entry(
                    title=self.data[CONF_NAME],
                    data=self.data,
                )
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or self.data).get(CONF_NAME, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_CLIENT_KEY,
                        default=(user_input or self.data).get(CONF_CLIENT_KEY, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=errors,
        )
