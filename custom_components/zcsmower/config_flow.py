"""Adds config flow for ZCS Lawn Mower Robot."""

from __future__ import annotations

import os

from homeassistant.core import callback
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlowWithConfigEntry,
    CONN_CLASS_CLOUD_POLL,
)
from homeassistant.const import (
    CONF_NAME,
    ATTR_NAME,
    DEGREE,
    UnitOfTime,
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
    CONF_CLIENT_KEY,
    CONF_STANDBY_TIME_START,
    CONF_STANDBY_TIME_STOP,
    CONF_UPDATE_INTERVAL_WORKING,
    CONF_UPDATE_INTERVAL_STANDBY,
    CONF_UPDATE_INTERVAL_IDLING,
    CONF_TRACE_POSITION_ENABLE,
    CONF_WAKE_UP_INTERVAL_DEFAULT,
    CONF_WAKE_UP_INTERVAL_INFINITY,
    CONF_MAP_ENABLE,
    CONF_MAP_HISTORY_ENABLE,
    CONF_MAP_IMAGE_PATH,
    CONF_MAP_MARKER_PATH,
    CONF_MAP_GPS_TOP_LEFT,
    CONF_MAP_GPS_BOTTOM_RIGHT,
    CONF_MAP_ROTATION,
    CONF_MAP_POINTS,
    CONF_MAP_DRAW_LINES,
    CONF_HIBERNATION_ENABLE,
    CONF_MOWERS,
    ATTR_IMEI,
    ATTR_ROBOT_CLIENT_INDEX,
    API_BASE_URI,
    API_APP_TOKEN,
    CONFIGURATION_DEFAULTS,
    STANDBY_TIME_START_DEFAULT,
    STANDBY_TIME_STOP_DEFAULT,
    LOCATION_HISTORY_ITEMS_DEFAULT,
    MAP_POINTS_DEFAULT,
)
from .api import (
    ZcsMowerApiClient,
    ZcsMowerApiAuthenticationError,
    ZcsMowerApiCommunicationError,
    ZcsMowerApiError,
)
from .helpers import (
    delete_robot_client,
    get_client_key,
    get_first_empty_robot_client,
    publish_client_thing,
    publish_robot_client,
    replace_robot_client,
    validate_imei,
)


