# Copyright (c) 2024-2025 Anvil
# SPDX-License-Identifier: MIT

from anvil import Component
from anvil.designer import in_designer, register_interaction, start_editing_form
from anvil.history import Location
from anvil.js import get_dom_node

from ._exceptions import InvalidPathParams
from ._logger import logger
from ._matcher import get_match
from ._navigate import nav_args_to_location, navigate_with_location
from ._router import navigation_emitter
from ._utils import ensure_dict

__version__ = "0.3.5"


def _temp_hack_to_get_form(self):
    if not in_designer:
        return None

    from ._import_utils import import_module

    try:
        import_module("routes")
    except Exception:
        pass

    if self._rn.location is None:
        return None
    elif self._rn.location.path is None:
        return None
    match = get_match(location=self._rn.location)

    if match is not None:
        return match.route.form


nav_props = {
    "path": {
        "name": "path",
        "type": "string",
        "group": "navigation",
        "priority": 100,
        "important": True,
    },
    "query": {"name": "query", "type": "object", "group": "navigation"},
    "params": {"name": "params", "type": "object", "group": "navigation"},
    "hash": {"name": "hash", "type": "string", "group": "navigation"},
    "nav_context": {"name": "nav_context", "type": "object", "group": "navigation"},
    "form_properties": {
        "name": "form_properties",
        "type": "object",
        "group": "navigation",
    },
}

active_props = {
    "active": {"name": "active", "type": "boolean", "group": "active"},
    "exact_path": {"name": "exact_path", "type": "boolean", "group": "active"},
    "exact_query": {"name": "exact_query", "type": "boolean", "group": "active"},
    "exact_hash": {"name": "exact_hash", "type": "boolean", "group": "active"},
}

all_props = {**nav_props, **active_props}

ignore_props = ["href", "url", "selected", *all_props]


def prop_filter(prop):
    return prop["name"] not in ignore_props and prop["type"] != "form"


def filter_props(prop_list):
    return filter(prop_filter, prop_list)


class RouteNamespace:
    pass


class LinkMixinCommon(Component):
    def __init__(self, **properties):
        self._rn = RouteNamespace()
        self._rn.props = properties
        self._rn.location = None
        self._rn.form = None
        self._rn.invalid = None
        self.add_event_handler("x-anvil-page-added", self._rn_setup)
        self.add_event_handler("x-anvil-page-removed", self._rn_cleanup)
        self.add_event_handler("click", self._rn_on_click)

    def _rn_do_click(self, e):
        if not in_designer:
            if self._rn.location is not None:
                logger.debug(f"NavLink clicked, navigating to {self._rn.location}")
                navigate_with_location(
                    self._rn.location,
                    nav_context=self.nav_context,
                    form_properties=self.form_properties,
                )
            elif self._rn.invalid is not None:
                raise self._rn.invalid
            else:
                logger.debug("NavLink clicked, but with invalid path, query or hash")
        elif self._rn.form is not None:
            start_editing_form(self, self._rn.form)

    def _rn_on_click(self, **event_args):
        event = event_args.get("event")
        if event is None:
            raise RuntimeError("Link provider did not pass the event")
        if event.ctrlKey or event.metaKey or event.shiftKey:
            logger.debug(
                "NavLink clicked, but with modifier keys - letting browser handle"
            )
            return
        event.preventDefault()
        self._rn_do_click(event)

    def _rn_setup(self, **event_args):
        # we have to do this when we're on the page in case links are relative
        self._rn_set_href()

        if in_designer and self._rn.form is not None:
            register_interaction(
                self, get_dom_node(self), "dblclick", self._rn_do_click
            )

        if not in_designer:
            navigation_emitter.add_event_handler("navigate", self._rn_set_href)

    def _rn_cleanup(self, **event_args):
        navigation_emitter.remove_event_handler("navigate", self._rn_set_href)

    @property
    def nav_context(self):
        return self._rn.props.get("nav_context")

    @nav_context.setter
    def nav_context(self, value):
        value = ensure_dict(value, "nav_context")
        self._rn.props["nav_context"] = value

    @property
    def form_properties(self):
        return self._rn.props.get("form_properties")

    @form_properties.setter
    def form_properties(self, value):
        value = ensure_dict(value, "form_properties")
        self._rn.props["form_properties"] = value

    @property
    def path(self):
        return self._rn.props.get("path")

    @path.setter
    def path(self, value):
        self._rn.props["path"] = value
        self._rn_set_href()

    @property
    def query(self):
        return self._rn.props.get("query")

    @query.setter
    def query(self, value):
        self._rn.props["query"] = value
        self._rn_set_href()

    @property
    def params(self):
        return self._rn.props.get("params")

    @params.setter
    def params(self, value):
        self._rn.props["params"] = value
        self._rn_set_href()

    @property
    def hash(self):
        return self._rn.props.get("hash")

    @hash.setter
    def hash(self, value):
        self._rn.props["hash"] = value
        self._rn_set_href()

    def _rn_set_href(self, **nav_args):
        prev_location = self._rn.location

        path = self.path or None
        params = self.params
        query = self.query
        hash = self.hash

        # fast path
        if (
            path is not None
            and not callable(query)
            and not in_designer
            and prev_location is not None
        ):
            return

        self._rn.location = None
        self._rn.form = None

        try:
            location = nav_args_to_location(
                path=path,
                params=params,
                query=query,
                hash=hash,
            )
        except InvalidPathParams as e:
            if not in_designer:
                self._rn.invalid = e
                self.href = ""
                return
            else:
                location = Location(path=path, hash=hash)
        else:
            self._rn.invalid = None

        self._rn.location = location

        if prev_location == location:
            return

        if in_designer:
            self._rn.form = _temp_hack_to_get_form(self)
        elif location.path is not None:
            self.href = location.get_url(True)
