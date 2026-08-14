"""Unit test verifying Alembic migration 004_create_artifact_extractions_table metadata, upgrade DDL, and downgrade DDL."""

import importlib.util
from pathlib import Path
from alembic.config import Config
from alembic import command


def test_migration_004_metadata_and_chain() -> None:
    """Verifies migration 004 revision ID, down_revision, and migration chain linkage."""
    migration_path = Path(__file__).resolve().parents[2] / "alembic" / "versions" / "004_create_artifact_extractions_table.py"
    assert migration_path.exists(), "Migration 004 file does not exist"

    spec = importlib.util.spec_from_file_location("migration_004", migration_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.revision == "004_create_artifact_extractions_table"
    assert mod.down_revision == "003_add_processing_status_to_artifacts"
    assert hasattr(mod, "upgrade"), "Migration 004 missing upgrade() function"
    assert hasattr(mod, "downgrade"), "Migration 004 missing downgrade() function"


def test_migration_004_offline_upgrade_and_downgrade_sql(capsys) -> None:
    """Verifies Alembic offline migration generation renders table creation and drop DDL cleanly."""
    backend_dir = Path(__file__).resolve().parents[2]
    alembic_ini_path = backend_dir / "alembic.ini"
    alembic_script_path = backend_dir / "alembic"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(alembic_script_path))
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///memory.db")

    # 1. Generate offline upgrade SQL script from 003 to 004
    command.upgrade(alembic_cfg, "003_add_processing_status_to_artifacts:004_create_artifact_extractions_table", sql=True)
    captured_upgrade = capsys.readouterr()
    upgrade_output = captured_upgrade.out

    assert "CREATE TABLE artifact_extractions" in upgrade_output
    assert "artifact_id" in upgrade_output
    assert "structured_data" in upgrade_output
    assert "provenance" in upgrade_output
    assert "warnings" in upgrade_output
    assert "confidence" in upgrade_output
    assert "status" in upgrade_output
    assert "extractor_version" in upgrade_output
    assert "prompt_version" in upgrade_output
    assert "llm_metadata" in upgrade_output
    assert "started_at" in upgrade_output
    assert "completed_at" in upgrade_output
    assert "REFERENCES artifacts" in upgrade_output or "FOREIGN KEY" in upgrade_output

    # 2. Generate offline downgrade SQL script from 004 back to 003
    command.downgrade(alembic_cfg, "004_create_artifact_extractions_table:003_add_processing_status_to_artifacts", sql=True)
    captured_downgrade = capsys.readouterr()
    downgrade_output = captured_downgrade.out

    assert "DROP TABLE artifact_extractions" in downgrade_output
