"""Tests for the config flow."""
import logging
from unittest import mock

from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_PATH
from http import HTTPStatus
import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant import data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.uk_trains import config_flow
from custom_components.uk_trains.const import CONF_API_PASSWORD, CONF_API_USERNAME, CONF_ORIGIN, CONF_QUERIES, DOMAIN, TRANSPORT_API_URL_BASE

async def test_validate_auth_valid(hass, requests_mock):
    """Test no exception is raised for valid auth."""
    requests_mock.get(TRANSPORT_API_URL_BASE + 'EUS', text='', status_code=HTTPStatus.OK)
    
    config_flow.validate_auth("token", "password", hass)


async def test_validate_auth_invalid(hass, requests_mock):
    """Test no exception is raised for valid auth."""
    requests_mock.get(TRANSPORT_API_URL_BASE + 'EUS', text='', status_code=HTTPStatus.FORBIDDEN)
    with pytest.raises(ValueError):
        config_flow.validate_auth("token", "password", hass)

async def test_validate_stations_valid(hass, requests_mock):
    """Test no exception is raised for valid auth."""
    requests_mock.get(TRANSPORT_API_URL_BASE + 'EUS', text='', status_code=HTTPStatus.OK)
    requests_mock.get(TRANSPORT_API_URL_BASE + 'EUS/to/HML', text='', status_code=HTTPStatus.OK)
    
    config_flow.validate_stations("token", "password", 'EUS', None, hass)
    config_flow.validate_stations("token", "password", 'EUS', 'HML', hass)


async def test_validate_stations_invalid(hass, requests_mock):
    """Test no exception is raised for valid auth."""
    requests_mock.get(TRANSPORT_API_URL_BASE + 'EUS', text='', status_code=HTTPStatus.FORBIDDEN)
    requests_mock.get(TRANSPORT_API_URL_BASE + 'EUS/to/HML', text='', status_code=HTTPStatus.FORBIDDEN)
    with pytest.raises(ValueError):
        config_flow.validate_stations("token", "password", 'EUS', None, hass)
    with pytest.raises(ValueError):
        config_flow.validate_stations("token", "password", 'EUS', 'HML', hass)


# async def test_flow_user_init(hass):
#     """Test the initialization of the form in the first step of the config flow."""
#     result = await hass.config_entries.flow.async_init(
#         config_flow.DOMAIN, context={"source": "user"}
#     )
#     print(result)
#     expected = {
#         "data_schema": config_flow.AUTH_SCHEMA,
#         "description_placeholders": None,
#         "errors": {},
#         "flow_id": mock.ANY,
#         "handler": "github_custom",
#         "step_id": "user",
#         "type": "form",
#     }
#     assert expected == result

# async def test_show_form(hass):
#     """Test that the form is served with no input."""
#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": SOURCE_USER}
#     )

#     assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
#     assert result["step_id"] == SOURCE_USER

# @patch("custom_components.github_custom.config_flow.validate_auth")
# async def test_flow_user_init_invalid_auth_token(m_validate_auth, hass):
#     """Test errors populated when auth token is invalid."""
#     m_validate_auth.side_effect = ValueError
#     _result = await hass.config_entries.flow.async_init(
#         config_flow.DOMAIN, context={"source": "user"}
#     )
#     result = await hass.config_entries.flow.async_configure(
#         _result["flow_id"], user_input={CONF_ACCESS_TOKEN: "bad"}
#     )
#     assert {"base": "auth"} == result["errors"]


# @patch("custom_components.github_custom.config_flow.validate_auth")
# async def test_flow_user_init_data_valid(hass):
#     """Test we advance to the next step when data is valid."""
#     _result = await hass.config_entries.flow.async_init(
#         config_flow.DOMAIN, context={"source": "user"}
#     )
#     result = await hass.config_entries.flow.async_configure(
#         _result["flow_id"], user_input={
#             CONF_API_USERNAME: "usernames",
#             CONF_API_PASSWORD: "password"
#         }
#     )
#     assert "repo" == result["step_id"]
#     assert "form" == result["type"]


# async def test_flow_repo_init_form(hass):
#     """Test the initialization of the form in the second step of the config flow."""
#     result = await hass.config_entries.flow.async_init(
#         config_flow.DOMAIN, context={"source": "repo"}
#     )
#     expected = {
#         "data_schema": config_flow.REPO_SCHEMA,
#         "description_placeholders": None,
#         "errors": {},
#         "flow_id": mock.ANY,
#         "handler": "github_custom",
#         "step_id": "repo",
#         "type": "form",
#     }
#     assert expected == result


# async def test_flow_repo_path_invalid(hass):
#     """Test errors populated when path is invalid."""
#     config_flow.GithubCustomConfigFlow.data = {
#         CONF_ACCESS_TOKEN: "token",
#     }
#     _result = await hass.config_entries.flow.async_init(
#         config_flow.DOMAIN, context={"source": "repo"}
#     )
#     result = await hass.config_entries.flow.async_configure(
#         _result["flow_id"], user_input={CONF_NAME: "bad", CONF_PATH: "bad"}
#     )
#     assert {"base": "invalid_path"} == result["errors"]


