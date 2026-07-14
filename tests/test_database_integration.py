from sqlalchemy import text

from app.database import upsert_records


def test_clean_records_table_fixture_runs(clean_records_table):
    pass


def test_upsert_records_is_idempotent(clean_records_table):
    rows = [
        {
            "natural_key": "idem-1",
            "occurred_at": None,
            "raw_fields": {},
            "disp_code": "N",
            "disposition": "No action needed",
            "final_radio_code": "N",
            "final_call_type": "TEST",
            "hundred_block_addr": "100 TEST ST",
            "grid": None,
        },
    ]

    upsert_records(rows, session=clean_records_table)
    first_count = clean_records_table.scalar(
        text("SELECT count(*) FROM records")
    )
    assert first_count == len(rows)

    upsert_records(rows, session=clean_records_table)
    second_count = clean_records_table.scalar(
        text("SELECT count(*) FROM records")
    )
    assert second_count == first_count == len(rows)


def test_upsert_records_updates_changed_value_in_place(clean_records_table):
    original = {
        "natural_key": "idem-2",
        "occurred_at": None,
        "raw_fields": {},
        "disp_code": "N",
        "disposition": "PENDING",
        "final_radio_code": "N",
        "final_call_type": "TEST",
        "hundred_block_addr": "200 TEST ST",
        "grid": None,
    }
    changed = {**original, "disposition": "NO ACTION REQUIRED"}

    upsert_records([original], session=clean_records_table)
    upsert_records([changed], session=clean_records_table)

    stored_rows = clean_records_table.execute(
        text(
            "SELECT disposition FROM records "
            "WHERE natural_key = :natural_key"
        ),
        {"natural_key": original["natural_key"]},
    ).all()

    assert len(stored_rows) == 1
    assert stored_rows[0].disposition == "NO ACTION REQUIRED"
