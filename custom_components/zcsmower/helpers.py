"""ZCS Lawn Mower Robot helpers."""
from __future__ import annotations

import string
import random

from .const import (
    API_APP_TOKEN,
    API_CLIENT_KEY_LENGTH,
)
from .api import (
    ZcsApiClient,
    ZcsApiAuthenticationError,
    ZcsApiCommunicationError,
)


async def generate_client_key() -> str:
    """Generate client key."""
    # get random client key with letters and digits
    return "".join(
        random.choice(string.ascii_lowercase + string.digits)
        for i in range(API_CLIENT_KEY_LENGTH)
    )


async def get_client_key(
    client: ZcsApiClient,
) -> str:
    """Generate, validate and return client key."""
    attempts = 0
    while True:
        attempts += 1
        try:
            client_key = await generate_client_key()
            result = await client.app_auth(client_key, API_APP_TOKEN, client_key)
        except ZcsApiAuthenticationError:
            result = False

        # Login with generated client key is successfull
        if result:
            break
        # Max attempts reached
        if attempts > 10:
            raise ZcsApiCommunicationError("Too many attempts to generate a client key have failed.")

    return client_key


async def publish_client_thing(
    client: ZcsApiClient,
    client_key: str,
    client_name: str,
) -> None:
    """Publish client name."""
    await client.execute(
        "thing.find",
        {
            "key": client_key,
        },
    )
    if await client.get_response():
        await client.execute(
            "thing.update",
            {
                "key": client_key,
                "name": client_name,
            },
        )
    else:
        await client.execute(
            "thing.create",
            {
                "defKey": "client",
                "key": client_key,
                "name": client_name,
            },
        )


async def validate_imei(
    client: ZcsApiClient,
    imei: str,
) -> dict:
    """Validate a lawn mower IMEI.

    Raises a ValueError if the IMEI is invalid.
    """
    if not imei.startswith("35") or len(imei) != 15:
        raise ValueError

    mower = await client.execute(
        "thing.find",
        {
            "imei": imei
        }
    )
    if mower:
        return await client.get_response()

    # Lawn mower not found
    raise KeyError(
        "Lawn mower not found. Please check the application configuration."
    )


async def get_first_empty_robot_client(
    mower: dict,
    client_key: str | None = None,
) -> str:
    """Get first empty robot_client key or the one that matches client_key."""
    if "attrs" not in mower:
        raise KeyError(
            "No attributes found for lawn mower not found. Abort."
        )
    # Iteration through the "robot_client" attributes
    for counter in range(1, 6):
        # First empty key
        if (robot_client_key := f"robot_client{counter}") not in mower["attrs"]:
            return robot_client_key
        # Key is set and same as given client_key
        elif mower["attrs"][robot_client_key].get("value") == client_key:
            return robot_client_key

    raise IndexError(
        "No available robot_client key found. Abort"
    )


async def publish_robot_client(
    client: ZcsApiClient,
    imei: str,
    robot_client_key: str,
    client_key: str,
) -> None:
    """Publish robot client."""
    await client.execute(
        "attribute.publish",
        {
            "thingKey": imei,
            "key": robot_client_key,
            "value": client_key,
        },
    )


async def delete_robot_client(
    client: ZcsApiClient,
    imei: str,
    robot_client_key: str,
) -> None:
    """Delete robot client."""
    await client.execute(
        "attribute.delete",
        {
            "thingKey": imei,
            "key": robot_client_key,
            "startTs": "1000-01-01T00:00:00Z",
            "endTs": "3000-12-31T23:59:59Z"
        },
    )


async def replace_robot_client(
    client: ZcsApiClient,
    mowers: dict,
    client_key_old: str,
    client_key_new: str,
) -> None:
    """Replace robot_client in all given lawn mowers."""
    await client.execute(
        "thing.list",
        {
            "show": [
                "id",
                "key",
                "attrs",
            ],
            "hideFields": True,
            "keys": list(mowers.keys()),
        },
    )
    response = await client.get_response()
    if "result" in response:
        result_list = response["result"]
        for mower in (
            mower
            for mower in result_list
            if "key" in mower and mower["key"] in mowers
        ):
            robot_client_key = await get_first_empty_robot_client(
                mower=mower,
                client_key=client_key_old,
            )
            await client.execute(
                "attribute.publish",
                {
                    "thingKey": mower.get("key", ""),
                    "key": robot_client_key,
                    "value": client_key_new,
                },
            )
