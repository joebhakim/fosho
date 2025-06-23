"""CLI interface for dsq commands using Typer."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .hashing import compute_file_crc32, compute_schema_md5
from .manifest import Manifest
from .scaffold import scaffold_dataset_schema

app = typer.Typer(
    name="dsq", help="Data Signing & Quality - Offline data integrity tool"
)
console = Console()


@app.command()
def scan(
    path: str = typer.Argument(".", help="Directory to scan for datasets"),
    overwrite_schemas: bool = typer.Option(
        False, "--overwrite-schemas", help="Regenerate schema stubs even if they exist"
    ),
):
    """Scan directory for datasets, generate schemas, and update manifest."""
    scan_path = Path(path)

    if not scan_path.exists():
        console.print(f"[red]Error: Path {path} does not exist[/red]")
        sys.exit(1)

    if not scan_path.is_dir():
        console.print(f"[red]Error: Path {path} is not a directory[/red]")
        sys.exit(1)

    # Find all CSV and Parquet files
    data_files = []
    for pattern in ["**/*.csv", "**/*.parquet", "**/*.pq"]:
        data_files.extend(scan_path.glob(pattern))

    if not data_files:
        console.print(f"[yellow]No CSV or Parquet files found in {path}[/yellow]")
        return

    console.print(f"Found {len(data_files)} dataset(s)")

    # Load or create manifest
    manifest = Manifest()
    manifest.load()

    # Process each file
    for file_path in data_files:
        try:
            relative_path = str(file_path.relative_to(Path.cwd()))
        except ValueError:
            # If file is not relative to cwd, use absolute path
            relative_path = str(file_path)
        console.print(f"Processing: {relative_path}")

        try:
            # Compute file hash
            crc32_hash = compute_file_crc32(file_path)

            # Scaffold schema
            schema, schema_file = scaffold_dataset_schema(
                file_path, overwrite=overwrite_schemas
            )

            # Compute schema hash
            schema_md5 = compute_schema_md5(schema)

            # Check if file changed
            existing_entry = manifest.get_dataset(relative_path)
            if existing_entry:
                if (
                    existing_entry["crc32"] != crc32_hash
                    or existing_entry["schema_md5"] != schema_md5
                ):
                    # File or schema changed, mark as unsigned
                    manifest.add_dataset(
                        relative_path, crc32_hash, schema_md5, signed=False
                    )
                    console.print(
                        f"  [yellow]Updated (unsigned due to changes)[/yellow]"
                    )
                else:
                    console.print(f"  [green]No changes[/green]")
            else:
                # New file
                manifest.add_dataset(
                    relative_path, crc32_hash, schema_md5, signed=False
                )
                console.print(f"  [blue]Added (unsigned)[/blue]")

            if schema_file:
                console.print(f"  Schema: {schema_file}")

        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")

    # Save manifest
    manifest.save()
    console.print(f"[green]Manifest updated: manifest.json[/green]")


@app.command()
def sign():
    """Sign all datasets in manifest (mark as approved)."""
    manifest = Manifest()
    manifest.load()

    datasets = manifest.get_all_datasets()
    if not datasets:
        console.print("[yellow]No datasets found in manifest[/yellow]")
        sys.exit(1)

    # Verify all files exist and checksums match
    console.print("Verifying datasets before signing...")

    for file_path, dataset_info in datasets.items():
        file_obj = Path(file_path)

        if not file_obj.exists():
            console.print(f"[red]Error: File {file_path} not found[/red]")
            sys.exit(1)

        # Verify checksum
        current_crc32 = compute_file_crc32(file_obj)
        if current_crc32 != dataset_info["crc32"]:
            console.print(f"[red]Error: Checksum mismatch for {file_path}[/red]")
            console.print(f"  Expected: {dataset_info['crc32']}")
            console.print(f"  Current:  {current_crc32}")
            sys.exit(1)

    # All verifications passed, sign all datasets
    manifest.sign_all()
    manifest.save()

    console.print(f"[green]Successfully signed {len(datasets)} dataset(s)[/green]")


@app.command()
def verify():
    """Verify integrity of all signed datasets."""
    manifest = Manifest()
    manifest.load()

    datasets = manifest.get_all_datasets()
    if not datasets:
        console.print("[yellow]No datasets found in manifest[/yellow]")
        sys.exit(1)

    # Verify manifest integrity
    if not manifest.verify_integrity():
        console.print("[red]Error: Manifest integrity check failed[/red]")
        sys.exit(1)

    errors = []
    unsigned_count = 0

    for file_path, dataset_info in datasets.items():
        file_obj = Path(file_path)

        # Check if file exists
        if not file_obj.exists():
            errors.append(f"File missing: {file_path}")
            continue

        # Check if signed
        if not dataset_info["signed"]:
            unsigned_count += 1
            continue

        # Verify checksum
        current_crc32 = compute_file_crc32(file_obj)
        if current_crc32 != dataset_info["crc32"]:
            errors.append(f"Checksum mismatch: {file_path}")
            # Mark as unsigned due to changes
            manifest.unsign_dataset(file_path)

    # Save manifest if we unmarked any datasets
    if any(not info["signed"] for info in datasets.values()):
        manifest.save()

    # Report results
    if errors:
        console.print("[red]Verification failed:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)

    if unsigned_count > 0:
        console.print(
            f"[yellow]Warning: {unsigned_count} dataset(s) not signed[/yellow]"
        )
        sys.exit(1)

    console.print("[green]All datasets verified successfully[/green]")


@app.command()
def status():
    """Show status of all datasets in manifest."""
    manifest = Manifest()
    manifest.load()

    datasets = manifest.get_all_datasets()
    if not datasets:
        console.print("[yellow]No datasets found in manifest[/yellow]")
        return

    table = Table()
    table.add_column("Dataset", style="cyan")
    table.add_column("CRC32", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Signed At")

    for file_path, info in datasets.items():
        status_text = "✓ Signed" if info["signed"] else "✗ Unsigned"
        status_style = "green" if info["signed"] else "yellow"

        table.add_row(
            file_path,
            info["crc32"],
            f"[{status_style}]{status_text}[/{status_style}]",
            info["signed_at"] or "Never",
        )

    console.print(table)


if __name__ == "__main__":
    app()
