# Copyright (c) 2024 Anvil
# SPDX-License-Identifier: MIT

# setup default navlink
import anvil
from anvil.designer import get_design_component
from anvil.js import get_dom_node

__version__ = "0.3.2"

BaseAnvilLink = get_design_component(anvil.Link)


class BaseAnchor(BaseAnvilLink):
    def __init__(self, **properties):
        super().__init__(**properties)
        self._d = get_dom_node(self)
        self._d.addEventListener("click", self._handle_click, True)

    def _handle_click(self, e):
        e.stopImmediatePropagation()
        self.raise_event("click", event=e)


class BaseNavLink(BaseAnchor):
    def __init__(self, active=False, role=None, **properties):
        super().__init__(**properties)
        self.active = active

    @property
    def active(self):
        return self.role == "selected"

    @active.setter
    def active(self, value):
        self.role = "selected" if value else None


try:
    from m3.components import Link as BaseAnchor
    from m3.components import NavigationLink as BaseNavLink
except ImportError:
    pass


try:
    from Mantine.Anchor import Anchor as BaseAnchor
    from Mantine.NavLink import NavLink as BaseNavLink

except ImportError:
    pass


anvil.pluggable_ui.provide_defaults(
    "routing", {"routing.NavLink": BaseNavLink, "routing.Anchor": BaseAnchor}
)


def wrap_modal(modal):
    def modal_wrapper(content, **kws):
        from .router import NavigationBlocker
        from .router._alert import DismissibleAlert

        if isinstance(content, str):
            content = anvil.Label(text=content)

        dismissible = kws.get("dismissible", False)

        if dismissible:
            with DismissibleAlert(content):
                return modal(content=content, **kws)
        else:
            with NavigationBlocker():
                return modal(content=content, **kws)

    return modal_wrapper


modal = anvil.pluggable_ui["anvil.modal"]

anvil.pluggable_ui.provide("routing", {"anvil.modal": wrap_modal(modal)})


def on_modal_changed(updates, **event_args):
    new_modal = updates.get("anvil.modal")
    if new_modal is None:
        return

    if event_args.get("provider") == "routing":
        return

    # need to be careful we don't cause an infinite loop
    # this might happen if someone else is listening for anvil.modal changes
    anvil.pluggable_ui.provide("routing", {"anvil.modal": wrap_modal(new_modal)})


anvil.pluggable_ui.add_listener("anvil.modal", on_modal_changed)