# async def test_flow_repo_add_another(hass):
#     """Test we show the repo flow again if the add_another box was checked."""
#     config_flow.GithubCustomConfigFlow.data = {
#         CONF_ACCESS_TOKEN: "token",
#         CONF_REPOS: [],
#     }
#     _result = await hass.config_entries.flow.async_init(
#         config_flow.DOMAIN, context={"source": "repo"}
#     )
#     result = await hass.config_entries.flow.async_configure(
#         _result["flow_id"],
#         user_input={CONF_PATH: "home-assistant/core", "add_another": True},
#     )
#     assert "repo" == result["step_id"]
#     assert "form" == result["type"]


# @patch("custom_components.github_custom.config_flow.GitHubAPI")
# async def test_flow_repo_creates_config_entry(m_github, hass):
#     """Test the config entry is successfully created."""
#     m_instance = AsyncMock()
#     m_instance.getitem = AsyncMock()
#     m_github.return_value = m_instance
#     config_flow.GithubCustomConfigFlow.data = {
#         CONF_ACCESS_TOKEN: "token",
#         CONF_REPOS: [],
#     }
#     _result = await hass.config_entries.flow.async_init(
#         config_flow.DOMAIN, context={"source": "repo"}
#     )
#     result = await hass.config_entries.flow.async_configure(
#         _result["flow_id"],
#         user_input={CONF_PATH: "home-assistant/core"},
#     )
#     expected = {
#         "version": 1,
#         "type": "create_entry",
#         "flow_id": mock.ANY,
#         "handler": "github_custom",
#         "title": "GitHub Custom",
#         "data": {
#             "access_token": "token",
#             "repositories": [
#                 {"path": "home-assistant/core", "name": "home-assistant/core"}
#             ],
#         },
#         "description": None,
#         "description_placeholders": None,
#         "result": mock.ANY,
#     }
#     assert expected == result


async def test_options_flow_init(hass):
    """Test config flow options."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="next_train_from_LBG",
        data={
            CONF_API_USERNAME: "usernames",
            CONF_API_PASSWORD: "password",
            CONF_QUERIES: [{CONF_ORIGIN: "LBG"}],
        },
    )
    
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # show initial form
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert "form" == result["type"]
    assert "init" == result["step_id"]
    assert {} == result["errors"]
    # Verify multi-select options populated with configured repos.
    assert {"sensor.ha_core": "HA Core"} == result["data_schema"].schema[
        "repos"
    ].options


# @patch("custom_components.github_custom.sensor.GitHubAPI")
# async def test_options_flow_remove_repo(m_github, hass):
#     """Test config flow options."""
#     m_instance = AsyncMock()
#     m_instance.getitem = AsyncMock()
#     m_github.return_value = m_instance

#     config_entry = MockConfigEntry(
#         domain=DOMAIN,
#         unique_id="kodi_recently_added_media",
#         data={
#             CONF_ACCESS_TOKEN: "access-token",
#             CONF_REPOS: [{"path": "home-assistant/core", "name": "HA Core"}],
#         },
#     )
#     config_entry.add_to_hass(hass)
#     assert await hass.config_entries.async_setup(config_entry.entry_id)
#     await hass.async_block_till_done()

#     # show initial form
#     result = await hass.config_entries.options.async_init(config_entry.entry_id)
#     # submit form with options
#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"], user_input={"repos": []}
#     )
#     assert "create_entry" == result["type"]
#     assert "" == result["title"]
#     assert result["result"] is True
#     assert {CONF_REPOS: []} == result["data"]


# @patch("custom_components.github_custom.sensor.GitHubAPI")
# @patch("custom_components.github_custom.config_flow.GitHubAPI")
# async def test_options_flow_add_repo(m_github, m_github_cf, hass):
#     """Test config flow options."""
#     m_instance = AsyncMock()
#     m_instance.getitem = AsyncMock()
#     m_github.return_value = m_instance
#     m_github_cf.return_value = m_instance

#     config_entry = MockConfigEntry(
#         domain=DOMAIN,
#         unique_id="kodi_recently_added_media",
#         data={
#             CONF_ACCESS_TOKEN: "access-token",
#             CONF_REPOS: [{"path": "home-assistant/core", "name": "HA Core"}],
#         },
#     )
#     config_entry.add_to_hass(hass)
#     assert await hass.config_entries.async_setup(config_entry.entry_id)
#     await hass.async_block_till_done()

#     # show initial form
#     result = await hass.config_entries.options.async_init(config_entry.entry_id)
#     # submit form with options
#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input={"repos": ["sensor.ha_core"], "path": "boralyl/steam-wishlist"},
#     )
#     assert "create_entry" == result["type"]
#     assert "" == result["title"]
#     assert result["result"] is True
#     expected_repos = [
#         {"path": "home-assistant/core", "name": "HA Core"},
#         {"path": "boralyl/steam-wishlist", "name": "boralyl/steam-wishlist"},
#     ]
#     assert {CONF_REPOS: expected_repos} == result["data"]
