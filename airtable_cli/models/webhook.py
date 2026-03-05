from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class Webhook(BaseModel):
    id: str
    type: str
    isHookEnabled: bool
    notificationUrl: Optional[str] = None
    cursorForNextPayload: Optional[int] = None
    areNotificationsEnabled: bool = True
    expirationTime: Optional[str] = None
    specification: Optional[dict[str, Any]] = None


class WebhookList(BaseModel):
    webhooks: list[Webhook]


class WebhookPayload(BaseModel):
    timestamp: str
    baseTransactionNumber: int
    actionMetadata: Optional[dict[str, Any]] = None
    changedTablesById: Optional[dict[str, Any]] = None
    createdTablesById: Optional[dict[str, Any]] = None
    destroyedTableIds: Optional[list[str]] = None


class WebhookPayloadList(BaseModel):
    payloads: list[WebhookPayload]
    cursor: Optional[int] = None
    mightHaveMore: bool = False
