"""Unit tests for LocalStorageService file persistence and checksums."""

import hashlib
import tempfile
from uuid import uuid4

from services.storage_service import LocalStorageService


def test_storage_service_save_and_delete():
    """Verify LocalStorageService saves bytes, calculates SHA-256 checksum, and deletes file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalStorageService(base_dir=temp_dir)
        tenant_id = uuid4()
        content = b"Sample document text content for unit testing."

        stored_name, path, checksum = storage.save_file(
            tenant_id=tenant_id,
            file_bytes=content,
            original_name="report.pdf",
        )

        assert stored_name.endswith("_report.pdf")
        assert checksum == hashlib.sha256(content).hexdigest()

        # Delete file
        deleted = storage.delete_file(path)
        assert deleted is True
