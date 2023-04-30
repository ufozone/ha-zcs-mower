"""
ZCS API Client
"""
import aiohttp

from .api import (
    ZcsMowerApi,
    ZcsMowerApiAuthenticationError,
    ZcsMowerApiCommunicationError,
    ZcsMowerApiError,
)
from .const import (
    LOGGER,
    DOMAIN,
)

class ZcsMowerApiClient(ZcsMowerApi):
    def __init__(
        self,
        session: aiohttp.ClientSession,
        options: {},
    ) -> None:
        """Initialize API Client"""
        ZcsMowerApi.__init__(
            self,
            session,
            options
        )
    
    # thing.find : This command is used to find and return a thing.
    # @param     string    thing_key   Identifies the thing.
    # @return    mixed     Returns the array of the selected thing on success, or the failure code.
    async def thing_find(
        self,
        thing_key: str
    ) -> any:
        """This command is used to find and return a thing."""
        
        result = await self.execute("thing.find", {
            "key": thing_key
        })
        if result == True and self._response["data"]["success"] == True:
            return self._response["data"]["params"]
        else:
            raise ZcsMowerApiAuthenticationError(
                "Authorization failed. Please check the application configuration."
            )
