"""Constants for ZCS Lawn Mower Robot integration."""
from logging import Logger, getLogger

from homeassistant.const import Platform, PERCENTAGE, UnitOfLength

LOGGER = getLogger(__package__)

DOMAIN = "zcsmower"
MANUFACTURER = "Zucchetti Centro Sistemi"

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

ROBOT_STATES = [
    {
        "name" : "unknown",
        "icon" : "mdi:crosshairs-question",
    },
    {
        "name" : "charging",
        "icon" : "mdi:battery-charging",
    },
    {
        "name" : "working",
        "icon" : "mdi:state-machine",
    },
    {
        "name" : "stop",
        "icon" : "mdi:stop-circle",
    },
    {
        "name" : "error",
        "icon" : "mdi:alert-circle",
    },
    {
        "name" : "nosignal",
        "icon" : "mdi:signal-off",
    },
    {
        "name" : "gotostation",
        "icon" : "mdi:ev-station",
    },
    {
        "name" : "gotoarea",
        "icon" : "mdi:grass",
    },
    {
        "name" : "bordercut",
        "icon" : "mdi:scissors-cutting",
    },
]

UNITS = {
    "KILOMETERS": UnitOfLength.KILOMETERS,
    "PERCENT": PERCENTAGE,
    "T24H": "",
    "T12H": "",
}
