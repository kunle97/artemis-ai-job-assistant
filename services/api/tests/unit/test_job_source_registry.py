"""Unit tests for job source registry constants."""

from src.domain.jobs.constants import JOB_SOURCE_REGISTRY


def test_job_source_registry_has_minimum_40_entries():
    total_entries = sum(len(source_map) for source_map in JOB_SOURCE_REGISTRY.values())
    assert total_entries >= 40


def test_job_source_registry_entries_have_required_keys():
    required_keys = {"board_token", "display_name", "careers_url"}

    for source, source_map in JOB_SOURCE_REGISTRY.items():
        for company_slug, company_config in source_map.items():
            missing_keys = required_keys - set(company_config.keys())
            assert not missing_keys, (
                f"Missing keys for {source}/{company_slug}: {sorted(missing_keys)}"
            )