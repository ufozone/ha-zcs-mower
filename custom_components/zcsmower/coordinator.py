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
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.recorder import (
    get_instance,
    history,
)
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
    CONF_STANDBY_TIME_START,
    CONF_STANDBY_TIME_STOP,
    CONF_UPDATE_INTERVAL_WORKING,
    CONF_UPDATE_INTERVAL_STANDBY,
    CONF_UPDATE_INTERVAL_IDLING,
    CONF_UPDATE_INTERVAL_HIBERNATION,
    CONF_TRACE_POSITION_ENABLE,
    CONF_WAKE_UP_INTERVAL_DEFAULT,
    CONF_WAKE_UP_INTERVAL_INFINITY,
    CONF_HIBERNATION_ENABLE,
    CONF_MOWERS,
    ATTR_IMEI,
    ATTR_DATA_THRESHOLD,
    ATTR_CONNECT_EXPIRATION,
    ATTR_INFINITY_STATE,
    ATTR_INFINITY_EXPIRATION,
    ATTR_SERIAL_NUMBER,
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
    API_WAIT_FOR_CONNECTION,
    STANDBY_TIME_START_DEFAULT,
    STANDBY_TIME_STOP_DEFAULT,
    CONFIGURATION_DEFAULTS,
    LOCATION_HISTORY_DAYS_DEFAULT,
    LOCATION_HISTORY_ITEMS_DEFAULT,
    MANUFACTURER_DEFAULT,
    MANUFACTURER_MAP,
    ROBOT_MODELS,
    ROBOT_STATES,
    ROBOT_STATES_WORKING,
    ROBOT_ERRORS,
    DATA_THRESHOLD_STATES,
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
            update_interval=timedelta(
                seconds=config_entry.options.get(
                    CONF_UPDATE_INTERVAL_STANDBY,
                    CONFIGURATION_DEFAULTS.get(CONF_UPDATE_INTERVAL_STANDBY).get("default"),
                )
            ),
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
                ATTR_STATE: None,
                ATTR_DATA_THRESHOLD: None,
                ATTR_CONNECT_EXPIRATION: None,
                ATTR_INFINITY_STATE: None,
                ATTR_INFINITY_EXPIRATION: None,
                ATTR_ICON: None,
                ATTR_WORKING: False,
                ATTR_AVAILABLE: False,
                ATTR_ERROR: None,
                ATTR_LOCATION: {},
                ATTR_LOCATION_HISTORY: None,
                ATTR_SERIAL_NUMBER: None,
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

        self.hibernation_enable = self.config_entry.options.get(CONF_HIBERNATION_ENABLE, False)
        self.standby_time_start = datetime.strptime(
            config_entry.options.get(CONF_STANDBY_TIME_START, STANDBY_TIME_START_DEFAULT),
            "%H:%M:%S"
        )
        self.standby_time_stop = datetime.strptime(
            config_entry.options.get(CONF_STANDBY_TIME_STOP, STANDBY_TIME_STOP_DEFAULT),
            "%H:%M:%S"
        )
        self.next_pull = None

        self._loop = asyncio.get_event_loop()
        self._scheduled_update_listeners: asyncio.TimerHandle | None = None
        self._scheduled_update_entry: asyncio.TimerHandle | None = None

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

    async def initialize(self) -> None:
        """Set up a ZCS Mower instance."""
        await self.client.auth()

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

            # Set update interval
            self.set_update_interval()

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

    async def async_set_entry_option(
        self,
        key: str,
        value: any,
    ) -> None:
        """Set config entry option and update config entry after 3 second."""
        _options = dict(self.config_entry.options)
        _options.update(
            {
                key: value
            }
        )
        if self._scheduled_update_entry:
            self._scheduled_update_entry.cancel()
        self._scheduled_update_entry = self.hass.loop.call_later(
            3,
            lambda: self.hass.config_entries.async_update_entry(
                self.config_entry, options=_options
            ),
        )

    def get_mower_attributes(
        self,
        imei: str,
    ) -> dict[str, any] | None:
        """Get attributes of an given lawn mower."""
        return self.data.get(imei, None)

    async def init_location_history(
        self,
        entity_id: str,
        imei: str,
    ) -> None:
        """Initiate location history for lawn mower."""
        # Load Recorder after loading entity
        await get_instance(self.hass).async_add_executor_job(
            self.get_location_history,
            entity_id,
            imei,
        )
        # Always update HA states after getting location history.
        self.hass.async_create_task(
            self._async_update_listeners()
        )

    def get_location_history(
        self,
        entity_id: str,
        imei: str,
    ) -> None:
        """Get location history for lawn mower."""
        if self.data[imei][ATTR_LOCATION_HISTORY] is None:
            self.data[imei][ATTR_LOCATION_HISTORY] = []

        # Getting history with history.get_last_state_changes can cause instability
        # because it has to scan the table to find the last number_of_states states
        # because the metadata_id_last_updated_ts index is in ascending order.
        history_list = history.state_changes_during_period(
            self.hass,
            start_time=self._get_datetime_now() - timedelta(days=LOCATION_HISTORY_DAYS_DEFAULT),
            entity_id=entity_id,
            no_attributes=False,
            include_start_time_state=True,
        )
        for state in history_list.get(entity_id, []):
            if state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None):
                latitude = state.attributes.get(ATTR_LATITUDE, None)
                longitude = state.attributes.get(ATTR_LONGITUDE, None)
                if latitude and longitude:
                    self.add_location_history(
                        imei=imei,
                        location=(latitude, longitude),
                    )

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
        self.data[imei][ATTR_LOCATION_HISTORY] = location_history[-LOCATION_HISTORY_ITEMS_DEFAULT:]

        return True

    def has_working_mowers(
        self,
    ) -> bool:
        """Count the working lawn mowers."""
        count_helper = [v[ATTR_WORKING] for k, v in self.data.items() if v.get(ATTR_WORKING)]
        return len(count_helper) > 0

    def is_standby_time(
        self,
        time: datetime | None = None,
    ) -> bool:
        """Return true if current time is in the standby time range."""
        _standby_time_start = dt_util.as_local(self.standby_time_start)
        _standby_time_stop = dt_util.as_local(self.standby_time_stop)
        if time is None:
            time = self._get_datetime_now()
        if _standby_time_start <= _standby_time_stop:
            return _standby_time_start.time() <= time.time() <= _standby_time_stop.time()
        else:
            return _standby_time_start.time() <= time.time() or time.time() <= _standby_time_stop.time()

    def set_update_interval(
        self,
    ) -> bool:
        """Set calculated update interval."""
        now = self._get_datetime_now()

        # If one or more lawn mower(s) working, increase update_interval
        if self.has_working_mowers():
            LOGGER.debug("Set update_interval: Working")
            suggested_update_interval = timedelta(
                seconds=self.config_entry.options.get(
                    CONF_UPDATE_INTERVAL_WORKING,
                    CONFIGURATION_DEFAULTS.get(CONF_UPDATE_INTERVAL_WORKING).get("default")
                )
            )
        # If hibernation is enabled, decrease update_interval
        elif self.hibernation_enable:
            LOGGER.debug("Set update_interval: Hibernation")
            suggested_update_interval = timedelta(
                seconds=self.config_entry.options.get(
                    CONF_UPDATE_INTERVAL_HIBERNATION,
                    CONFIGURATION_DEFAULTS.get(CONF_UPDATE_INTERVAL_HIBERNATION).get("default")
                )
            )
        # If current time is in standby time, decrease update_interval
        elif self.is_standby_time(now):
            LOGGER.debug("Set update_interval: Standby")
            suggested_update_interval = timedelta(
                seconds=self.config_entry.options.get(
                    CONF_UPDATE_INTERVAL_STANDBY,
                    CONFIGURATION_DEFAULTS.get(CONF_UPDATE_INTERVAL_STANDBY).get("default")
                )
            )
        # If current time is out of standby time, calculate update_interval
        else:
            LOGGER.debug("Set update_interval: Idle")
            suggested_update_interval = timedelta(
                seconds=self.config_entry.options.get(
                    CONF_UPDATE_INTERVAL_IDLING,
                    CONFIGURATION_DEFAULTS.get(CONF_UPDATE_INTERVAL_IDLING).get("default")
                )
            )
            time_to_standby = (dt_util.as_local(self.standby_time_start) - now).seconds

            # Time until start of standby time is shorter than update_interval for idle time
            if time_to_standby < suggested_update_interval.seconds:
                LOGGER.debug("Set update_interval: Time until start of standby time is shorter than update_interval for idle time")
                # If time to standby is shorter than update_interval for working time
                if (time_to_standby < (interval_working := self.config_entry.options.get(
                    CONF_UPDATE_INTERVAL_WORKING,
                    CONFIGURATION_DEFAULTS.get(CONF_UPDATE_INTERVAL_WORKING).get("default"))
                )):
                    LOGGER.debug("Set update_interval: Time to standby is shorter than update_interval for working time")
                    time_to_standby = interval_working

                suggested_update_interval = timedelta(
                    seconds=time_to_standby
                )

        # Set next_pull
        self.next_pull = now + suggested_update_interval

        # Set suggested update_interval
        if suggested_update_interval != self.update_interval:
            self.update_interval = suggested_update_interval
            LOGGER.info("Set update_interval to %s seconds.", suggested_update_interval.total_seconds())
            return True
        return False

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
            # Get data threshold status from lawn mower
            if "data_th" in data["alarms"]:
                data_th = data["alarms"]["data_th"]
                _state = data_th["state"] if data_th["state"] < len(DATA_THRESHOLD_STATES) else 0
                mower[ATTR_DATA_THRESHOLD] = DATA_THRESHOLD_STATES[_state]["name"]
            # Get +Infinity status from lawn mower
            if "infinity_plan_status" in data["alarms"]:
                infinity_plan_status = data["alarms"]["infinity_plan_status"]
                _state = infinity_plan_status["state"] if infinity_plan_status["state"] < len(INFINITY_PLAN_STATES) else 0
                mower[ATTR_INFINITY_STATE] = INFINITY_PLAN_STATES[_state]["name"]
        if "attrs" in data:
            # In most cases, expiration_date is not available
            if "expiration_date" in data["attrs"]:
                expiration_date = data["attrs"]["expiration_date"]
                mower[ATTR_CONNECT_EXPIRATION] = self._convert_datetime_from_api(expiration_date["value"])
            # If only the created_on date is available, calculate expiration date
            elif "created_on" in data["attrs"]:
                created_on = data["attrs"]["created_on"]
                mower[ATTR_CONNECT_EXPIRATION] = self._convert_datetime_from_api(created_on["value"]) + timedelta(days=730)
            # In most cases, infinity_expiration_date is not available
            if "infinity_expiration_date" in data["attrs"]:
                infinity_expiration_date = data["attrs"]["infinity_expiration_date"]
                mower[ATTR_INFINITY_EXPIRATION] = self._convert_datetime_from_api(infinity_expiration_date["value"])
            # In some cases, robot_serial is not available
            if "robot_serial" in data["attrs"]:
                mower[ATTR_SERIAL_NUMBER] = data["attrs"]["robot_serial"]["value"]
                if len(mower[ATTR_SERIAL_NUMBER]) > 5:
                    if mower[ATTR_SERIAL_NUMBER][0:2] in MANUFACTURER_MAP:
                        mower[ATTR_MANUFACTURER] = MANUFACTURER_MAP[mower[ATTR_SERIAL_NUMBER][0:2]]
                    mower[ATTR_MODEL] = mower[ATTR_SERIAL_NUMBER][0:6]
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
            # Get inifity interval, if +Infinity is active or pending and valid
            if mower.get(ATTR_INFINITY_STATE) in ("active", "pending") and mower.get(ATTR_INFINITY_EXPIRATION) > self._get_datetime_now():
                _wake_up_interval = self.config_entry.options.get(
                    CONF_WAKE_UP_INTERVAL_INFINITY,
                    CONFIGURATION_DEFAULTS.get(CONF_WAKE_UP_INTERVAL_INFINITY).get("default")
                )
            # Get default interval, if +Infinity is not active
            else:
                _wake_up_interval = self.config_entry.options.get(
                    CONF_WAKE_UP_INTERVAL_DEFAULT,
                    CONFIGURATION_DEFAULTS.get(CONF_WAKE_UP_INTERVAL_DEFAULT).get("default")
                )

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

        # Wait 10 seconds before the loop starts
        await asyncio.sleep(10)

        attempt = 0
        # Wait for connection state to be True, but max 10 attempts
        while connected is False and attempt <= 10:
            connected = await self.async_fetch_single_mower(imei)
            if connected is True:
                return True
            attempt = attempt + 1
            # Wait calculated seconds before next attempt
            await asyncio.sleep((API_WAIT_FOR_CONNECTION - 10) / 10)

        raise TimeoutError(
            f"The lawn mower with IMEI {imei} was not available after a long wait"
        )

    async def async_update_now(
        self,
        imei: str,
    ) -> bool:
        """Fetch data for mower from API."""
        LOGGER.debug("update_now: %s", imei)
        try:
            return await self.async_fetch_single_mower(imei)
        except Exception as exception:
            LOGGER.exception(exception)
        return False

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
        except TimeoutError as exception:
            LOGGER.error(exception)
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
        except TimeoutError as exception:
            LOGGER.error(exception)
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
        except TimeoutError as exception:
            LOGGER.error(exception)
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
        except TimeoutError as exception:
            LOGGER.error(exception)
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
        except TimeoutError as exception:
            LOGGER.error(exception)
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
        except TimeoutError as exception:
            LOGGER.error(exception)
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
        except TimeoutError as exception:
            LOGGER.error(exception)
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
        except TimeoutError as exception:
            LOGGER.error(exception)
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
        except TimeoutError as exception:
            LOGGER.error(exception)
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
        except TimeoutError as exception:
            LOGGER.error(exception)
        except Exception as exception:
            LOGGER.exception(exception)
