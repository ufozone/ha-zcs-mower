"""Constants for ZCS Lawn Mower Robot integration."""
from logging import Logger, getLogger
from enum import Enum

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import Platform, PERCENTAGE, UnitOfLength

LOGGER = getLogger(__package__)

DOMAIN = "zcsmower"

PLATFORMS = [
    #Platform.BINARY_SENSOR,
    #Platform.DEVICE_TRACKER,
    Platform.SENSOR,
    #Platform.SWITCH,
]

API_BASE_URI = "https://api-de.devicewise.com/api"
API_APP_TOKEN = "DJMYYngGNEit40vA"

CONF_CLIENT_KEY = "client_key"
CONF_IMEI = "imei"
CONF_MOWERS = "lawn_mowers"

ATTR_IMEI = "imei"

ROBOT_STATES = {
    1: "charging",
    2: "working",
    3: "stop",
    4: "error",
    5: "nosignal",
    6: "gotostation",
    7: "gotoarea",
    8: "bordercut"
}

UNITS = {
    "KILOMETERS": UnitOfLength.KILOMETERS,
    "PERCENT": PERCENTAGE,
    "T24H": "",
    "T12H": "",
}
