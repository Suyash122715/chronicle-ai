"""Unit test verifying Alembic migration 005_create_knowledge_graph_tables metadata, upgrade DDL, and downgrade DDL."""

import importlib.util
from pathlib import Path
from alembic.config import Config
from alembic import command


def test_migration_005_metadata_and_chain() -> None:
    """Verifies migration 005 revision ID, down_revision, and migration chain linkage."""
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "005_create_knowledge_graph_tables.py"
    )
    assert migration_path.exists(), "Migration 005 file does not exist"

    spec = importlib.util.spec_from_file_location("migration_005", migration_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.revision == "005_create_knowledge_graph_tables"
    assert mod.down_revision == "004_create_artifact_extractions_table"
    assert hasattr(mod, "upgrade"), "Migration 005 missing upgrade() function"
    assert hasattr(mod, "downgrade"), "Migration 005 missing downgrade() function"


def test_migration_005_offline_upgrade_and_downgrade_sql(capsys) -> None:
    """Verifies Alembic offline migration generation renders table creation and drop DDL cleanly."""
    backend_dir = Path(__file__).resolve().parents[2]
    alembic_ini_path = backend_dir / "alembic.ini"
    alembic_script_path = backend_dir / "alembic"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(alembic_script_path))
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///memory.db")

    # 1. Generate offline upgrade SQL script from 004 to 005
    command.upgrade(
        alembic_cfg,
        "004_create_artifact_extractions_table:005_create_knowledge_graph_tables",
        sql=True,
    )
    captured_upgrade = capsys.readouterr()
    upgrade_output = captured_upgrade.out

    assert "CREATE TABLE graph_entities" in upgrade_output
    assert "CREATE TABLE graph_relationships" in upgrade_output
    assert "CREATE TABLE entity_artifact_provenance" in upgrade_output
    assert "CREATE TABLE relationship_artifact_provenance" in upgrade_output

    assert "canonical_name" in upgrade_output
    assert "relationship_type" in upgrade_output
    assert "evidence" in upgrade_output
    assert "uq_graph_entities_user_type_canonical" in upgrade_output or "UNIQUE" in upgrade_output
    assert "uq_graph_relationships_user_source_target_type" in upgrade_output or "UNIQUE" in upgrade_output

    # 2. Generate offline downgrade SQL script from 005 back to 004
    command.downgrade(
        alembic_cfg,
        "005_create_knowledge_graph_tables:004_create_artifact_extractions_table",
        sql=True,
    )
    captured_downgrade = capsys.readouterr()
    downgrade_output = captured_downgrade.out

    assert "DROP TABLE relationship_artifact_provenance" in downgrade_output
    assert "DROP TABLE entity_artifact_provenance" in downgrade_output
    assert "DROP TABLE graph_relationships" in downgrade_output
    assert "DROP TABLE graph_entities" in downgrade_output
