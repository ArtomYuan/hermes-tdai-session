"""Hermes TDAI session middleware.

TDAI MemoryProxy can resolve a per-request session id from the request body.
Hermes' custom provider configuration (``extra_headers`` / ``extra_body``) is
static, so it cannot carry the current session id on its own. This plugin
registers an ``llm_request`` middleware that injects it.

Environment variables
---------------------
TDAI_PROXY_MARK
    Substring of the proxy ``base_url`` to match. Default: ``:8096/hermes/``
TDAI_SESSION_FIELD
    Field name under ``metadata``. Default: ``session_id``

Copyright (C) 2026 ArtomYuan
SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

MIDDLEWARE_KIND = "llm_request"
DEFAULT_PROXY_MARK = ":8096/hermes/"
DEFAULT_SESSION_FIELD = "session_id"


def _proxy_mark() -> str:
    """Return the base_url substring that identifies the TDAI proxy."""
    return os.environ.get("TDAI_PROXY_MARK", DEFAULT_PROXY_MARK)


def _session_field() -> str:
    """Return the body field name to inject under ``metadata``."""
    return os.environ.get("TDAI_SESSION_FIELD", DEFAULT_SESSION_FIELD)


def inject_session_id(*, session_id: str = "", base_url: str = "", request=None, **kwargs):
    """Add ``metadata.<field>`` to the outgoing provider request.

    Returns ``{"request": payload}`` so Hermes replaces the provider kwargs, or
    ``None`` to leave the request untouched.
    """
    if not session_id or not isinstance(request, dict):
        return None
    if _proxy_mark() not in str(base_url or ""):
        return None

    field = _session_field()
    body = dict(request)
    meta = body.get("metadata")
    meta = dict(meta) if isinstance(meta, dict) else {}
    if meta.get(field) == session_id:
        return None
    meta[field] = session_id
    body["metadata"] = meta

    logger.info("[hermes-tdai-session] injected metadata.%s=%s", field, session_id)
    return {
        "request": body,
        "source": "hermes-tdai-session",
        "reason": "per-session isolation for TDAI MemoryProxy",
    }


def register(ctx) -> None:
    """Register the middleware with the Hermes plugin context."""
    ctx.register_middleware(MIDDLEWARE_KIND, inject_session_id)
    logger.info(
        "[hermes-tdai-session] llm_request middleware registered (mark=%r, field=%r)",
        _proxy_mark(),
        _session_field(),
    )
