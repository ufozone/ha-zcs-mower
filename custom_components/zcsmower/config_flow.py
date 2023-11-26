"""Adds config flow for ZCS Lawn Mower Robot."""
from __future__ import annotations

import os

from homeassistant.core import (
    callback,
    HomeAssistant,
    HassJob,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlowWithConfigEntry,
    CONN_CLASS_CLOUD_POLL,
)
from homeassistant.const import (
    CONF_NAME,
    ATTR_NAME,
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
    CONF_CAMERA_ENABLE,
    CONF_MAP_HISTORY_ENABLE,
    CONF_MAP_IMAGE_PATH,
    CONF_MAP_MARKER_PATH,
    CONF_MAP_GPS_TOP_LEFT,
    CONF_MAP_GPS_BOTTOM_RIGHT,
    CONF_MAP_DRAW_LINES,
    CONF_MAP_POINTS,
    CONF_MOWERS,
    ATTR_IMEI,
    API_BASE_URI,
    API_APP_TOKEN,
    STANDBY_TIME_START_DEFAULT,
    STANDBY_TIME_STOP_DEFAULT,
    UPDATE_INTERVAL_WORKING,
    UPDATE_INTERVAL_STANDBY,
    UPDATE_INTERVAL_IDLING,
    LOCATION_HISTORY_ITEMS,
    MAP_POINTS_DEFAULT,
    ROBOT_WAKE_UP_INTERVAL_DEFAULT,
    ROBOT_WAKE_UP_INTERVAL_INFINITY,
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

    VERSION = 9
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
                # Input is valid, set data and options
                self._title = user_input.get(CONF_NAME, "")
                self._options = {
                    CONF_CLIENT_KEY: user_input.get(CONF_CLIENT_KEY, "").strip(),
                    CONF_UPDATE_INTERVAL_WORKING: int(UPDATE_INTERVAL_WORKING),
                    CONF_UPDATE_INTERVAL_STANDBY: int(UPDATE_INTERVAL_STANDBY),
                    CONF_UPDATE_INTERVAL_IDLING: int(UPDATE_INTERVAL_IDLING),
                    CONF_TRACE_POSITION_ENABLE: user_input.get(CONF_TRACE_POSITION_ENABLE, False),
                    CONF_WAKE_UP_INTERVAL_DEFAULT: int(ROBOT_WAKE_UP_INTERVAL_DEFAULT),
                    CONF_WAKE_UP_INTERVAL_INFINITY: int(ROBOT_WAKE_UP_INTERVAL_INFINITY),
                    CONF_CAMERA_ENABLE: user_input.get(CONF_CAMERA_ENABLE, False),
                    CONF_MAP_IMAGE_PATH: "",
                    CONF_MAP_MARKER_PATH: "",
                    CONF_MAP_GPS_TOP_LEFT: "",
                    CONF_MAP_GPS_BOTTOM_RIGHT: "",
                    CONF_MAP_HISTORY_ENABLE: True,
                    CONF_MAP_DRAW_LINES: True,
                    CONF_MAP_POINTS: int(MAP_POINTS_DEFAULT),
                    CONF_MOWERS: {},
                }
                LOGGER.debug(self._options)
                # Return the form of the next step
                # If user ticked the box go to camera step
                if user_input.get(CONF_CAMERA_ENABLE, False):
                    return await self.async_step_camera()
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
                    vol.Optional(
                        CONF_TRACE_POSITION_ENABLE,
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_CAMERA_ENABLE,
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_camera(
        self,
        user_input: dict[str, any] | None = None,
    ) -> FlowResult:
        """Second step in config flow to configure camera."""
        errors: dict[str, str] = {}
        if user_input is not None:
            image_map_path = user_input.get(CONF_MAP_IMAGE_PATH, "").strip()
            image_marker_path = user_input.get(CONF_MAP_MARKER_PATH, "").strip()
            if not os.path.isfile(image_map_path):
                errors["base"] = "path_invalid"
            if user_input.get(CONF_MAP_GPS_TOP_LEFT).count(",") != 1:
                errors["base"] = "coordinates_invalid"
            if user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT).count(",") != 1:
                errors["base"] = "coordinates_invalid"
            if image_marker_path and not os.path.isfile(image_marker_path):
                errors["base"] = "path_invalid"

            if not errors:
                # Input is valid, set data
                self._options.update(
                    {
                        CONF_MAP_IMAGE_PATH: image_map_path,
                        CONF_MAP_MARKER_PATH: image_marker_path,
                        CONF_MAP_HISTORY_ENABLE: user_input.get(CONF_MAP_HISTORY_ENABLE, True),
                        CONF_MAP_POINTS: int(user_input.get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT)),
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
                LOGGER.debug(self._options)
                # Return the form of the next step
                return await self.async_step_mower()
        return self.async_show_form(
            step_id="camera",
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
                    vol.Optional(
                        CONF_MAP_MARKER_PATH,
                        description={
                            "suggested_value": (user_input or {}).get(CONF_MAP_MARKER_PATH, ""),
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
                        default=(user_input or {}).get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=1,
                            max=LOCATION_HISTORY_ITEMS,
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
            # Validate the IMEI
            try:
                await validate_imei(
                    imei=user_input[ATTR_IMEI],
                    client_key=self._options[CONF_CLIENT_KEY],
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
                self._options[CONF_MOWERS][user_input[ATTR_IMEI]] = {
                    ATTR_NAME: user_input.get(ATTR_NAME, user_input[ATTR_IMEI]),
                }
                LOGGER.debug(self._options)
                # If user ticked the box show this form again so
                # they can add an additional lawn mower.
                if user_input.get("add_another", False):
                    return await self.async_step_mower()

                # User is done adding lawn mowers, create the config entry.
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
                "camera",
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
            if user_input[ATTR_IMEI] in self._options[CONF_MOWERS]:
                errors["base"] = "imei_exists"
            elif (
                user_input.get(ATTR_NAME, "")
                and any(m.get(ATTR_NAME, "") == user_input.get(ATTR_NAME) for m in self._options[CONF_MOWERS].values())
            ):
                errors["base"] = "name_exists"
            else:
                # Validate the IMEI
                try:
                    await validate_imei(
                        imei=user_input[ATTR_IMEI],
                        client_key=self._options[CONF_CLIENT_KEY],
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
                self._options[CONF_MOWERS][user_input[ATTR_IMEI]] = {
                    ATTR_NAME: user_input.get(ATTR_NAME, user_input[ATTR_IMEI]),
                }
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

    async def async_step_change(
        self,
        user_input: dict | None = None
    ) -> FlowResult:
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
                    if (
                        mower_name != self._options[CONF_MOWERS][mower_imei]
                        and any(m.get(ATTR_NAME, "") == mower_name for m in self._options[CONF_MOWERS].values())
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
                        self._options[CONF_MOWERS][mower_imei] = {
                            ATTR_NAME: mower_name,
                        }
                        # Input is valid, set data
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

    async def async_step_delete(
        self,
        user_input: dict | None = None
    ) -> FlowResult:
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
                device_registry = dr.async_get(self.hass)
                device = device_registry.async_get_device({(DOMAIN, user_input[ATTR_IMEI])})
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
                self._options[CONF_MOWERS].pop(user_input[ATTR_IMEI])

                # Input is valid, set data
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

    async def async_step_camera(
        self,
        user_input: dict | None = None
    ) -> FlowResult:
        """Manage the ZCS Lawn Mower Robot map cam settings."""
        errors: dict[str, str] = {}
        gps_top_left = self._options.get(CONF_MAP_GPS_TOP_LEFT, "")
        if gps_top_left != "":
            gps_top_left = ",".join(
                [str(x) for x in gps_top_left]
            )
        gps_bottom_right = self._options.get(CONF_MAP_GPS_BOTTOM_RIGHT, "")
        if gps_bottom_right != "":
            gps_bottom_right = ",".join(
                [str(x) for x in gps_bottom_right]
            )
        if user_input is not None:
            image_map_path = user_input.get(CONF_MAP_IMAGE_PATH, "").strip()
            image_marker_path = user_input.get(CONF_MAP_MARKER_PATH, "").strip()
            if not os.path.isfile(image_map_path):
                errors["base"] = "path_invalid"
            if user_input.get(CONF_MAP_GPS_TOP_LEFT).count(",") != 1:
                errors["base"] = "coordinates_invalid"
            if user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT).count(",") != 1:
                errors["base"] = "coordinates_invalid"
            if image_marker_path and not os.path.isfile(image_marker_path):
                errors["base"] = "path_invalid"

            if not errors:
                # Input is valid, set data
                self._options.update(
                    {
                        CONF_CAMERA_ENABLE: user_input.get(CONF_CAMERA_ENABLE, False),
                        CONF_MAP_IMAGE_PATH: image_map_path,
                        CONF_MAP_MARKER_PATH: image_marker_path,
                        CONF_MAP_HISTORY_ENABLE: user_input.get(CONF_MAP_HISTORY_ENABLE, True),
                        CONF_MAP_POINTS: int(user_input.get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT)),
                        CONF_MAP_DRAW_LINES: user_input.get(CONF_MAP_DRAW_LINES, False),
                    }
                )
                if user_input.get(CONF_MAP_GPS_TOP_LEFT):
                    gps_top_left = user_input.get(CONF_MAP_GPS_TOP_LEFT)
                    self._options[CONF_MAP_GPS_TOP_LEFT] = [
                        float(x.strip())
                        for x in user_input.get(CONF_MAP_GPS_TOP_LEFT).split(",")
                        if x
                    ]
                if user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT):
                    gps_bottom_right = user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT)
                    self._options[CONF_MAP_GPS_BOTTOM_RIGHT] = [
                        float(x.strip())
                        for x in user_input.get(CONF_MAP_GPS_BOTTOM_RIGHT).split(",")
                        if x
                    ]
                LOGGER.debug(self._options)
                return self.async_create_entry(
                    title="",
                    data=self._options,
                )
        return self.async_show_form(
            step_id="camera",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CAMERA_ENABLE,
                        default=(user_input or self._options).get(CONF_CAMERA_ENABLE, False),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_MAP_IMAGE_PATH,
                        default=(user_input or self._options).get(CONF_MAP_IMAGE_PATH, ""),
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
                    vol.Optional(
                        CONF_MAP_MARKER_PATH,
                        description={
                            "suggested_value": (user_input or self._options).get(CONF_MAP_MARKER_PATH, ""),
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Optional(
                        CONF_MAP_HISTORY_ENABLE,
                        default=(user_input or self._options).get(CONF_MAP_HISTORY_ENABLE, True),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_MAP_POINTS,
                        default=(user_input or self._options).get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=1,
                            max=LOCATION_HISTORY_ITEMS,
                        )
                    ),
                    vol.Optional(
                        CONF_MAP_DRAW_LINES,
                        default=(user_input or self._options).get(CONF_MAP_DRAW_LINES, False),
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
            # Standby time start and stop are equal
            if user_input.get(CONF_STANDBY_TIME_START) == user_input.get(CONF_STANDBY_TIME_STOP):
                errors["base"] = "standby_time_invalid"
            # Update interval for working is bigger than in standby time
            if user_input.get(CONF_UPDATE_INTERVAL_WORKING) > user_input.get(CONF_UPDATE_INTERVAL_STANDBY):
                errors["base"] = "update_interval_working_invalid"
            # Update interval in standby time is bigger than for idling
            if user_input.get(CONF_UPDATE_INTERVAL_STANDBY) > user_input.get(CONF_UPDATE_INTERVAL_IDLING):
                errors["base"] = "update_interval_standby_invalid"

            if not errors:
                # Input is valid, set data
                self._options.update(
                    {
                        CONF_CLIENT_KEY: user_input.get(CONF_CLIENT_KEY, "").strip(),
                        CONF_STANDBY_TIME_START: user_input.get(CONF_STANDBY_TIME_START, STANDBY_TIME_START_DEFAULT),
                        CONF_STANDBY_TIME_STOP: user_input.get(CONF_STANDBY_TIME_STOP, STANDBY_TIME_STOP_DEFAULT),
                        CONF_UPDATE_INTERVAL_WORKING: user_input.get(CONF_UPDATE_INTERVAL_WORKING, UPDATE_INTERVAL_WORKING),
                        CONF_UPDATE_INTERVAL_STANDBY: user_input.get(CONF_UPDATE_INTERVAL_STANDBY, UPDATE_INTERVAL_STANDBY),
                        CONF_UPDATE_INTERVAL_IDLING: user_input.get(CONF_UPDATE_INTERVAL_IDLING, UPDATE_INTERVAL_IDLING),
                        CONF_TRACE_POSITION_ENABLE: user_input.get(CONF_TRACE_POSITION_ENABLE, False),
                        CONF_WAKE_UP_INTERVAL_DEFAULT: user_input.get(CONF_WAKE_UP_INTERVAL_DEFAULT, ROBOT_WAKE_UP_INTERVAL_DEFAULT),
                        CONF_WAKE_UP_INTERVAL_INFINITY: user_input.get(CONF_WAKE_UP_INTERVAL_INFINITY, ROBOT_WAKE_UP_INTERVAL_INFINITY),
                    }
                )
                LOGGER.debug(self._options)
                return self.async_create_entry(
                    title="",
                    data=self._options,
                )
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    # Client key
                    vol.Required(
                        CONF_CLIENT_KEY,
                        default=(user_input or self._options).get(CONF_CLIENT_KEY, ""),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    # Standby time starts
                    vol.Optional(
                        CONF_STANDBY_TIME_START,
                        default=STANDBY_TIME_START_DEFAULT,
                        description={
                            "suggested_value": (user_input or self._options).get(CONF_STANDBY_TIME_START, STANDBY_TIME_START_DEFAULT),
                        },
                    ): selector.TimeSelector(
                        selector.TimeSelectorConfig(),
                    ),
                    # Standby time stops
                    vol.Optional(
                        CONF_STANDBY_TIME_STOP,
                        default=STANDBY_TIME_STOP_DEFAULT,
                        description={
                            "suggested_value": (user_input or self._options).get(CONF_STANDBY_TIME_STOP, STANDBY_TIME_STOP_DEFAULT),
                        },
                    ): selector.TimeSelector(
                        selector.TimeSelectorConfig(),
                    ),
                    # Update interval, if one or more lawn mowers working
                    vol.Optional(
                        CONF_UPDATE_INTERVAL_WORKING,
                        default=UPDATE_INTERVAL_WORKING,
                        description={
                            "suggested_value": (user_input or self._options).get(CONF_UPDATE_INTERVAL_WORKING, UPDATE_INTERVAL_WORKING),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=30,
                            max=300,
                            step=30,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    # Update interval, if all lawn mowers on standby
                    vol.Optional(
                        CONF_UPDATE_INTERVAL_STANDBY,
                        default=UPDATE_INTERVAL_STANDBY,
                        description={
                            "suggested_value": (user_input or self._options).get(CONF_UPDATE_INTERVAL_STANDBY, UPDATE_INTERVAL_STANDBY),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=120,
                            max=3600,
                            step=60,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    # Update interval, if all lawn mowers idling
                    vol.Optional(
                        CONF_UPDATE_INTERVAL_IDLING,
                        default=UPDATE_INTERVAL_IDLING,
                        description={
                            "suggested_value": (user_input or self._options).get(CONF_UPDATE_INTERVAL_IDLING, UPDATE_INTERVAL_IDLING),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=600,
                            max=86400,
                            step=600,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    # Trace position
                    vol.Optional(
                        CONF_TRACE_POSITION_ENABLE,
                        default=(user_input or self._options).get(CONF_TRACE_POSITION_ENABLE, False),
                    ): selector.BooleanSelector(),
                    # Wake up interval (Standard plan)
                    vol.Optional(
                        CONF_WAKE_UP_INTERVAL_DEFAULT,
                        default=ROBOT_WAKE_UP_INTERVAL_DEFAULT,
                        description={
                            "suggested_value": (user_input or self._options).get(CONF_WAKE_UP_INTERVAL_DEFAULT, ROBOT_WAKE_UP_INTERVAL_DEFAULT),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=300,
                            max=21600,
                            step=300,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    # Wake up interval (Infinity+ plan)
                    vol.Optional(
                        CONF_WAKE_UP_INTERVAL_INFINITY,
                        default=ROBOT_WAKE_UP_INTERVAL_INFINITY,
                        description={
                            "suggested_value": (user_input or self._options).get(CONF_WAKE_UP_INTERVAL_INFINITY, ROBOT_WAKE_UP_INTERVAL_INFINITY),
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=300,
                            max=21600,
                            step=300,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
            errors=errors,
        )
