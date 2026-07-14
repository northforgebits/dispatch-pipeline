from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from app.config import settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def clean_records_table():
    """Yield sessions connected to an isolated, migrated PostgreSQL schema."""
    schema_name = f"pytest_{uuid4().hex}"
    admin_engine = create_engine(settings.database_url, pool_pre_ping=True)
    test_engine = None

    with admin_engine.begin() as connection:
        connection.execute(CreateSchema(schema_name))

    try:
        test_url = make_url(settings.database_url).update_query_dict(
            {"options": f"-csearch_path={schema_name}"}
        )
        alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
        alembic_config.set_main_option(
            "sqlalchemy.url",
            test_url.render_as_string(hide_password=False).replace("%", "%%"),
        )
        command.upgrade(alembic_config, "head")

        test_engine = create_engine(test_url, pool_pre_ping=True)
        with sessionmaker(bind=test_engine)() as session:
            yield session
    finally:
        if test_engine is not None:
            test_engine.dispose()

        try:
            with admin_engine.begin() as connection:
                connection.execute(DropSchema(schema_name, cascade=True))
        finally:
            admin_engine.dispose()
