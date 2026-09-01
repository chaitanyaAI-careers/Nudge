from datetime import datetime, timezone

import pytest

from showcase.workflow_contracts import (
    ScheduledWork,
    WorkStatus,
    build_queue_request,
    delivery_result,
    mark_queued,
    record_delivery,
)


def make_work(
    status: WorkStatus = WorkStatus.PENDING,
) -> ScheduledWork:
    return ScheduledWork(
        work_id="synthetic-work-001",
        scheduled_for=datetime(
            2030,
            1,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        idempotency_key="synthetic-idempotency-key",
        status=status,
    )


def test_pending_work_builds_queue_request():
    work = make_work()

    result = build_queue_request(work)

    assert result.work_id == "synthetic-work-001"
    assert result.idempotency_key == "synthetic-idempotency-key"


def test_queue_request_requires_idempotency_key():
    work = ScheduledWork(
        work_id="synthetic-work-002",
        scheduled_for=datetime(
            2030,
            1,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        idempotency_key="",
    )

    with pytest.raises(ValueError):
        build_queue_request(work)


def test_only_pending_work_can_be_queued():
    work = make_work(
        status=WorkStatus.COMPLETED,
    )

    with pytest.raises(ValueError):
        build_queue_request(work)


def test_mark_queued_changes_state():
    result = mark_queued(make_work())

    assert result.status is WorkStatus.QUEUED


def test_successful_delivery_completes_work():
    queued = make_work(
        status=WorkStatus.QUEUED,
    )

    result = record_delivery(
        queued,
        delivered=True,
        detail="Synthetic delivery succeeded.",
    )

    assert result.status is WorkStatus.COMPLETED


def test_failed_delivery_marks_work_failed():
    queued = make_work(
        status=WorkStatus.QUEUED,
    )

    result = record_delivery(
        queued,
        delivered=False,
        detail="Synthetic delivery failed.",
    )

    assert result.status is WorkStatus.FAILED


def test_delivery_requires_queued_state():
    with pytest.raises(ValueError):
        record_delivery(
            make_work(),
            delivered=True,
            detail="Synthetic delivery succeeded.",
        )


def test_delivery_result_is_structured():
    result = delivery_result(
        make_work(),
        delivered=True,
        detail=" Synthetic delivery succeeded. ",
    )

    assert result.work_id == "synthetic-work-001"
    assert result.delivered is True
    assert result.detail == "Synthetic delivery succeeded."
