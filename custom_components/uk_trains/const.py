import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA

DOMAIN = "uk_trains"
TRANSPORT_API_URL_BASE = "https://api.rtt.io/api/v1/json/search/"

ATTR_ATCOCODE = "atcocode"
ATTR_LOCALITY = "locality"
ATTR_STOP_NAME = "stop_name"
ATTR_REQUEST_TIME = "request_time"
ATTR_STATION_CODE = "station_code"
ATTR_CALLING_AT = "calling_at"
ATTR_NEXT_TRAINS = "next_trains"

CONF_API_PASSWORD = "password"
CONF_API_USERNAME = "username"
CONF_QUERIES = "queries"
CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"

_QUERY_SCHEME = vol.Schema(
    {
        vol.Required(CONF_ORIGIN): cv.string,
        vol.Optional(CONF_DESTINATION): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_USERNAME): cv.string,
        vol.Required(CONF_API_PASSWORD): cv.string,
        vol.Required(CONF_QUERIES): [_QUERY_SCHEME],
    }
)
