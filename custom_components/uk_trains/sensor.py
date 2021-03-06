"""Support for UK public transport data provided by www.realtimetrains.co.uk."""
import logging
from datetime import datetime, timedelta
from homeassistant import config_entries, core

import homeassistant.util.dt as dt_util
import requests
from homeassistant.components.sensor import SensorEntity
from http import HTTPStatus
from homeassistant.const import TIME_MINUTES
from homeassistant.util import Throttle

from .const import (ATTR_CALLING_AT, ATTR_NEXT_TRAINS, ATTR_STATION_CODE,
                    CONF_API_PASSWORD, CONF_API_USERNAME, CONF_DESTINATION,
                    CONF_ORIGIN, CONF_QUERIES, DOMAIN, TRANSPORT_API_URL_BASE)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Get the rtt_io sensor."""
    sensors = []
    number_sensors = len(config.get(CONF_QUERIES))
    interval = timedelta(seconds=87 * number_sensors)

    for query in config.get(CONF_QUERIES):
        station_code = query.get(CONF_ORIGIN)
        calling_at = query.get(CONF_DESTINATION, '')
        sensors.append(
            RttIoLiveTrainTimeSensor(
                hass,
                config.get(CONF_API_USERNAME),
                config.get(CONF_API_PASSWORD),
                station_code,
                calling_at,
                interval,
            )
        )

    add_entities(sensors, True)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if config_entry.options:
        config.update(config_entry.options)
    sensors = []
    number_sensors = len(config.get(CONF_QUERIES))
    interval = timedelta(seconds=87 * number_sensors)
    for query in config.get(CONF_QUERIES):
        station_code = query.get(CONF_ORIGIN)
        calling_at = query.get(CONF_DESTINATION, '')
        sensors.append(
            RttIoLiveTrainTimeSensor(
                hass,
                config.get(CONF_API_USERNAME),
                config.get(CONF_API_PASSWORD),
                station_code,
                calling_at,
                interval,
            )
        )
    async_add_entities(sensors, update_before_add=True)


async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
) -> None:
    """Set up the sensor platform."""
    sensors = []
    number_sensors = len(config.get(CONF_QUERIES))
    interval = timedelta(seconds=87 * number_sensors)
    for query in config.get(CONF_QUERIES):
        station_code = query.get(CONF_ORIGIN)
        calling_at = query.get(CONF_DESTINATION, '')
        sensors.append(
            RttIoLiveTrainTimeSensor(
                hass,
                config.get(CONF_API_USERNAME),
                config.get(CONF_API_PASSWORD),
                station_code,
                calling_at,
                interval,
            )
        )
    async_add_entities(sensors, update_before_add=True)


class RttIoSensor(SensorEntity):
    """
    Sensor that reads the UK transport web API.

    www.realtimetrains.co.uk provides comprehensive transport data for UK train
    travel across the UK via simple JSON API. Subclasses of this
    base class can be used to access specific types of information.
    """

    _attr_icon = "mdi:train"
    _attr_native_unit_of_measurement = TIME_MINUTES

    def __init__(self, hass, name, api_username, api_password, url):
        """Initialize the sensor."""
        self._data = {}
        self._api_username = api_username
        self._api_password = api_password
        self._url = TRANSPORT_API_URL_BASE + url
        self._name = name
        self._state = None
        self._attr_available = False
        self.hass = hass
        self._uid = url

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._uid

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    def _do_api_request(self):
        """Perform an API request."""
        self._data = {}
        response = requests.get(self._url, auth=(self._api_username, self._api_password))
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            self._state = "Credentials invalid"
        elif response.status_code != HTTPStatus.OK:
            _LOGGER.warning(f"Invalid response from API: {response.status_code}: {self._url}")
        elif "error" in response.json():
            self._state = "Unknown error occurred, ensure station codes are valid"
        else:
            self._data = response.json()


class RttIoLiveTrainTimeSensor(RttIoSensor):
    """Live train time sensor from UK www.realtimetrains.co.uk."""

    _attr_icon = "mdi:train"

    def __init__(self, hass, api_username, api_password, station_code, calling_at, interval):
        """Construct a live train time sensor."""
        self._station_code = station_code
        self._calling_at = calling_at
        self._next_trains = []

        if len(calling_at) > 0:
            query_url = f"{station_code}/to/{calling_at}"
            sensor_name = f"Next train to {calling_at} from {station_code}"
        else:
            query_url = f"{station_code}"
            sensor_name = f"Trains from {station_code}"

        RttIoSensor.__init__(
            self, hass, sensor_name, api_username, api_password, query_url
        )
        self.update = Throttle(interval)(self._update)
        hass.async_add_executor_job(self.update)

    def _update(self):
        """Get the latest live departure data for the specified stop."""

        self._do_api_request()
        self._next_trains = []

        if self._data != {}:
            if self._data["services"] is None or len(self._data["services"]) == 0:
                self._state = "No departures"
                self._attr_available = True
            else:
                for departure in self._data["services"]:
                    if departure.get('plannedCancel', False):
                        continue
                    if 'locationDetail' not in departure:
                        continue
                    self._next_trains.append(
                        {
                            "origin_name": departure['locationDetail']['origin'][0]['description'],
                            "destination_name": departure['locationDetail']['destination'][0]['description'],
                            "destination_time": departure['locationDetail']['destination'][0]['publicTime'],
                            "scheduled": departure['locationDetail']['gbttBookedDeparture'],
                            "estimated": departure['locationDetail'].get('realtimeDeparture', ''),
                            "platform": departure['locationDetail'].get('platform', ''),
                            "operator_name": departure["atocName"],
                        }
                    )
                    # times need to be properly formatted
                    for key in ['destination_time', 'scheduled', 'estimated']:
                        if len(self._next_trains[-1][key]) == 4:
                            self._next_trains[-1][key] = self._next_trains[-1][key][:2] + ':' + self._next_trains[-1][key][2:]

                if self._next_trains:
                    self._attr_available = True
                    self._state = min(
                        _delta_mins(train["scheduled"]) for train in self._next_trains
                    )
                else:
                    self._state = "No valid departures"
                    self._attr_available = True

    @property
    def extra_state_attributes(self):
        """Return other details about the sensor state."""
        attrs = {}
        if self._data is not None:
            attrs[ATTR_STATION_CODE] = self._station_code
            attrs[ATTR_CALLING_AT] = self._calling_at
            if self._next_trains:
                attrs[ATTR_NEXT_TRAINS] = self._next_trains
            return attrs


def _delta_mins(hhmm_time_str):
    """Calculate time delta in minutes to a time in hh:mm format."""
    now = dt_util.now()
    hhmm_time = datetime.strptime(hhmm_time_str, "%H:%M")

    hhmm_datetime = now.replace(hour=hhmm_time.hour, minute=hhmm_time.minute)

    if hhmm_datetime < now:
        hhmm_datetime += timedelta(days=1)

    delta_mins = (hhmm_datetime - now).total_seconds() // 60
    return delta_mins
