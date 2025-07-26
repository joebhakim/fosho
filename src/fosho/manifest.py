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
        self, 
        identifier: str, 
        source_type: str,
        content_hash: str, 
        schema_md5: Optional[str] = None, 
        signed: bool = False,
        scaffolded: bool = False,
        schema_path: Optional[str] = None,
        dataset_name: Optional[str] = None
    ) -> None:
        """Add or update a dataset entry.
        
        Args:
            identifier: File path for local files, dataset name for remote
            source_type: "local_file" or "remote_dataset"
            content_hash: CRC32 for files, dataset hash for remote datasets
            schema_md5: MD5 of the schema (None if not scaffolded)
            signed: Whether the dataset is signed
            scaffolded: Whether a schema has been generated
            schema_path: Path to the schema file
            dataset_name: Name for remote datasets
        """
        if "datasets" not in self.data:
            self.data["datasets"] = {}

        entry = {
            "source_type": source_type,
            "signed": signed,
            "signed_at": datetime.utcnow().isoformat() + "Z" if signed else None,
            "scaffolded": scaffolded,
            "schema_path": schema_path,
        }

        if source_type == "local_file":
            entry["crc32"] = content_hash
        elif source_type == "remote_dataset":
            entry["dataset_hash"] = content_hash
            entry["dataset_name"] = dataset_name or identifier
        else:
            raise ValueError(f"Unknown source_type: {source_type}")

        if schema_md5:
            entry["schema_md5"] = schema_md5

        self.data["datasets"][identifier] = entry

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

    def scaffold_dataset(self, identifier: str, schema_md5: str, schema_path: str) -> None:
        """Mark a dataset as scaffolded with schema information."""
        if identifier in self.data["datasets"]:
            self.data["datasets"][identifier]["scaffolded"] = True
            self.data["datasets"][identifier]["schema_md5"] = schema_md5
            self.data["datasets"][identifier]["schema_path"] = schema_path

    def unscaffold_dataset(self, identifier: str) -> None:
        """Mark a dataset as not scaffolded (schema needs regeneration)."""
        if identifier in self.data["datasets"]:
            self.data["datasets"][identifier]["scaffolded"] = False
            self.data["datasets"][identifier].pop("schema_md5", None)
            self.data["datasets"][identifier]["schema_path"] = None

    def get_content_hash(self, identifier: str) -> Optional[str]:
        """Get the content hash for a dataset (CRC32 for files, dataset_hash for remote)."""
        entry = self.get_dataset(identifier)
        if not entry:
            return None
        return entry.get("crc32") or entry.get("dataset_hash")

    def is_local_file(self, identifier: str) -> bool:
        """Check if dataset is a local file."""
        entry = self.get_dataset(identifier)
        return entry and entry.get("source_type") == "local_file"

    def is_remote_dataset(self, identifier: str) -> bool:
        """Check if dataset is a remote dataset."""
        entry = self.get_dataset(identifier)
        return entry and entry.get("source_type") == "remote_dataset"

    def is_scaffolded(self, identifier: str) -> bool:
        """Check if dataset has been scaffolded."""
        entry = self.get_dataset(identifier)
        return entry and entry.get("scaffolded", False)

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
