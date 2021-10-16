"""Test component setup."""
from homeassistant.setup import async_setup_component

from custom_components.uk_trains.const import DOMAIN, CONF_API_USERNAME, CONF_API_PASSWORD

TRAIN_STATION_CODE = "WIM"
TRAIN_DESTINATION_NAME = "WAT"
VALID_CONFIG = {
    "sensor": {
        "platform": DOMAIN,
        CONF_API_USERNAME: "foo",
        CONF_API_PASSWORD: "ebcd1234",
        "queries": [
            {
                "origin": TRAIN_STATION_CODE,
                "destination": TRAIN_DESTINATION_NAME,
            },
        ],
    }
}

async def test_async_setup(hass):
    """Test the component gets setup."""
    assert await async_setup_component(hass, "sensor", VALID_CONFIG) is True
