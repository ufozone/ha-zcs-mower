"""ZCS Lawn Mower Robot API Client.

https://github.com/deviceWISE/sample_tr50_python
"""
from __future__ import annotations

import socket

import aiohttp
import async_timeout
import json

from .const import LOGGER


class ZcsMowerApiError(Exception):
    """Exception to indicate a general API error."""


class ZcsMowerApiCommunicationError(ZcsMowerApiError):
    """Exception to indicate a communication error."""


class ZcsMowerApiAuthenticationError(ZcsMowerApiError):
    """Exception to indicate an authentication error."""


class ZcsMowerApiClient:
    """Sample API Client."""

    # The API endpoint for POSTing (e.g. https://www.example.com/api)
    _endpoint = ""

    # The application identifier you will be using.
    _app_id = ""

    # The application token.
    _app_token = ""

    # The thing key used to identify the application.
    _thing_key = ""

    # Holds the current session identifier.
    _session_id = ""

    # If the last request succeeded or failed.
    _status = None

    # Holds the response data from the API call.
    _response = []

    # Holds any error returned by the API.
    _error = []

    def __init__(
        self,
        session: aiohttp.ClientSession,
        options: {},
    ) -> None:
        """Initialize API."""
        self._session = session

        if "endpoint" in options:
            self._endpoint = options["endpoint"]

        if "app_id" in options:
            self._app_id = options["app_id"]
        if "app_token" in options:
            self._app_token = options["app_token"]
        if "thing_key" in options:
            self._thing_key = options["thing_key"]

        if "session_id" in options:
            self._session_id = options["session_id"]

    async def check_robot(
        self,
        imei: str
    ) -> any:
        """Check given IMEI against the API."""
        result = await self.execute(
            "thing.find",
            {
                "imei": imei
            }
        )
        if result is True and self._response["data"]["success"] is True:
            return await self.get_response()
        else:
            raise ZcsMowerApiCommunicationError(
                "Lawn mower not found. Please check the application configuration."
            )

    # This method sends the TR50 request to the server and parses the response.
    # https://github.com/deviceWISE/sample_tr50_python
    # @param    mixed    data     JSON command and arguments. This parameter can also
    #                             be a dict that will be converted to a JSON string.
    # @return   bool     Success or failure to post.
    async def post(
        self,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> bool:
        """Send the TR50 request to the server and parses the response.

        Args:
            data (dict | None): JSON command and arguments to send.
            headers (dict | None): Headers to send.

        Returns:
            bool: Success or failure to post.

        """
        self._error = []
        self._status = True
        self._response = ""

        if not isinstance(data, dict):
            data = json.loads(data)

        data = await self.set_json_auth(data)
        LOGGER.debug("API.request:")
        LOGGER.debug(data)

        try:
            async with async_timeout.timeout(60):
                response = await self._session.request(
                    method="POST",
                    url=self._endpoint,
                    headers=headers,
                    json=data,
                )
                if not response.status == 200:
                    raise ZcsMowerApiError(
                        "Failed to POST to API"
                    )
                response.raise_for_status()

                self._response = await response.json()

                if "errorMessages" in self._response:
                    self._error = self._response["errorMessages"]

                if "success" in self._response:
                    self._status = self._response["success"]
                elif "data" in self._response and "success" in self._response["data"]:
                    self._status = self._response["data"]["success"]
                elif "auth" in self._response and "success" in self._response["auth"]:
                    self._status = self._response["auth"]["success"]

                LOGGER.debug("API.response:")
                LOGGER.debug(self._response)

                # If _status is True
                if self._status:
                    return self._status
                # Else _status is False
                else:
                    # If session is invalid, refresh authentication and execute command
                    # again possible loop, if authentication session is always invalid
                    # after successful refresh
                    if len([
                        error
                        for error in self._error
                        if "Authentication session is invalid: Error: Session " in error
                    ]) > 0:
                        refresh_auth = await self.auth()
                        if refresh_auth:
                            data["auth"]["sessionId"] = self._session_id
                            return await self.post(data, headers)

                    raise ZcsMowerApiCommunicationError(self._error)
        except ZcsMowerApiCommunicationError as exception:
            raise ZcsMowerApiCommunicationError(
                f"Communication failed: {exception}"
            ) from exception
        except TimeoutError as exception:
            raise ZcsMowerApiCommunicationError(
                "Timeout error fetching information",
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise ZcsMowerApiCommunicationError(
                "Error fetching information",
            ) from exception
        except Exception as exception:
            raise ZcsMowerApiError(
                "Something really wrong happened!"
            ) from exception

    # Package the command and the params into an array and sends the command to the
    # configured endpoint for processing.
    # https://github.com/deviceWISE/sample_tr50_python
    # @param    command    string    The TR50 command to execute.
    # @param    params     dict      The command parameters.
    # @return   bool       Success or failure to post.
    async def execute(
        self,
        command: str,
        params: dict | bool = False
    ) -> bool:
        """Execute commands agains the deviceWISE API.

        Package the command and the params into an array and sends the
        command to the configured endpoint for processing.

        Args:
            command (str): The TR50 command to execute.
            params (dict): The command parameters.

        Returns:
            bool: Successor failure to post.

        """
        if command == "api.authenticate":
            parameters = {
                "auth" : {
                    "command" : "api.authenticate",
                    "params" : params
                }
            }
        else:
            parameters = {
                "data" : {
                    "command" : command
                }
            }
            if params is not False:
                parameters["data"]["params"] = params

        return await self.post(parameters)

    # Depending on the configuration, authenticate the app or the user, prefer the app.
    # https://github.com/deviceWISE/sample_tr50_python
    # @return    bool    Success or failure to authenticate.
    async def auth(
        self
    ) -> bool:
        """Depending on the configuration, authenticate the app."""
        if (
            len(self._app_id) > 0
            and len(self._app_token) > 0
            and len(self._thing_key) > 0
        ):
            return await self.app_auth(self._app_id, self._app_token, self._thing_key)
        return False

    # Authenticate the application.
    # https://github.com/deviceWISE/sample_tr50_python
    # @param     string    app_id                The application ID.
    # @param     string    app_token             The application token.
    # @param     string    thing_key             The key of the application's thing.
    # @param     bool      update_session_id     Update the object session ID.
    # @return    bool      Success or failure to authenticate.
    async def app_auth(
        self,
        app_id: str,
        app_token: str,
        thing_key: str,
        update_session_id: bool = True
    ) -> bool:
        """Authenticate the application."""
        try:
            params = {
                "appId": app_id,
                "appToken": app_token,
                "thingKey": thing_key
            }
            response = await self.execute("api.authenticate", params)
            if response is True:
                if update_session_id:
                    self._session_id = self._response["auth"]["params"]["sessionId"]
                return True
            return False
        except ZcsMowerApiCommunicationError as exception:
            raise ZcsMowerApiAuthenticationError(
                "Authorization failed. Please check the application configuration.",
            ) from exception
        except Exception as exception:
            raise exception

    # Return the response data for the last command if the last command was successful.
    # https://github.com/deviceWISE/sample_tr50_python
    # @return    dict    The response data.
    async def get_response(
        self
    ) -> any:
        """Return the response data for the last command if the last command was successful."""
        if (
            self._status
            and len(self._response["data"]) > 0
            and "params" in self._response["data"]
        ):
            return self._response["data"]["params"]
        return None

    # This method checks the JSON command for the auth parameter. If it is not set, it adds.
    # https://github.com/deviceWISE/sample_tr50_python
    # @param    mixed    data    A JSON string or the dict representation of JSON.
    # @return   string   A JSON string with the auth parameter.
    async def set_json_auth(
        self,
        data: str
    ) -> str:
        """Check the JSON command for the auth parameter. If it is not set, it adds."""
        if not isinstance(data, dict):
            data = json.loads(data)

        if "auth" not in data:
            if len(self._session_id) == 0:
                await self.auth()
            # If it is still empty, we cannot proceed
            if len(self._session_id) == 0:
                raise ZcsMowerApiAuthenticationError(
                    "Authorization failed. Please check the application configuration."
                )
            data["auth"] = {
                "sessionId" : self._session_id
            }
        return data