class ZcsMowerConfigFlow(ConfigFlow, domain=DOMAIN):
    """ZCS Lawn Mower config flow."""

    VERSION = 11
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize the ZCS Lawn Mower flow."""
        self._title: str | None = None
        self._options: dict[str, any] | None = None

    async def async_step_user(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Invoke when a user initiates a flow via the user interface."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Garage Name
            if (garage_name := user_input.get(CONF_NAME, "").strip()):
                client_name = f"{garage_name} (Home Assistant)"
            else:
                client_name = "Home Assistant"

            try:
                client = ZcsMowerApiClient(
                    session=async_create_clientsession(self.hass),
                    options={
                        "endpoint": API_BASE_URI,
                    },
                )
                client_key = await get_client_key(client)
                await publish_client_thing(
                    client=client,
                    client_key=client_key,
                    client_name=client_name,
                )
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
                # Input is valid, set data and options
                self._title = garage_name
                self._options = {
                    CONF_CLIENT_KEY: client_key,
                    CONF_STANDBY_TIME_START: STANDBY_TIME_START_DEFAULT,
                    CONF_STANDBY_TIME_STOP: STANDBY_TIME_STOP_DEFAULT,
                    CONF_UPDATE_INTERVAL_WORKING: _get_config(CONF_UPDATE_INTERVAL_WORKING, "default"),
                    CONF_UPDATE_INTERVAL_STANDBY: _get_config(CONF_UPDATE_INTERVAL_STANDBY, "default"),
                    CONF_UPDATE_INTERVAL_IDLING: _get_config(CONF_UPDATE_INTERVAL_IDLING, "default"),
                    CONF_TRACE_POSITION_ENABLE: user_input.get(CONF_TRACE_POSITION_ENABLE, False),
                    CONF_WAKE_UP_INTERVAL_DEFAULT: _get_config(CONF_WAKE_UP_INTERVAL_DEFAULT, "default"),
                    CONF_WAKE_UP_INTERVAL_INFINITY: _get_config(CONF_WAKE_UP_INTERVAL_INFINITY, "default"),
                    CONF_MAP_ENABLE: user_input.get(CONF_MAP_ENABLE, False),
                    CONF_MAP_IMAGE_PATH: "",
                    CONF_MAP_MARKER_PATH: "",
                    CONF_MAP_GPS_TOP_LEFT: None,
                    CONF_MAP_GPS_BOTTOM_RIGHT: None,
                    CONF_MAP_ROTATION: 0.0,
                    CONF_MAP_HISTORY_ENABLE: True,
                    CONF_MAP_POINTS: int(MAP_POINTS_DEFAULT),
                    CONF_MAP_DRAW_LINES: True,
                    CONF_HIBERNATION_ENABLE: False,
                    CONF_MOWERS: {},
                }
                LOGGER.debug("Step user -> saved options:")
                LOGGER.debug(self._options)

                # Return the form of the next step
                # If user ticked the box go to map step
                if user_input.get(CONF_MAP_ENABLE, False):
                    return await self.async_step_map()
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
                    vol.Optional(
                        CONF_TRACE_POSITION_ENABLE,
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_MAP_ENABLE,
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_map(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Second step in config flow to configure map."""
        errors: dict[str, str] = {}
        if user_input is not None:
            image_map_path = user_input.get(CONF_MAP_IMAGE_PATH, "").strip()
            image_marker_path = user_input.get(CONF_MAP_MARKER_PATH, "").strip()

            if not os.path.isfile(image_map_path):
                errors["base"] = "path_invalid"
            elif user_input.get(CONF_MAP_GPS_TOP_LEFT).count(",") != 1:
                errors["base"] = "coordinates_invalid"
            elif user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT).count(",") != 1:
                errors["base"] = "coordinates_invalid"
            elif image_marker_path and not os.path.isfile(image_marker_path):
                errors["base"] = "path_invalid"

            if not errors:
                # Input is valid, set data
                self._options.update(
                    {
                        CONF_MAP_IMAGE_PATH: image_map_path,
                        CONF_MAP_MARKER_PATH: image_marker_path,
                        CONF_MAP_ROTATION: float(
                            user_input.get(CONF_MAP_ROTATION, 0.0)
                        ),
                        CONF_MAP_HISTORY_ENABLE: user_input.get(
                            CONF_MAP_HISTORY_ENABLE, True
                        ),
                        CONF_MAP_POINTS: int(
                            user_input.get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT)
                        ),
                        CONF_MAP_DRAW_LINES: user_input.get(CONF_MAP_DRAW_LINES, False),
                    }
                )
                if user_input.get(CONF_MAP_GPS_TOP_LEFT):
                    self._options[CONF_MAP_GPS_TOP_LEFT] = [
                        float(x.strip())
                        for x in user_input.get(CONF_MAP_GPS_TOP_LEFT).split(",")
                        if x
                    ]
                if user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT):
                    self._options[CONF_MAP_GPS_BOTTOM_RIGHT] = [
                        float(x.strip())
                        for x in user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT).split(",")
                        if x
                    ]
                LOGGER.debug("Step map -> saved options:")
                LOGGER.debug(self._options)

                # Return the form of the next step
                return await self.async_step_mower()
        return self.async_show_form(
            step_id="map",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MAP_IMAGE_PATH,
                        default=(user_input or {}).get(CONF_MAP_IMAGE_PATH, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_MAP_GPS_TOP_LEFT,
                        default=(user_input or {}).get(CONF_MAP_GPS_TOP_LEFT, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_MAP_GPS_BOTTOM_RIGHT,
                        default=(user_input or {}).get(CONF_MAP_GPS_BOTTOM_RIGHT, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_MAP_ROTATION,
                        default=(user_input or {}).get(CONF_MAP_ROTATION, 0.0),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=-360,
                            max=360,
                            step=0.01,
                            unit_of_measurement=DEGREE,
                        )
                    ),
                    vol.Optional(
                        CONF_MAP_MARKER_PATH,
                        description={
                            "suggested_value": (user_input or {}).get(
                                CONF_MAP_MARKER_PATH, ""
                            ),
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        CONF_MAP_HISTORY_ENABLE,
                        default=(user_input or {}).get(CONF_MAP_HISTORY_ENABLE, True),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_MAP_POINTS,
                        default=(user_input or {}).get(
                            CONF_MAP_POINTS, MAP_POINTS_DEFAULT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=1,
                            max=LOCATION_HISTORY_ITEMS_DEFAULT,
                        )
                    ),
                    vol.Optional(
                        CONF_MAP_DRAW_LINES,
                        default=(user_input or {}).get(CONF_MAP_DRAW_LINES, False),
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_mower(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Second/third step in config flow to add a lawn mower."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Validate lawn mower
            try:
                client_key = self._options[CONF_CLIENT_KEY]
                client = ZcsMowerApiClient(
                    session=async_get_clientsession(self.hass),
                    options={
                        "endpoint": API_BASE_URI,
                        "app_id": client_key,
                        "app_token": API_APP_TOKEN,
                        "thing_key": client_key,
                    },
                )
                mower = await validate_imei(
                    client=client,
                    imei=user_input[ATTR_IMEI],
                )
                robot_client_key = await get_first_empty_robot_client(
                    mower=mower,
                    client_key=client_key,
                )
            except ValueError as exception:
                LOGGER.info(exception)
                errors["base"] = "imei_invalid"
            except KeyError as exception:
                LOGGER.info(exception)
                errors["base"] = "mower_invalid"
            except IndexError as exception:
                LOGGER.info(exception)
                errors["base"] = "mower_too_many_clients"
            except ZcsMowerApiCommunicationError as exception:
                LOGGER.error(exception)
                errors["base"] = "communication_failed"
            except (Exception, ZcsMowerApiError) as exception:
                LOGGER.exception(exception)
                errors["base"] = "connection_failed"

            if not errors:
                # Input is valid, set data.
                self._options[CONF_MOWERS][user_input[ATTR_IMEI]] = {
                    ATTR_NAME: user_input.get(ATTR_NAME, user_input[ATTR_IMEI]),
                    ATTR_ROBOT_CLIENT_INDEX: robot_client_key,
                }
                # If user ticked the box show this form again so
                # they can add an additional lawn mower.
                if user_input.get("add_another", False):
                    return await self.async_step_mower()

                # User is done adding lawn mowers,
                # publish robot_client and create the config entry.
                for imei, mower in self._options.get(CONF_MOWERS, {}).items():
                    await publish_robot_client(
                        client=client,
                        imei=imei,
                        robot_client_key=mower.get(ATTR_ROBOT_CLIENT_INDEX),
                        client_key=client_key,
                    )

                LOGGER.debug("Step mower -> saved options:")
                LOGGER.debug(self._options)
                return self.async_create_entry(
                    title=self._title,
                    data={},
                    options=self._options,
                )
        return self.async_show_form(
            step_id="mower",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        ATTR_IMEI,
                        default=(user_input or {}).get(ATTR_IMEI, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        ATTR_NAME,
                        description={
                            "suggested_value": (user_input or {}).get(ATTR_NAME, ""),
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        "add_another",
                        default=(user_input or {}).get("add_another", False),
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> ZcsMowerOptionsFlowHandler:
        """Get the options flow for this handler."""
        return ZcsMowerOptionsFlowHandler(config_entry)


class ZcsMowerOptionsFlowHandler(OptionsFlowWithConfigEntry):
    """Handles options flow for the component."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__(config_entry)
        self.base_path = os.path.dirname(__file__)

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Show options menu for the ZCS Lawn Mower Robot component."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "add",
                "change",
                "delete",
                "map",
                "settings",
            ],
        )

    async def async_step_add(self, user_input: dict | None = None) -> FlowResult:
        """Add a lawn mower to the garage."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[ATTR_IMEI] in self._options[CONF_MOWERS]:
                errors["base"] = "imei_exists"
            elif user_input.get(ATTR_NAME, "") and any(
                m.get(ATTR_NAME, "") == user_input.get(ATTR_NAME)
                for m in self._options[CONF_MOWERS].values()
            ):
                errors["base"] = "name_exists"
            else:
                # Validate lawn mower
                try:
                    client_key = self._options[CONF_CLIENT_KEY]
                    client = ZcsMowerApiClient(
                        session=async_get_clientsession(self.hass),
                        options={
                            "endpoint": API_BASE_URI,
                            "app_id": client_key,
                            "app_token": API_APP_TOKEN,
                            "thing_key": client_key,
                        },
                    )
                    mower = await validate_imei(
                        client=client,
                        imei=user_input[ATTR_IMEI],
                    )
                    robot_client_key = await get_first_empty_robot_client(
                        mower=mower,
                        client_key=client_key,
                    )
                except ValueError as exception:
                    LOGGER.info(exception)
                    errors["base"] = "imei_invalid"
                except KeyError as exception:
                    LOGGER.info(exception)
                    errors["base"] = "mower_invalid"
                except IndexError as exception:
                    LOGGER.info(exception)
                    errors["base"] = "mower_too_many_clients"
                except ZcsMowerApiCommunicationError as exception:
                    LOGGER.error(exception)
                    errors["base"] = "communication_failed"
                except (Exception, ZcsMowerApiError) as exception:
                    LOGGER.exception(exception)
                    errors["base"] = "connection_failed"

            if not errors:
                # Input is valid, set data
                self._options[CONF_MOWERS][user_input[ATTR_IMEI]] = {
                    ATTR_NAME: user_input.get(ATTR_NAME, user_input[ATTR_IMEI]),
                    ATTR_ROBOT_CLIENT_INDEX: robot_client_key,
                }
                # Publish robot_client and create the config entry.
                await publish_robot_client(
                    client=client,
                    imei=user_input[ATTR_IMEI],
                    robot_client_key=robot_client_key,
                    client_key=client_key,
                )
                LOGGER.debug("Step add -> saved options:")
                LOGGER.debug(self._options)
                return self.async_create_entry(
                    title="",
                    data=self._options,
                )
        return self.async_show_form(
            step_id="add",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        ATTR_IMEI,
                        default=(user_input or {}).get(ATTR_IMEI, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        ATTR_NAME,
                        description={
                            "suggested_value": (user_input or {}).get(ATTR_NAME, ""),
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_change(self, user_input: dict | None = None) -> FlowResult:
        """Change a lawn mower from the garage."""
        errors: dict[str, str] = {}
        last_step = False
        form_schema = {
            vol.Required(
                ATTR_IMEI,
                default=(user_input or {}).get(ATTR_IMEI, ""),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(
                            value=imei,
                            label=f"{mower.get(ATTR_NAME)} ({imei})",
                        )
                        for imei, mower in self._options[CONF_MOWERS].items()
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key=ATTR_IMEI,
                    multiple=False,
                )
            ),
        }
        if user_input is not None:
            if user_input[ATTR_IMEI] not in self._options[CONF_MOWERS]:
                errors["base"] = "imei_not_exists"
            else:
                last_step = True
                mower_imei = user_input[ATTR_IMEI]
                if ATTR_NAME not in user_input:
                    mower_name = self._options[CONF_MOWERS][mower_imei].get(ATTR_NAME)
                else:
                    mower_name = user_input.get(ATTR_NAME)
                    if mower_name != self._options[CONF_MOWERS][mower_imei] and any(
                        m.get(ATTR_NAME, "") == mower_name
                        for m in self._options[CONF_MOWERS].values()
                    ):
                        errors["base"] = "name_exists"

                    if not errors:
                        device_registry = dr.async_get(self.hass)
                        device = device_registry.async_get_device(
                            {(DOMAIN, mower_imei)}
                        )
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
                        # Input is valid, set data
                        self._options[CONF_MOWERS][mower_imei] = {
                            ATTR_NAME: mower_name,
                        }
                        LOGGER.debug("Step change -> saved options:")
                        LOGGER.debug(self._options)
                        return self.async_create_entry(
                            title="",
                            data=self._options,
                        )
                form_schema.update(
                    {
                        vol.Required(
                            ATTR_NAME,
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

    async def async_step_delete(self, user_input: dict | None = None) -> FlowResult:
        """Delete a lawn mower from the garage."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if len(self._options[CONF_MOWERS]) == 1:
                errors["base"] = "last_mower"
            elif user_input[ATTR_IMEI] not in self._options[CONF_MOWERS]:
                errors["base"] = "imei_not_exists"
            elif user_input["confirm"] is not True:
                errors["base"] = "delete_not_confirmed"

            if not errors:
                robot_client_key = self._options[CONF_MOWERS][user_input[ATTR_IMEI]].get(ATTR_ROBOT_CLIENT_INDEX)

                device_registry = dr.async_get(self.hass)
                device = device_registry.async_get_device(
                    {(DOMAIN, user_input[ATTR_IMEI])}
                )
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

                # Input is valid, set data
                self._options[CONF_MOWERS].pop(user_input[ATTR_IMEI])

                # Remove remote client from lawn mower
                if robot_client_key:
                    try:
                        client_key = self._options[CONF_CLIENT_KEY]
                        client = ZcsMowerApiClient(
                            session=async_get_clientsession(self.hass),
                            options={
                                "endpoint": API_BASE_URI,
                                "app_id": client_key,
                                "app_token": API_APP_TOKEN,
                                "thing_key": client_key,
                            },
                        )
                        await delete_robot_client(
                            client=client,
                            imei=user_input[ATTR_IMEI],
                            robot_client_key=robot_client_key,
                        )
                    except Exception as exception:
                        LOGGER.warning(exception)

                LOGGER.debug("Step delete -> saved options:")
                LOGGER.debug(self._options)
                return self.async_create_entry(
                    title="",
                    data=self._options,
                )
        return self.async_show_form(
            step_id="delete",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        ATTR_IMEI,
                        default=(user_input or {}).get(ATTR_IMEI, ""),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=imei,
                                    label=f"{mower.get(ATTR_NAME)} ({imei})",
                                )
                                for imei, mower in self._options[CONF_MOWERS].items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            translation_key=ATTR_IMEI,
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

    async def async_step_map(self, user_input: dict | None = None) -> FlowResult:
        """Manage the ZCS Lawn Mower Robot map cam settings."""
        errors: dict[str, str] = {}
        gps_top_left = self._options.get(CONF_MAP_GPS_TOP_LEFT, "")
        if gps_top_left is not None:
            gps_top_left = ",".join([str(x) for x in gps_top_left])
        gps_bottom_right = self._options.get(CONF_MAP_GPS_BOTTOM_RIGHT, "")
        if gps_bottom_right is not None:
            gps_bottom_right = ",".join([str(x) for x in gps_bottom_right])
        if user_input is not None:
            image_map_path = user_input.get(CONF_MAP_IMAGE_PATH, "").strip()
            image_marker_path = user_input.get(CONF_MAP_MARKER_PATH, "").strip()
            if not os.path.isfile(image_map_path):
                errors["base"] = "path_invalid"
            elif user_input.get(CONF_MAP_GPS_TOP_LEFT).count(",") != 1:
                errors["base"] = "coordinates_invalid"
            elif user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT).count(",") != 1:
                errors["base"] = "coordinates_invalid"
            elif image_marker_path and not os.path.isfile(image_marker_path):
                errors["base"] = "path_invalid"

            if not errors:
                # Input is valid, set data
                self._options.update(
                    {
                        CONF_MAP_ENABLE: user_input.get(CONF_MAP_ENABLE, False),
                        CONF_MAP_IMAGE_PATH: image_map_path,
                        CONF_MAP_MARKER_PATH: image_marker_path,
                        CONF_MAP_ROTATION: float(
                            user_input.get(CONF_MAP_ROTATION, 0.0)
                        ),
                        CONF_MAP_HISTORY_ENABLE: user_input.get(
                            CONF_MAP_HISTORY_ENABLE, True
                        ),
                        CONF_MAP_POINTS: int(
                            user_input.get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT)
                        ),
                        CONF_MAP_DRAW_LINES: user_input.get(CONF_MAP_DRAW_LINES, False),
                    }
                )
                if user_input.get(CONF_MAP_GPS_TOP_LEFT):
                    self._options[CONF_MAP_GPS_TOP_LEFT] = [
                        float(x.strip())
                        for x in user_input.get(CONF_MAP_GPS_TOP_LEFT).split(",")
                        if x
                    ]
                if user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT):
                    self._options[CONF_MAP_GPS_BOTTOM_RIGHT] = [
                        float(x.strip())
                        for x in user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT).split(",")
                        if x
                    ]

                LOGGER.debug("Step map -> saved options:")
                LOGGER.debug(self._options)
                return self.async_create_entry(
                    title="",
                    data=self._options,
                )
            else:
                gps_top_left = user_input.get(CONF_MAP_GPS_TOP_LEFT)
                gps_bottom_right = user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT)

        return self.async_show_form(
            step_id="map",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MAP_ENABLE,
                        default=(user_input or self._options).get(
                            CONF_MAP_ENABLE, False
                        ),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_MAP_IMAGE_PATH,
                        default=(user_input or self._options).get(
                            CONF_MAP_IMAGE_PATH, ""
                        ),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_MAP_GPS_TOP_LEFT,
                        default=gps_top_left,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_MAP_GPS_BOTTOM_RIGHT,
                        default=gps_bottom_right,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(
                        CONF_MAP_ROTATION,
                        default=(user_input or self._options).get(
                            CONF_MAP_ROTATION, 0.0
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=-360,
                            max=360,
                            step=0.01,
                            unit_of_measurement=DEGREE,
                        )
                    ),
                    vol.Optional(
                        CONF_MAP_MARKER_PATH,
                        description={
                            "suggested_value": (user_input or self._options).get(
                                CONF_MAP_MARKER_PATH, ""
                            ),
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        CONF_MAP_HISTORY_ENABLE,
                        default=(user_input or self._options).get(
                            CONF_MAP_HISTORY_ENABLE, True
                        ),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_MAP_POINTS,
                        default=(user_input or self._options).get(
                            CONF_MAP_POINTS, MAP_POINTS_DEFAULT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=1,
                            max=LOCATION_HISTORY_ITEMS_DEFAULT,
                        )
                    ),
                    vol.Optional(
                        CONF_MAP_DRAW_LINES,
                        default=(user_input or self._options).get(
                            CONF_MAP_DRAW_LINES, False
                        ),
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_settings(self, user_input: dict | None = None) -> FlowResult:
        """Manage the ZCS Lawn Mower Robot settings."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Standby time start and stop are equal
            if user_input.get(CONF_STANDBY_TIME_START) == user_input.get(
                CONF_STANDBY_TIME_STOP
            ):
                errors["base"] = "standby_time_invalid"
            # Update interval for working is bigger than in standby time
            elif user_input.get(CONF_UPDATE_INTERVAL_WORKING) > user_input.get(
                CONF_UPDATE_INTERVAL_STANDBY
            ):
                errors["base"] = "update_interval_working_invalid"
            # Update interval in standby time is bigger than for idling
            elif user_input.get(CONF_UPDATE_INTERVAL_STANDBY) > user_input.get(
                CONF_UPDATE_INTERVAL_IDLING
            ):
                errors["base"] = "update_interval_standby_invalid"
            # User ticked the box for re-generating client key
            elif user_input.get("generate_client_key", False):
                # Garage Name
                if (garage_name := self.config_entry.title):
                    client_name = f"{garage_name} (Home Assistant)"
                else:
                    client_name = "Home Assistant"

                try:
                    client = ZcsMowerApiClient(
                        session=async_create_clientsession(self.hass),
                        options={
                            "endpoint": API_BASE_URI,
                        },
                    )
                    client_key_old = self.options.get(CONF_CLIENT_KEY)
                    client_key_new = await get_client_key(client)

                    await publish_client_thing(
                        client=client,
                        client_key=client_key_new,
                        client_name=client_name,
                    )
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
                self._options.update(
                    {
                        CONF_HIBERNATION_ENABLE: user_input.get(
                            CONF_HIBERNATION_ENABLE, False
                        ),
                        CONF_STANDBY_TIME_START: user_input.get(
                            CONF_STANDBY_TIME_START, STANDBY_TIME_START_DEFAULT
                        ),
                        CONF_STANDBY_TIME_STOP: user_input.get(
                            CONF_STANDBY_TIME_STOP, STANDBY_TIME_STOP_DEFAULT
                        ),
                        CONF_UPDATE_INTERVAL_WORKING: user_input.get(
                            CONF_UPDATE_INTERVAL_WORKING,
                            _get_config(CONF_UPDATE_INTERVAL_WORKING, "default"),
                        ),
                        CONF_UPDATE_INTERVAL_STANDBY: user_input.get(
                            CONF_UPDATE_INTERVAL_STANDBY,
                            _get_config(CONF_UPDATE_INTERVAL_STANDBY, "default"),
                        ),
                        CONF_UPDATE_INTERVAL_IDLING: user_input.get(
                            CONF_UPDATE_INTERVAL_IDLING,
                            _get_config(CONF_UPDATE_INTERVAL_IDLING, "default"),
                        ),
                        CONF_TRACE_POSITION_ENABLE: user_input.get(
                            CONF_TRACE_POSITION_ENABLE, False
                        ),
                        CONF_WAKE_UP_INTERVAL_DEFAULT: user_input.get(
                            CONF_WAKE_UP_INTERVAL_DEFAULT,
                            _get_config(CONF_WAKE_UP_INTERVAL_DEFAULT, "default"),
                        ),
                        CONF_WAKE_UP_INTERVAL_INFINITY: user_input.get(
                            CONF_WAKE_UP_INTERVAL_INFINITY,
                            _get_config(CONF_WAKE_UP_INTERVAL_INFINITY, "default"),
                        ),
                    }
                )
                # If user ticked the box for re-generating client key
                # Replace remote clients in lawn mower(s)
                if user_input.get("generate_client_key", False):
                    self._options.update(
                        {
                            CONF_CLIENT_KEY: client_key_new,
                        }
                    )
                    try:
                        await replace_robot_client(
                            client=client,
                            mowers=self.options.get(CONF_MOWERS, {}),
                            client_key_old=client_key_old,
                            client_key_new=client_key_new,
                        )
                    except Exception as exception:
                        LOGGER.warning(exception)

                LOGGER.debug("Step settings -> saved options:")
                LOGGER.debug(self._options)
                return self.async_create_entry(
                    title="",
                    data=self._options,
                )
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    # Hibernation state
                    vol.Optional(
                        CONF_HIBERNATION_ENABLE,
                        default=(user_input or self._options).get(
                            CONF_HIBERNATION_ENABLE, False
                        ),
                    ): selector.BooleanSelector(),
                    # Standby time starts
                    vol.Optional(
                        CONF_STANDBY_TIME_START,
                        default=STANDBY_TIME_START_DEFAULT,
                        description={
                            "suggested_value": (user_input or self._options).get(
                                CONF_STANDBY_TIME_START, STANDBY_TIME_START_DEFAULT
                            ),
                        },
                    ): selector.TimeSelector(
                        selector.TimeSelectorConfig(),
                    ),
                    # Standby time stops
                    vol.Optional(
                        CONF_STANDBY_TIME_STOP,
                        default=STANDBY_TIME_STOP_DEFAULT,
                        description={
                            "suggested_value": (user_input or self._options).get(
                                CONF_STANDBY_TIME_STOP, STANDBY_TIME_STOP_DEFAULT
                            ),
                        },
                    ): selector.TimeSelector(
                        selector.TimeSelectorConfig(),
                    ),
                    # Update interval, if one or more lawn mowers working
                    vol.Optional(
                        CONF_UPDATE_INTERVAL_WORKING,
                        default=_get_config(CONF_UPDATE_INTERVAL_WORKING, "default"),
                        description={
                            "suggested_value": (user_input or self._options).get(
                                CONF_UPDATE_INTERVAL_WORKING,
                                _get_config(CONF_UPDATE_INTERVAL_WORKING, "default"),
                            ),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=_get_config(CONF_UPDATE_INTERVAL_WORKING, "min", 1),
                            max=_get_config(CONF_UPDATE_INTERVAL_WORKING, "max", 100000),
                            step=_get_config(CONF_UPDATE_INTERVAL_WORKING, "step", 1),
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    # Update interval, if all lawn mowers on standby
                    vol.Optional(
                        CONF_UPDATE_INTERVAL_STANDBY,
                        default=_get_config(CONF_UPDATE_INTERVAL_STANDBY, "default"),
                        description={
                            "suggested_value": (user_input or self._options).get(
                                CONF_UPDATE_INTERVAL_STANDBY,
                                _get_config(CONF_UPDATE_INTERVAL_STANDBY, "default"),
                            ),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=_get_config(CONF_UPDATE_INTERVAL_STANDBY, "min", 1),
                            max=_get_config(CONF_UPDATE_INTERVAL_STANDBY, "max", 100000),
                            step=_get_config(CONF_UPDATE_INTERVAL_STANDBY, "step", 1),
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    # Update interval, if all lawn mowers idling
                    vol.Optional(
                        CONF_UPDATE_INTERVAL_IDLING,
                        default=_get_config(CONF_UPDATE_INTERVAL_IDLING, "default"),
                        description={
                            "suggested_value": (user_input or self._options).get(
                                CONF_UPDATE_INTERVAL_IDLING,
                                _get_config(CONF_UPDATE_INTERVAL_IDLING, "default"),
                            ),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=_get_config(CONF_UPDATE_INTERVAL_IDLING, "min", 1),
                            max=_get_config(CONF_UPDATE_INTERVAL_IDLING, "max", 100000),
                            step=_get_config(CONF_UPDATE_INTERVAL_IDLING, "step", 1),
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    # Trace position
                    vol.Optional(
                        CONF_TRACE_POSITION_ENABLE,
                        default=(user_input or self._options).get(
                            CONF_TRACE_POSITION_ENABLE, False
                        ),
                    ): selector.BooleanSelector(),
                    # Wake up interval (Standard plan)
                    vol.Optional(
                        CONF_WAKE_UP_INTERVAL_DEFAULT,
                        default=_get_config(CONF_WAKE_UP_INTERVAL_DEFAULT, "default"),
                        description={
                            "suggested_value": (user_input or self._options).get(
                                CONF_WAKE_UP_INTERVAL_DEFAULT,
                                _get_config(CONF_WAKE_UP_INTERVAL_DEFAULT, "default"),
                            ),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=_get_config(CONF_WAKE_UP_INTERVAL_DEFAULT, "min", 1),
                            max=_get_config(CONF_WAKE_UP_INTERVAL_DEFAULT, "max", 100000),
                            step=_get_config(CONF_WAKE_UP_INTERVAL_DEFAULT, "step", 1),
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    # Wake up interval (+Infinity plan)
                    vol.Optional(
                        CONF_WAKE_UP_INTERVAL_INFINITY,
                        default=_get_config(CONF_WAKE_UP_INTERVAL_INFINITY, "default"),
                        description={
                            "suggested_value": (user_input or self._options).get(
                                CONF_WAKE_UP_INTERVAL_INFINITY,
                                _get_config(CONF_WAKE_UP_INTERVAL_INFINITY, "default"),
                            ),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=_get_config(CONF_WAKE_UP_INTERVAL_INFINITY, "min", 1),
                            max=_get_config(CONF_WAKE_UP_INTERVAL_INFINITY, "max", 100000),
                            step=_get_config(CONF_WAKE_UP_INTERVAL_INFINITY, "step", 1),
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    # Re-generate client key
                    vol.Optional(
                        "generate_client_key",
                        default=(user_input or {}).get("generate_client_key", False),
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

def _get_config(
    key: str,
    native: str = "default",
    fallback_default: int = 0
) -> int:
    return int(CONFIGURATION_DEFAULTS.get(key).get(native, fallback_default))
