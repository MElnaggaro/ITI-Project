"""Static security checks for the environment/repository foundation."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_compose_has_exactly_required_services_and_no_source_database() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    assert set(services) == {
        "api",
        "worker",
        "postgres",
        "redis",
        "qdrant",
        "minio",
        "prometheus",
        "grafana",
    }
    assert "pgvector/pgvector" in services["postgres"]["image"]
    assert "source" not in " ".join(services).lower()


def test_compose_healthchecks_and_local_port_bindings_are_present() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))

    for service in compose["services"].values():
        assert "healthcheck" in service

    for service_name in ("api", "minio", "prometheus", "grafana"):
        for binding in compose["services"][service_name]["ports"]:
            assert binding.startswith("127.0.0.1:")


def test_dockerfile_runs_as_non_root_and_excludes_environment_files() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "USER platform" in dockerfile
    assert ".env" in dockerignore
    assert "*.key" in dockerignore


def test_example_environment_contains_only_placeholder_secrets() -> None:
    example = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "REPLACE_WITH_A_LONG_RANDOM_JWT_SECRET" in example
    assert "REPLACE_WITH_A_VALID_FERNET_KEY" in example
    assert "CELERY_TASK_IGNORE_RESULT=true" in example
    assert "SOURCE_ALLOWED_DIALECTS=postgresql" in example
