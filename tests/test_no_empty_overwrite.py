from src.storage import should_overwrite_successful


def test_zero_results_with_timeout_does_not_overwrite():
    assert not should_overwrite_successful(
        accepted_count=0,
        raw_count=0,
        had_errors=True,
        capacity_reached=False,
        all_priority_completed=False,
    )


def test_zero_results_after_clean_complete_refresh_can_overwrite():
    assert should_overwrite_successful(
        accepted_count=0,
        raw_count=0,
        had_errors=False,
        capacity_reached=False,
        all_priority_completed=True,
    )

