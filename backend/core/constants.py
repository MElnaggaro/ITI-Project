"""Foundation-level constants that later phases may reference."""

REQUIRED_EMBEDDING_DIMENSION = 1024
DEFAULT_SOURCE_EXECUTION_TIMEOUT_SECONDS = 30
DEFAULT_SOURCE_QUERY_ROW_LIMIT = 1000
DEFAULT_SOURCE_RESULT_SIZE_LIMIT_BYTES = 1_000_000
SUPPORTED_SOURCE_DIALECTS = frozenset({"postgresql", "sqlserver", "mysql", "oracle"})

SAFE_STATUS_MESSAGES = {
    "configuration_error": "The service configuration is invalid.",
    "authentication_not_configured": "Authentication is not configured yet.",
    "feature_not_ready": "This feature is not configured yet.",
    "internal_error": "An unexpected error occurred.",
}
