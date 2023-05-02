"""DataUpdateCoordinator for ZCS Lawn Mower Robot."""
from __future__ import annotations

from datetime import (
    timedelta,
    datetime,
)
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_NAME,
    ATTR_LOCATION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_STATE,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import (
    ZcsMowerApiClient,
    ZcsMowerApiAuthenticationError,
    ZcsMowerApiError,
)
from .const import (
    DOMAIN,
    LOGGER,
    ATTR_IMEI,
    ATTR_SERIAL,
    ATTR_CONNECTED,
    ATTR_LAST_COMM,
    ATTR_LAST_SEEN,
)


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class ZcsMowerDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the ZCS API."""

    def __init__(
        self,
        mowers: dict,
        hass: HomeAssistant,
        client: ZcsMowerApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.mowers = mowers
        self.client = client

    async def __aenter__(self):
        """Return Self."""
        return self

    async def __aexit__(self, *excinfo):
        """Close Session before class is destroyed."""
        await self.client._session.close()

    async def _async_update_data(self):
        """Update data via library."""
        try:
            mower_data = {}
            mower_imeis = []
            for _imei, _name in self.mowers.items():
                mower_imeis.append(_imei)
                mower_data[_imei] = {
                    ATTR_NAME: _name,
                    ATTR_IMEI: _imei,
                    ATTR_SERIAL: None,
                    ATTR_STATE: 0,
                    ATTR_LOCATION: None,
                    ATTR_CONNECTED: False,
                    ATTR_LAST_COMM: None,
                    ATTR_LAST_SEEN: None,
                }
            
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
                        "varBillingPlanCode"
                    ],
                    "hideFields": True,
                    "keys": mower_imeis
                },
            )
            response = await self.client.get_response()
            if "result" in response:
                result_list = response["result"]
                for mower in (
                    mower
                    for mower in result_list
                    if "key" in mower and mower["key"] in mower_data
                ):
                    if "alarms" in mower and "robot_state" in mower["alarms"]:
                        robot_state = mower["alarms"]["robot_state"]
                        mower_data[mower["key"]][ATTR_STATE] = robot_state["state"]
                        # latitude and longitude, not always available
                        if "lat" in robot_state and "lng" in robot_state:
                            mower_data[mower["key"]][ATTR_LOCATION] = {
                                ATTR_LATITUDE: robot_state["lat"],
                                ATTR_LONGITUDE: robot_state["lng"],
                            }
                        # robot_state["since"] -> timestamp since state change (format 2023-04-30T10:24:47.517Z)
                    if "attrs" in mower and "robot_serial" in mower["attrs"]:
                        robot_serial = mower["attrs"]["robot_serial"]
                        mower_data[mower["key"]][ATTR_SERIAL] = robot_serial["value"]

            # TODO
            LOGGER.debug("_async_update_data")
            LOGGER.debug(mower_data)

            return mower_data
        except ZcsMowerApiAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ZcsMowerApiError as exception:
            raise UpdateFailed(exception) from exception
