"""DataUpdateCoordinator for ZCS Lawn Mower Robot."""
from __future__ import annotations

import asyncio

from datetime import (
    timedelta,
    datetime,
)

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_NAME,
    ATTR_ICON,
    ATTR_STATE,
    ATTR_LOCATION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SW_VERSION,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed
import homeassistant.util.dt as dt_util

from .api import (
    ZcsMowerApiClient,
    ZcsMowerApiAuthenticationError,
    ZcsMowerApiError,
)
from .const import (
    LOGGER,
    DOMAIN,
    CONF_CLIENT_KEY,
    CONF_UPDATE_INTERVAL_WORKING,
    CONF_UPDATE_INTERVAL_IDLING,
    CONF_UPDATE_INTERVAL_STANDBY,
    CONF_TRACE_POSITION_ENABLE,
    CONF_WAKE_UP_INTERVAL_DEFAULT,
    CONF_WAKE_UP_INTERVAL_INFINITY,
    CONF_MOWERS,
    ATTR_IMEI,
    ATTR_INFINITY,
    ATTR_SERIAL,
    ATTR_WORKING,
    ATTR_ERROR,
    ATTR_LOCATION_HISTORY,
    ATTR_AVAILABLE,
    ATTR_CONNECTED,
    ATTR_LAST_COMM,
    ATTR_LAST_SEEN,
    ATTR_LAST_PULL,
    ATTR_LAST_STATE,
    ATTR_LAST_WAKE_UP,
    ATTR_LAST_TRACE_POSITION,
    API_BASE_URI,
    API_APP_TOKEN,
    API_DATETIME_FORMAT_DEFAULT,
    API_DATETIME_FORMAT_FALLBACK,
    API_ACK_TIMEOUT,
    UPDATE_INTERVAL_WORKING,
    UPDATE_INTERVAL_IDLING,
    UPDATE_INTERVAL_STANDBY,
    LOCATION_HISTORY_ITEMS,
    MANUFACTURER_DEFAULT,
    MANUFACTURER_MAP,
    ROBOT_WAKE_UP_INTERVAL_DEFAULT,
    ROBOT_WAKE_UP_INTERVAL_INFINITY,
    ROBOT_MODELS,
    ROBOT_STATES,
    ROBOT_STATES_WORKING,
    ROBOT_ERRORS,
    INFINITY_PLAN_STATES,
)


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class ZcsMowerDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the ZCS API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=config_entry.options.get(CONF_UPDATE_INTERVAL_IDLING, UPDATE_INTERVAL_IDLING)),
        )
        self.config_entry = config_entry
        self.client = ZcsMowerApiClient(
            session=async_get_clientsession(hass),
            options={
                "endpoint": API_BASE_URI,
                "app_id": config_entry.options.get(CONF_CLIENT_KEY, ""),
                "app_token": API_APP_TOKEN,
                "thing_key": config_entry.options.get(CONF_CLIENT_KEY, ""),
            }
        )
        self.mowers = dict(config_entry.options.get(CONF_MOWERS, []))

        self.data = {}
        for _imei, _mower in self.mowers.items():
            self.data[_imei] = {
                ATTR_IMEI: _imei,
                ATTR_NAME: _mower.get(ATTR_NAME, _imei),
                ATTR_INFINITY: None,
                ATTR_STATE: None,
                ATTR_ICON: None,
                ATTR_WORKING: False,
                ATTR_AVAILABLE: False,
                ATTR_ERROR: None,
                ATTR_LOCATION: {},
                ATTR_LOCATION_HISTORY: None,
                ATTR_SERIAL: None,
                ATTR_MANUFACTURER: MANUFACTURER_DEFAULT,
                ATTR_MODEL: None,
                ATTR_SW_VERSION: None,
                ATTR_CONNECTED: False,
                ATTR_LAST_COMM: None,
                ATTR_LAST_SEEN: None,
                ATTR_LAST_PULL: None,
                ATTR_LAST_STATE: None,
                ATTR_LAST_WAKE_UP: None,
                ATTR_LAST_TRACE_POSITION: None,
            }
        self._loop = asyncio.get_event_loop()
        self._scheduled_update_listeners: asyncio.TimerHandle | None = None

    def _convert_datetime_from_api(
        self,
        date_string: str,
    ) -> datetime:
        """Convert datetime string from API data into datetime object."""
        try:
            _dt = datetime.strptime(date_string, API_DATETIME_FORMAT_DEFAULT)
        except ValueError:
            _dt = datetime.strptime(date_string, API_DATETIME_FORMAT_FALLBACK)
        return dt_util.as_local(_dt)

    def _get_datetime_now(self) -> datetime:
        """Get current datetime in local time."""
        return dt_util.now()

    def _get_datetime_from_duration(
        self,
        duration: int,
    ) -> datetime:
        """Get datetime object by adding a duration to the current time."""
        return dt_util.now() + timedelta(minutes=duration)

    async def __aenter__(self):
        """Return Self."""
        return self

    async def __aexit__(self, *excinfo):
        """Close Session before class is destroyed."""
        await self.client._session.close()

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Update all mowers.
            await self.async_fetch_all_mowers()

            LOGGER.debug("_async_update_data")
            LOGGER.debug(self.data)

            # If one or more lawn mower(s) working, increase update_interval
            if self.has_working_mowers():
                suggested_update_interval = timedelta(seconds=self.config_entry.options.get(CONF_UPDATE_INTERVAL_WORKING, UPDATE_INTERVAL_WORKING))
            else:
                suggested_update_interval = timedelta(seconds=self.config_entry.options.get(CONF_UPDATE_INTERVAL_IDLING, UPDATE_INTERVAL_IDLING))
            # Set suggested update_interval
            if suggested_update_interval != self.update_interval:
                self.update_interval = suggested_update_interval
                LOGGER.info("Update update_interval to %s seconds, because lawn mower(s) changed state from idle to working or vice versa.", suggested_update_interval.total_seconds())
            return self.data
        except ZcsMowerApiAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ZcsMowerApiError as exception:
            raise UpdateFailed(exception) from exception

    async def _async_update_listeners(self) -> None:
        """Schedule update all registered listeners after 1 second."""
        if self._scheduled_update_listeners:
            self._scheduled_update_listeners.cancel()
        self._scheduled_update_listeners = self.hass.loop.call_later(
            1,
            lambda: self.async_update_listeners(),
        )

    def get_mower_attributes(
        self,
        imei: str,
    ) -> dict[str, any] | None:
        """Get attributes of an given lawn mower."""
        return self.data.get(imei, None)

    def init_location_history(
        self,
        imei: str,
    ) -> None:
        """Initiate location history for lawn mower."""
        if self.data[imei][ATTR_LOCATION_HISTORY] is None:
            self.data[imei][ATTR_LOCATION_HISTORY] = []

    def add_location_history(
        self,
        imei: str,
        location: tuple[float, float],
    ) -> bool:
        """Add item to location history."""
        if self.data[imei][ATTR_LOCATION_HISTORY] is None:
            return False

        location_history = self.data[imei][ATTR_LOCATION_HISTORY].copy()
        # Abort, if provided location is last item in location history
        if location in location_history[-1:]:
            return False

        location_history.append(location)
        self.data[imei][ATTR_LOCATION_HISTORY] = location_history[-LOCATION_HISTORY_ITEMS:]

        return True

    def has_working_mowers(
        self,
    ) -> bool:
        """Count the working lawn mowers."""
        count_helper = [v[ATTR_WORKING] for k, v in self.data.items() if v.get(ATTR_WORKING)]
        return len(count_helper) > 0

    async def async_fetch_all_mowers(
        self,
    ) -> None:
        """Fetch data for all mowers."""
        mower_imeis = list(self.data.keys())
        if len(mower_imeis) == 0:
            return None

        await self.client.execute(
            "thing.list",
            {
                "show": [
                    "id",
                    "key",
                    "name",
                    "connected",
                    "lastSeen",
                    "lastCommunication",
                    "loc",
                    "properties",
                    "alarms",
                    "attrs",
                    "createdOn",
                    "storage",
                    "varBillingPlanCode",
                ],
                "hideFields": True,
                "keys": mower_imeis,
            },
        )
        response = await self.client.get_response()
        if "result" in response:
            result_list = response["result"]
            for mower in (
                mower
                for mower in result_list
                if "key" in mower and mower["key"] in self.data
            ):
                await self.async_update_mower(mower)

    async def async_fetch_single_mower(
        self,
        imei: str,
    ) -> bool:
        """Fetch data for single mower, return connection state."""
        await self.client.execute(
            "thing.find",
            {
                "imei": imei,
            },
        )
        response = await self.client.get_response()
        await self.async_update_mower(response)

        # Always update HA states after a command was executed.
        # API calls that change the lawn mower's state update the local object when
        # executing the command, so only the HA state needs further updates.
        self.hass.async_create_task(
            self._async_update_listeners()
        )
        return response.get("connected", False)

    async def async_update_mower(
        self,
        data: dict[str, any],
    ) -> None:
        """Update a single mower."""
        imei = data.get("key", "")
        mower = self.get_mower_attributes(imei)
        if mower is None:
            return None
        # Start refreshing mower in coordinator from fetched API data
        if "alarms" in data:
            # Get robot state, error code and location
            if "robot_state" in data["alarms"]:
                robot_state = data["alarms"]["robot_state"]
                _state = (
                    robot_state["state"] if robot_state["state"] < len(ROBOT_STATES) else 0
                )
                mower[ATTR_STATE] = ROBOT_STATES[_state]["name"]
                mower[ATTR_ICON] = ROBOT_STATES[_state]["icon"]
                mower[ATTR_WORKING] = _state in list(ROBOT_STATES_WORKING)
                mower[ATTR_AVAILABLE] = _state > 0
                # msg not always available
                if "msg" in robot_state:
                    mower[ATTR_ERROR] = ROBOT_ERRORS.get(int(robot_state["msg"]), None)
                # latitude and longitude not always available
                if "lat" in robot_state and "lng" in robot_state:
                    latitude = float(robot_state["lat"])
                    longitude = float(robot_state["lng"])
                    mower[ATTR_LOCATION] = {
                        ATTR_LATITUDE: latitude,
                        ATTR_LONGITUDE: longitude,
                    }
                    self.add_location_history(
                        imei=imei,
                        location=(latitude, longitude),
                    )
            # Get Infinity+ status from lawn mower
            if "infinity_plan_status" in data["alarms"]:
                infinity_plan_status = data["alarms"]["infinity_plan_status"]
                _state = infinity_plan_status["state"] if infinity_plan_status["state"] < len(ROBOT_STATES) else None
                mower[ATTR_INFINITY] = INFINITY_PLAN_STATES[_state]["name"]
        if "attrs" in data:
            # In some cases, robot_serial is not available
            if "robot_serial" in data["attrs"]:
                mower[ATTR_SERIAL] = data["attrs"]["robot_serial"]["value"]
                if len(mower[ATTR_SERIAL]) > 5:
                    if mower[ATTR_SERIAL][0:2] in MANUFACTURER_MAP:
                        mower[ATTR_MANUFACTURER] = MANUFACTURER_MAP[mower[ATTR_SERIAL][0:2]]
                    mower[ATTR_MODEL] = mower[ATTR_SERIAL][0:6]
                    if mower[ATTR_MODEL] in ROBOT_MODELS:
                        mower[ATTR_MODEL] = ROBOT_MODELS[mower[ATTR_MODEL]]
            # In some cases, program_version is not available
            if "program_version" in data["attrs"]:
                _revision = data["attrs"]["program_version"]["value"]
                mower[ATTR_SW_VERSION] = f"r{_revision}"
        mower[ATTR_CONNECTED] = data.get("connected", False)
        if "lastCommunication" in data:
            mower[ATTR_LAST_COMM] = self._convert_datetime_from_api(data["lastCommunication"])
        if "lastSeen" in data:
            mower[ATTR_LAST_SEEN] = self._convert_datetime_from_api(data["lastSeen"])
        mower[ATTR_LAST_PULL] = self._get_datetime_now()

        # Lawn mower is working
        if mower.get(ATTR_WORKING, False):
            # Get inifity intervals, if Infinity+ is active
            if mower.get(ATTR_INFINITY) == "active":
                _wake_up_interval = self.config_entry.options.get(CONF_WAKE_UP_INTERVAL_INFINITY, ROBOT_WAKE_UP_INTERVAL_INFINITY)
            # Get default intervals, if Infinity+ is not active
            else:
                _wake_up_interval = self.config_entry.options.get(CONF_WAKE_UP_INTERVAL_DEFAULT, ROBOT_WAKE_UP_INTERVAL_DEFAULT)

            # Send a wake_up command every WAKE_UP_INTERVAL seconds
            if (
                mower.get(ATTR_LAST_WAKE_UP) is None
                or (self._get_datetime_now() - mower.get(ATTR_LAST_WAKE_UP)).total_seconds() > _wake_up_interval
            ):
                self.hass.async_create_task(
                    self.async_wake_up(imei)
                )
        # State changed
        if mower.get(ATTR_STATE) != mower.get(ATTR_LAST_STATE):
            # If lawn mower is now working
            # and position tracing is active
            # send a trace_position command
            if (
                mower.get(ATTR_WORKING, False)
                and self.config_entry.options.get(CONF_TRACE_POSITION_ENABLE, False)
            ):
                self.hass.async_create_task(
                    self.async_trace_position(imei)
                )
            # Set new state to last state
            mower[ATTR_LAST_STATE] = mower.get(ATTR_STATE)

        self.data[imei] = mower

    async def async_prepare_for_command(
        self,
        imei: str,
    ) -> bool:
        """Prepare lawn mower for incomming command."""
        try:
            # Use connection state from last fetch if last pull was not longer than 10 seconds ago
            mower = self.get_mower_attributes(imei)
            last_pull = mower.get(ATTR_LAST_PULL, None)
            last_wake_up = mower.get(ATTR_LAST_WAKE_UP, None)

            if (
                last_pull is not None
                and (self._get_datetime_now() - last_pull).total_seconds() < 10
                and mower.get(ATTR_CONNECTED, False)
            ):
                return True

            # Fetch connection state fresh from API
            connected = await self.async_fetch_single_mower(imei)
            if connected is True:
                return True

            # Send wake up command if last attempt was more than 60 seconds ago
            if (
                last_wake_up is None
                or (self._get_datetime_now() - last_wake_up).total_seconds() > 60
            ):
                await self.async_wake_up(imei)

            # Wait 5 seconds before the loop starts
            await asyncio.sleep(5)

            attempt = 0
            while connected is False and attempt <= 5:
                connected = await self.async_fetch_single_mower(imei)
                if connected is True:
                    return True
                attempt = attempt + 1
                # Wait 5 seconds before next attempt
                await asyncio.sleep(5)
            raise asyncio.TimeoutError(
                f"The lawn mower with IMEI {imei} was not available after a long wait"
            )
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_wake_up(
        self,
        imei: str,
    ) -> bool:
        """Send command wake_up to lawn nower."""
        LOGGER.debug("wake_up: %s", imei)
        try:
            self.data[imei][ATTR_LAST_WAKE_UP] = self._get_datetime_now()
            return await self.client.execute(
                "sms.send",
                {
                    "coding": "SEVEN_BIT",
                    "imei": imei,
                    "message": "UP",
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)
        return False

    async def async_set_profile(
        self,
        imei: str,
        profile: int,
    ) -> bool:
        """Send command set_profile to lawn nower."""
        LOGGER.debug("set_profile: %s", imei)
        try:
            await self.async_prepare_for_command(imei)
            return await self.client.execute(
                "method.exec",
                {
                    "method": "set_profile",
                    "imei": imei,
                    "params": {
                        "profile": (profile - 1),
                    },
                    "ackTimeout": API_ACK_TIMEOUT,
                    "singleton": True,
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_work_now(
        self,
        imei: str,
    ) -> bool:
        """Send command work_now to lawn nower."""
        LOGGER.debug("work_now: %s", imei)
        try:
            await self.async_prepare_for_command(imei)
            return await self.client.execute(
                "method.exec",
                {
                    "method": "work_now",
                    "imei": imei,
                    "ackTimeout": API_ACK_TIMEOUT,
                    "singleton": True,
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_work_for(
        self,
        imei: str,
        duration: int,
        area: int | None = None,
    ) -> bool:
        """Prepare command work_for."""
        LOGGER.debug("work_for: %s", imei)
        _target = self._get_datetime_from_duration(duration)
        LOGGER.debug(_target)
        await self.async_work_until(
            imei=imei,
            hours=_target.hour,
            minutes=_target.minute,
            area=area,
        )

    async def async_work_until(
        self,
        imei: str,
        hours: int,
        minutes: int,
        area: int | None = None,
    ) -> bool:
        """Send command work_until to lawn nower."""
        LOGGER.debug("work_until: %s", imei)
        _params = {
            "hh": hours,
            "mm": minutes,
        }
        if isinstance(area, int) and area in range(1, 9):
            _params["area"] = area - 1
        else:
            _params["area"] = 255
        try:
            await self.async_prepare_for_command(imei)
            return await self.client.execute(
                "method.exec",
                {
                    "method": "work_until",
                    "imei": imei,
                    "params": _params,
                    "ackTimeout": API_ACK_TIMEOUT,
                    "singleton": True,
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_border_cut(
        self,
        imei: str,
    ) -> bool:
        """Send command border_cut to lawn nower."""
        LOGGER.debug("border_cut: %s", imei)
        try:
            await self.async_prepare_for_command(imei)
            return await self.client.execute(
                "method.exec",
                {
                    "method": "border_cut",
                    "imei": imei,
                    "ackTimeout": API_ACK_TIMEOUT,
                    "singleton": True,
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_charge_now(
        self,
        imei: str,
    ) -> bool:
        """Send command charge_now to lawn nower."""
        LOGGER.debug("charge_now: %s", imei)
        try:
            await self.async_prepare_for_command(imei)
            return await self.client.execute(
                "method.exec",
                {
                    "method": "charge_now",
                    "imei": imei,
                    "ackTimeout": API_ACK_TIMEOUT,
                    "singleton": True,
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_charge_for(
        self,
        imei: str,
        duration: int,
    ) -> bool:
        """Prepare command charge_until."""
        LOGGER.debug("charge_for: %s", imei)
        _target = self._get_datetime_from_duration(duration)
        LOGGER.debug(_target)
        await self.async_charge_until(
            imei=imei,
            hours=_target.hour,
            minutes=_target.minute,
            weekday=_target.isoweekday(),
        )

    async def async_charge_until(
        self,
        imei: str,
        hours: int,
        minutes: int,
        weekday: int,
    ) -> bool:
        """Send command charge_until to lawn nower."""
        LOGGER.debug("charge_until: %s", imei)
        try:
            await self.async_prepare_for_command(imei)
            return await self.client.execute(
                "method.exec",
                {
                    "method": "charge_until",
                    "imei": imei,
                    "params": {
                        "hh": hours,
                        "mm": minutes,
                        "weekday": (weekday - 1),
                    },
                    "ackTimeout": API_ACK_TIMEOUT,
                    "singleton": True,
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_trace_position(
        self,
        imei: str,
    ) -> bool:
        """Send command trace_position to lawn nower."""
        LOGGER.debug("trace_position: %s", imei)
        try:
            self.data[imei][ATTR_LAST_TRACE_POSITION] = self._get_datetime_now()
            await self.async_prepare_for_command(imei)
            return await self.client.execute(
                "method.exec",
                {
                    "method": "trace_position",
                    "imei": imei,
                    "ackTimeout": API_ACK_TIMEOUT,
                    "singleton": True,
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_keep_out(
        self,
        imei: str,
        latitude: float,
        longitude: float,
        radius: int,
        hours: int | None = None,
        minutes: int | None = None,
        index: int | None = None,
    ) -> bool:
        """Send command keep_out to lawn nower."""
        LOGGER.debug("keep_out: %s", imei)
        _params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
        }
        if isinstance(hours, int) and hours in range(0, 24):
            _params["hh"] = hours
        if isinstance(minutes, int) and minutes in range(0, 60):
            _params["mm"] = minutes
        if isinstance(index, int):
            _params["index"] = index
        try:
            await self.async_prepare_for_command(imei)
            return await self.client.execute(
                "method.exec",
                {
                    "method": "keep_out",
                    "imei": imei,
                    "params": _params,
                    "ackTimeout": API_ACK_TIMEOUT,
                    "singleton": True,
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)

    async def async_custom_command(
        self,
        imei: str,
        command: str,
        params: dict[str, any] | list[any] | None = None,
    ) -> bool:
        """Send custom command to lawn nower."""
        LOGGER.debug("custom_command: %s", imei)
        LOGGER.debug(command)
        LOGGER.debug(params)
        try:
            await self.async_prepare_for_command(imei)
            return await self.client.execute(
                "method.exec",
                {
                    "method": command,
                    "imei": imei,
                    "params": params,
                    "ackTimeout": API_ACK_TIMEOUT,
                    "singleton": True,
                },
            )
        except Exception as exception:
            LOGGER.exception(exception)
