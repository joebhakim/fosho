def main() -> None:
    """Main entry point for fosho CLI with dsq subcommands."""
    from .cli import app

    app()
