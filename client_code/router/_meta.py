# Copyright (c) 2024-2025 Anvil
# SPDX-License-Identifier: MIT

import anvil

from ._utils import document

__version__ = "0.3.3"


def get_or_create_tag(type):
    tag = document.querySelector(type)
    if tag is None:
        tag = document.createElement(type)
        tag.textContent = ""
        document.head.appendChild(tag)
    return tag


def get_or_create_meta_tag(name):
    tag = document.querySelector(f'meta[name="{name}"]')
    if tag is None:
        tag = document.createElement("meta")
        tag.setAttribute("name", name)
        tag.setAttribute("content", "")
        document.head.appendChild(tag)
    return tag


if anvil.is_server_side():
    title_tag = meta_title = meta_title_og = meta_description = meta_description_og = (
        meta_image_og
    ) = None
    default_title = ""
    default_description = ""
    default_image = ""
    default_title_og = ""
    default_description_og = ""
    default_image_og = ""

else:
    title_tag = get_or_create_tag("title")
    meta_title = get_or_create_meta_tag("title")
    meta_title_og = get_or_create_meta_tag("og:title")
    meta_description = get_or_create_meta_tag("description")
    meta_description_og = get_or_create_meta_tag("og:description")
    meta_image_og = get_or_create_meta_tag("og:image")

    default_title = title_tag.textContent or meta_title.content
    default_description = meta_description.content
    default_image = meta_image_og.content
    default_title_og = meta_title_og.content
    default_description_og = meta_description_og.content
    default_image_og = meta_image_og.content


def get_default_meta():
    rv = {}
    if default_title:
        rv["title"] = default_title
    if default_description:
        rv["description"] = default_description
    return rv


def asset_or_image_to_url(asset_or_image):
    from anvil.js.window import URL

    if not isinstance(asset_or_image, str):
        return asset_or_image

    if asset_or_image.startswith("asset:"):
        asset_or_image = asset_or_image[6:] + "_/theme/"

    if asset_or_image.startswith("/_/theme/"):
        asset_or_image = asset_or_image[1:]
    if asset_or_image.startswith("_/theme/"):
        return URL(anvil.server.get_app_origin() + "/" + asset_or_image).href

    return asset_or_image


def update_meta_tags(meta):
    title = meta.get("title") or default_title
    description = meta.get("description") or default_description
    og_title = meta.get("og:title") or default_title_og
    og_description = meta.get("og:description") or default_description_og
    og_image = meta.get("og:image") or default_image_og

    title_tag.textContent = title
    meta_title.content = title
    meta_title_og.content = og_title
    document.title = title

    meta_description.content = description
    meta_description_og.content = og_description
    meta_image_og.content = asset_or_image_to_url(og_image)
