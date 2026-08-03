"""Local Object Storage service for tenant document files with SHA-256 checksum calculation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from app.config import get_settings


class LocalStorageService:
    """Manages tenant-isolated local object storage for uploaded files."""

    def __init__(self, base_dir: str | None = None) -> None:
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            settings = get_settings()
            self.base_dir = Path(getattr(settings, "storage_dir", "./storage"))

    def save_file(self, tenant_id: UUID, file_bytes: bytes, original_name: str) -> tuple[str, str, str]:
        """Save file bytes to tenant-isolated path and return (stored_name, storage_path, checksum)."""
        tenant_dir = self.base_dir / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(original_name).suffix
        unique_prefix = str(uuid4())[:8]
        stored_name = f"{unique_prefix}_{original_name}"
        full_path = tenant_dir / stored_name

        full_path.write_bytes(file_bytes)
        checksum = hashlib.sha256(file_bytes).hexdigest()

        return stored_name, str(full_path.resolve()), checksum

    def delete_file(self, storage_path: str) -> bool:
        """Delete file from disk if present."""
        path = Path(storage_path)
        if path.exists():
            path.unlink()
            return True
        return False
