from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum


class WorkStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ScheduledWork:
    work_id: str
    scheduled_for: datetime
    idempotency_key: str
    status: WorkStatus = WorkStatus.PENDING


@dataclass(frozen=True)
class QueueRequest:
    work_id: str
    idempotency_key: str


@dataclass(frozen=True)
class DeliveryResult:
    work_id: str
    delivered: bool
    detail: str


def build_queue_request(work: ScheduledWork) -> QueueRequest:
    """
    Build a generic queue contract for eligible scheduled work.

    The production scheduler, persistence queries, queue technology,
    locking behavior, retry configuration, and notification workflow
    intentionally remain private.
    """
    if work.status is not WorkStatus.PENDING:
        raise ValueError("only pending work can be queued")

    if not work.idempotency_key.strip():
        raise ValueError("idempotency key is required")

    return QueueRequest(
        work_id=work.work_id,
        idempotency_key=work.idempotency_key,
    )


def mark_queued(work: ScheduledWork) -> ScheduledWork:
    if work.status is not WorkStatus.PENDING:
        raise ValueError("only pending work can transition to queued")

    return replace(
        work,
        status=WorkStatus.QUEUED,
    )


def record_delivery(
    work: ScheduledWork,
    delivered: bool,
    detail: str,
) -> ScheduledWork:
    """
    Demonstrate the final state contract only.

    Delivery adapters, callback handling, retry policy, notification
    providers, and terminal-failure behavior remain private.
    """
    if work.status is not WorkStatus.QUEUED:
        raise ValueError("delivery can only be recorded for queued work")

    if not detail.strip():
        raise ValueError("delivery detail is required")

    target = (
        WorkStatus.COMPLETED
        if delivered
        else WorkStatus.FAILED
    )

    return replace(
        work,
        status=target,
    )


def delivery_result(
    work: ScheduledWork,
    delivered: bool,
    detail: str,
) -> DeliveryResult:
    if not detail.strip():
        raise ValueError("delivery detail is required")

    return DeliveryResult(
        work_id=work.work_id,
        delivered=delivered,
        detail=detail.strip(),
    )
