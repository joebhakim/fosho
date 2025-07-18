"""CLI interface for fosho commands using Typer."""

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
    name="fosho", help="Data Signing & Quality - Offline data integrity tool"
)
console = Console()


@app.command()
def scan(
    path: str = typer.Argument(..., help="Directory to scan for datasets"),
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

    # Find all CSV and Parquet files, excluding common directories to avoid
    excluded_dirs = {".venv", "venv", "__pycache__", ".git", "node_modules", ".pytest_cache"}
    data_files = []
    for pattern in ["**/*.csv", "**/*.parquet", "**/*.pq"]:
        for file_path in scan_path.glob(pattern):
            # Check if any parent directory is in excluded_dirs
            if any(part in excluded_dirs for part in file_path.parts):
                continue
            data_files.append(file_path)

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

    # Verify all files exist, checksums match, and schemas validate
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

        # Verify schema validates against actual data
        try:
            from .scaffold import scaffold_dataset_schema
            from .reader import read_csv_with_schema
            
            schema, _ = scaffold_dataset_schema(file_obj, overwrite=False)
            current_schema_md5 = compute_schema_md5(schema)
            
            # Check schema hash matches
            if current_schema_md5 != dataset_info["schema_md5"]:
                console.print(f"[red]Error: Schema mismatch for {file_path}[/red]")
                console.print(f"  Expected schema MD5: {dataset_info['schema_md5']}")
                console.print(f"  Current schema MD5:  {current_schema_md5}")
                console.print(f"  Run 'fosho scan' to update the manifest")
                sys.exit(1)
            
            # Validate data against schema
            df = read_csv_with_schema(file_obj, schema)
            validated_df = df.validate()  # This will raise if schema doesn't fit data
            console.print(f"  [green]✓ Schema validates {file_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error: Schema validation failed for {file_path}[/red]")
            console.print(f"  {str(e)}")
            console.print(f"  Please fix the schema or data before signing")
            sys.exit(1)

    # All verifications passed, sign all datasets
    manifest.sign_all()
    manifest.save()

    console.print(f"[green]Successfully signed {len(datasets)} dataset(s)[/green]")




@app.command()
def status():
    """Show status of all datasets with file, data, and schema verification."""
    manifest = Manifest()
    manifest.load()

    datasets = manifest.get_all_datasets()
    if not datasets:
        console.print("[yellow]No datasets found in manifest[/yellow]")
        return

    # Verify manifest integrity first
    manifest_integrity = manifest.verify_integrity()
    if not manifest_integrity:
        console.print("[red]Warning: Manifest integrity check failed[/red]")

    table = Table()
    table.add_column("Dataset", style="cyan")
    table.add_column("CRC32", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("File Status")
    table.add_column("Data Status")
    table.add_column("Schema Status")
    table.add_column("Signed At")

    changes_detected = False

    for file_path, info in datasets.items():
        file_obj = Path(file_path)

        # Check file existence
        if file_obj.exists():
            file_status = "[green]✓ Exists[/green]"
            
            # Check data integrity (CRC32)
            try:
                current_crc32 = compute_file_crc32(file_obj)
                data_match = current_crc32 == info["crc32"]
                data_status = "[green]✓ Valid[/green]" if data_match else "[red]✗ Changed[/red]"
                
                # Check schema if file exists and we can load it
                try:
                    from .scaffold import scaffold_dataset_schema
                    schema, _ = scaffold_dataset_schema(file_obj, overwrite=False)
                    current_schema_md5 = compute_schema_md5(schema)
                    schema_match = current_schema_md5 == info["schema_md5"]
                    schema_status = "[green]✓ Valid[/green]" if schema_match else "[yellow]⚠ Changed[/yellow]"
                except Exception:
                    schema_status = "[gray]? Unknown[/gray]"
                    schema_match = True  # Don't treat as error if we can't check
                
                # Mark as unsigned if data changed
                if not data_match and info["signed"]:
                    manifest.unsign_dataset(file_path)
                    changes_detected = True
                    info["signed"] = False
                    info["signed_at"] = None
                    
            except Exception as e:
                data_status = f"[red]✗ Error: {str(e)[:20]}...[/red]"
                schema_status = "[gray]? Unknown[/gray]"
        else:
            file_status = "[red]✗ Missing[/red]"
            data_status = "[red]✗ Missing[/red]"
            schema_status = "[red]✗ Missing[/red]"

        # Overall status
        status_text = "✓ Signed" if info["signed"] else "✗ Unsigned"
        status_style = "green" if info["signed"] else "yellow"

        table.add_row(
            file_path,
            info["crc32"],
            f"[{status_style}]{status_text}[/{status_style}]",
            file_status,
            data_status,
            schema_status,
            info["signed_at"] or "Never",
        )

    console.print(table)

    # Save manifest if we unmarked any datasets due to data changes
    if changes_detected:
        manifest.save()
        console.print("\n[yellow]Note: Some datasets were automatically unsigned due to data changes[/yellow]")

    # Summary counts
    total = len(datasets)
    signed_count = sum(1 for info in datasets.values() if info["signed"])
    console.print(f"\nSummary: {signed_count}/{total} datasets signed")


if __name__ == "__main__":
    app()
