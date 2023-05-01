"""DataUpdateCoordinator for ZCS Lawn Mower Robot."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    ROBOT_STATES,
)


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class ZcsMowerDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the ZCS API."""

    config_entry: ConfigEntry

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

    async def _async_update_data(self):
        """Update data via library."""
        try:
            mower_data = {}
            mower_imeis = []
            for _imei, _name in self.mowers.items():
                mower_imeis.append(_imei)
                mower_data[_imei] = {
                    "name": _name,
                    "imei": _imei,
                    "state": 0,
                    "location": {
                        "latitude": None,
                        "longitude": None,
                    },
                }
            
            result = await self.client.execute("thing.list", {
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
            })
            response = await self.client.get_response()
            if "result" in response:
                result_list = response["result"]
                #for i in range(len(result_list)):
                #    mower = result_list[i]
                for mower in result_list:
                    if "key" in mower and "alarms" in mower:
                        if "robot_state" in mower["alarms"] and mower["key"] in mower_data:
                            robot_state = mower["alarms"]["robot_state"]
                            mower_data[mower["key"]]["state"] = robot_state["state"]
                            # latitude and longitude, not always available
                            if "lat" in robot_state and "lng" in robot_state:
                                mower_data[mower["key"]]["location"]["latitude"] = robot_state["lat"]
                                mower_data[mower["key"]]["location"]["longitude"] = robot_state["lng"]
                            # robot_state["since"] -> timestamp since state change (format 2023-04-30T10:24:47.517Z)
            
            # TODO
            LOGGER.debug("_async_update_data")
            LOGGER.debug(mower_data)
            
            
            return mower_data
        except ZcsMowerApiAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ZcsMowerApiError as exception:
            raise UpdateFailed(exception) from exception
