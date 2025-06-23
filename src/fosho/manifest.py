"""Manifest.json read/write/update functionality."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .hashing import compute_manifest_md5


class Manifest:
    """Manages manifest.json file operations."""

    def __init__(self, manifest_path: str = "manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.data = {"datasets": {}}

    def load(self) -> None:
        """Load existing manifest from disk."""
        if self.manifest_path.exists():
            with open(self.manifest_path, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {"datasets": {}}

    def save(self) -> None:
        """Save manifest to disk with computed manifest_md5."""
        # Remove manifest_md5 before computing hash
        temp_data = {k: v for k, v in self.data.items() if k != "manifest_md5"}

        # Compute hash of the manifest content
        manifest_content = json.dumps(temp_data, indent=2, sort_keys=True)
        manifest_hash = compute_manifest_md5(manifest_content)

        # Add hash back to data
        self.data["manifest_md5"] = manifest_hash

        # Write final manifest
        with open(self.manifest_path, "w") as f:
            json.dump(self.data, f, indent=2, sort_keys=True)

    def add_dataset(
        self, file_path: str, crc32: str, schema_md5: str, signed: bool = False
    ) -> None:
        """Add or update a dataset entry."""
        if "datasets" not in self.data:
            self.data["datasets"] = {}

        self.data["datasets"][file_path] = {
            "crc32": crc32,
            "schema_md5": schema_md5,
            "signed": signed,
            "signed_at": datetime.utcnow().isoformat() + "Z" if signed else None,
        }

    def sign_dataset(self, file_path: str) -> None:
        """Mark a dataset as signed."""
        if file_path in self.data["datasets"]:
            self.data["datasets"][file_path]["signed"] = True
            self.data["datasets"][file_path]["signed_at"] = (
                datetime.utcnow().isoformat() + "Z"
            )

    def sign_all(self) -> None:
        """Mark all datasets as signed."""
        for dataset in self.data["datasets"].values():
            dataset["signed"] = True
            dataset["signed_at"] = datetime.utcnow().isoformat() + "Z"

    def unsign_dataset(self, file_path: str) -> None:
        """Mark a dataset as unsigned (due to changes)."""
        if file_path in self.data["datasets"]:
            self.data["datasets"][file_path]["signed"] = False
            self.data["datasets"][file_path]["signed_at"] = None

    def get_dataset(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get dataset entry by file path."""
        return self.data["datasets"].get(file_path)

    def has_dataset(self, file_path: str) -> bool:
        """Check if dataset exists in manifest."""
        return file_path in self.data["datasets"]

    def get_all_datasets(self) -> Dict[str, Dict[str, Any]]:
        """Get all dataset entries."""
        return self.data["datasets"]

    def verify_integrity(self) -> bool:
        """Verify manifest integrity by checking manifest_md5."""
        if "manifest_md5" not in self.data:
            return False

        stored_hash = self.data["manifest_md5"]
        temp_data = {k: v for k, v in self.data.items() if k != "manifest_md5"}
        manifest_content = json.dumps(temp_data, indent=2, sort_keys=True)
        computed_hash = compute_manifest_md5(manifest_content)

        return stored_hash == computed_hash
