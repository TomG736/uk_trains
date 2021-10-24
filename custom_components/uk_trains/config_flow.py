from copy import deepcopy
from typing import Any, Dict, Optional
from homeassistant.data_entry_flow import FlowResult

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import HTTP_OK
from homeassistant.core import callback
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry, async_get_registry)

from .const import (_QUERY_SCHEME, CONF_API_PASSWORD, CONF_API_USERNAME,
                    CONF_DESTINATION, CONF_ORIGIN, CONF_QUERIES, DOMAIN,
                    TRANSPORT_API_URL_BASE)

AUTH_SCHEMA = {
    vol.Required(CONF_API_USERNAME): cv.string,
    vol.Required(CONF_API_PASSWORD): cv.string,
}


async def validate_auth(username, password, hass=None):
    response = requests.get(TRANSPORT_API_URL_BASE + 'EUS', auth=(username, password))
    if response.status_code != HTTP_OK:
        raise ValueError('Auth Failed')


async def validate_stations(username, password, orig, dest, hass=None):
    response = requests.get(TRANSPORT_API_URL_BASE + orig + (f"/to/{dest}" if dest else ''), auth=(username, password))
    if response.status_code != HTTP_OK:
        raise ValueError('Failed')


class RTTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(user_input[CONF_API_USERNAME], user_input[CONF_API_PASSWORD])
            except ValueError:
                errors["base"] = "auth"
            if not errors:
                # Input is valid, set data.
                self.data = user_input
                self.data[CONF_QUERIES] = []
                # Return the form of the next step.
                return await self.async_step_journey()

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )

    async def async_step_journey(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Second step in config flow to add a journey."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # Validate the path.
            try:
                await validate_stations(self.data[CONF_API_USERNAME], self.data[CONF_API_PASSWORD], user_input[CONF_ORIGIN], user_input.get(CONF_DESTINATION, None))
            except ValueError:
                errors["base"] = "invalid_stations"

            if not errors:
                # Input is valid, set data.
                self.data[CONF_QUERIES].append(
                    {
                        CONF_ORIGIN: user_input[CONF_ORIGIN],
                        CONF_DESTINATION: user_input.get(CONF_DESTINATION, ''),
                    }
                )
                # If user ticked the box show this form again so they can add an
                # additional journey.
                if user_input.get("add_another", False):
                    return await self.async_step_journey()

                # User is done adding journey, create the config entry.
                return self.async_create_entry(title="RTT Train Info", data=self.data)

        return self.async_show_form(
            step_id="journey", data_schema=_QUERY_SCHEME.append({
                vol.Optional("add_another"): cv.boolean
            }), errors=errors
        )


@staticmethod
@callback
def async_get_options_flow(config_entry):
    """Get the options flow for this handler."""
    return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}
        # Grab all configured journeys from the entity registry so we can populate the
        # multi-select dropdown that will allow a user to remove a journey.
        entity_registry = await async_get_registry(self.hass)
        entries = async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )
        # Default value for our multi-select.
        all_journeys = {e.entity_id: e.original_name for e in entries}
        repo_map = {e.entity_id: e for e in entries}

        if user_input is not None:
            updated_journeys = deepcopy(self.config_entry.data[CONF_QUERIES])

            # Remove any unchecked journeys.
            removed_entities = [
                entity_id
                for entity_id in repo_map.keys()
                if entity_id not in user_input["journeys"]
            ]
            for entity_id in removed_entities:
                # Unregister from HA
                entity_registry.async_remove(entity_id)
                # Remove from our configured journeys.
                entry = repo_map[entity_id]
                entry_path = entry.unique_id
                updated_journeys = [e for e in updated_journeys if e["path"] != entry_path]

            if user_input.get(CONF_ORIGIN):
                # Validate the path.
                username = self.hass.data[DOMAIN][self.config_entry.entry_id][
                    CONF_API_USERNAME
                ]
                password = self.hass.data[DOMAIN][self.config_entry.entry_id][
                    CONF_API_PASSWORD
                ]
                try:
                    await validate_stations(username, password, user_input[CONF_ORIGIN], user_input.get(CONF_DESTINATION, ''))
                except ValueError:
                    errors["base"] = "invalid_path"

                if not errors:
                    # Add the new journey.
                    updated_journeys.append(
                        {
                            CONF_ORIGIN: user_input[CONF_ORIGIN],
                            CONF_DESTINATION: user_input.get(CONF_DESTINATION, ''),
                        }
                    )

            if not errors:
                # Value of data will be set on the options property of our config_entry
                # instance.
                return self.async_create_entry(
                    title="",
                    data={CONF_QUERIES: updated_journeys},
                )

        options_schema = vol.Schema(
            {
                vol.Optional("journeys", default=list(all_journeys.keys())): cv.multi_select(
                    all_journeys
                ),
                vol.Optional(CONF_ORIGIN): cv.string,
                vol.Optional(CONF_DESTINATION): cv.string,
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
