"""Tests for the sensor module."""

from homeassistant.const import HTTP_OK, HTTP_UNAUTHORIZED
from custom_components.uk_trains.const import TRANSPORT_API_URL_BASE
from custom_components.uk_trains import sensor
#from requests import Response
import json

async def test_async_update_success(hass, requests_mock):
    """Tests a fully successful async_update."""

    with open('tests/testdata/success.json') as fd:
        requests_mock.get(TRANSPORT_API_URL_BASE + 'origin/to/dest', text=fd.read(), status_code=HTTP_OK)

    custom_sensor = sensor.RttIoLiveTrainTimeSensor(hass, 'username', 'password', 'origin', 'dest', 10)
    await custom_sensor.async_device_update()
    raw_expected = {
        'location': {
            'name': 'Sevenoaks',
            'crs': 'SEV',
            'tiploc': 'SVNOAKS',
            'country': 'gb',
            'system': 'nr'
        },
        'filter': {
            'destination': {
                'name': 'London Bridge',
                'crs': 'LBG',
                'tiploc': [
                    'LNDNBDC',
                    'LNDNBDE',
                    'LNDNBDG'
                ],
                'country': 'gb',
                'system': 'nr'
            }
        },
        'services': [
            {
                'locationDetail': {
                    'tiploc': 'SVNOAKS',
                    'gbttBookedArrival': '0456',
                    'gbttBookedDeparture': '0457',
                    'origin': [
                        {
                            'tiploc': 'TONBDG',
                            'description': 'Tonbridge',
                            'workingTime': '044500',
                            'publicTime': '0445'
                        }
                    ],
                    'destination': [
                        {
                            'tiploc': 'CHRX',
                            'description': 'London Charing Cross',
                            'workingTime': '054300',
                            'publicTime': '0545'
                        }
                    ],
                    'isCall': True,
                    'isPublicCall': True,
                    'platform': '1',
                    'displayAs': 'CALL'
                },
                'serviceUid': 'G83169',
                'runDate': '2021-10-15',
                'trainIdentity': '1Y02',
                'runningIdentity': '1Y02',
                'atocCode': 'SE',
                'atocName': 'Southeastern',
                'serviceType': 'train',
                'isPassenger': True
            },
            {
                'locationDetail': {
                    'tiploc': 'SVNOAKS',
                    'gbttBookedDeparture': '0532',
                    'origin': [
                        {
                            'tiploc': 'SVNOAKS',
                            'description': 'Sevenoaks',
                            'workingTime': '053200',
                            'publicTime': '0532'
                        }
                    ],
                    'destination': [
                        {
                            'tiploc': 'CHRX',
                            'description': 'London Charing Cross',
                            'workingTime': '062600',
                            'publicTime': '0626'
                        }
                    ],
                    'isCall': True,
                    'isPublicCall': True,
                    'platform': '2',
                    'displayAs': 'ORIGIN'
                },
                'serviceUid': 'G83470',
                'runDate': '2021-10-15',
                'trainIdentity': '2F06',
                'runningIdentity': '2F06',
                'atocCode': 'SE',
                'atocName': 'Southeastern',
                'serviceType': 'train',
                'isPassenger': True
            }
        ]
    }
    expected = {
        'station_code': 'origin',
        'calling_at': 'dest',
        'next_trains': [
            {
                'origin_name': 'Tonbridge',
                'destination_name': 'London Charing Cross',
                'destination_time': '05:45',
                'scheduled': '04:57',
                'estimated': '',
                'platform': '1',
                'operator_name': 'Southeastern'
            },
            {
                'origin_name': 'Sevenoaks',
                'destination_name': 'London Charing Cross',
                'destination_time': '06:26',
                'scheduled': '05:32',
                'estimated': '',
                'platform': '2',
                'operator_name': 'Southeastern'
            }
        ]
    }
    assert raw_expected == custom_sensor._data
    assert expected == custom_sensor.extra_state_attributes
    assert custom_sensor.available is True


async def test_async_update_failed(hass, requests_mock):
    """Tests a failed async_update."""
    
    requests_mock.get(TRANSPORT_API_URL_BASE + 'origin/to/dest', text='', status_code=HTTP_UNAUTHORIZED)
    
    custom_sensor = sensor.RttIoLiveTrainTimeSensor(hass, 'username', 'password', 'origin', 'dest', 10)
    await custom_sensor.async_device_update()

    assert custom_sensor.available is False
    assert 'Credentials invalid' == custom_sensor._state
