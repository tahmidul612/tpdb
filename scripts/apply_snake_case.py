#!/usr/bin/env python3
"""
Apply automated camelCase to snake_case conversions.

This script uses the analyze_naming module to detect camelCase names
and automatically applies the conversions to Python source files.
"""

import re
import sys
from pathlib import Path
from typing import Dict

# Import from analyze_naming module
from analyze_naming import analyze_files, get_unique_conversions


def apply_conversions_to_file(
    file_path: Path, conversions: Dict[str, str], dry_run: bool = False
) -> bool:
    """Apply snake_case conversions to a single file.

    Args:
        file_path: Path to the file to modify
        conversions: Dictionary mapping camelCase to snake_case names
        dry_run: If True, only show what would be changed without modifying files

    Returns:
        True if any changes were made (or would be made in dry_run mode)
    """
    with open(file_path, "r") as f:
        content = f.read()

    changes_made = False

    # Apply each conversion using word boundary matching
    for camel_case, snake_case in conversions.items():
        # Use word boundary \b to avoid partial matches
        # This ensures we only match complete identifiers
        pattern = rf"\b{re.escape(camel_case)}\b"
        new_content = re.sub(pattern, snake_case, content)

        if new_content != content:
            changes_made = True
            count = content.count(camel_case)
            print(f"  {camel_case} → {snake_case} ({count} occurrences)")
            content = new_content

    # Write changes if not in dry-run mode and changes were made
    if changes_made and not dry_run:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✓ Updated {file_path}")
    elif changes_made and dry_run:
        print(f"[DRY RUN] Would update {file_path}")
    else:
        print(f"- No changes needed for {file_path}")

    return changes_made


def apply_all_conversions(
    src_dir: Path, dry_run: bool = False, interactive: bool = False
) -> int:
    """Apply conversions to all files in the directory.

    Args:
        src_dir: Directory containing Python files to process
        dry_run: If True, only show what would be changed
        interactive: If True, prompt before applying changes to each file

    Returns:
        Number of files modified (or that would be modified in dry_run mode)
    """
    # Use analyze_naming to find all conversions
    all_conversions = analyze_files(src_dir)

    if not all_conversions:
        print("✓ No camelCase names found - all files already use snake_case!")
        return 0

    # Get unique conversions across all files
    unique_conversions = get_unique_conversions(all_conversions)

    print("\n" + "=" * 80)
    print("CONVERSION PLAN")
    print("=" * 80)
    print(f"\nWill convert {len(unique_conversions)} unique camelCase names:")
    print("-" * 80)
    for camel, snake in sorted(unique_conversions.items()):
        print(f"  {camel:30} → {snake}")

    print("\n" + "=" * 80)
    print(f"Files to process: {len(all_conversions)}")
    print("=" * 80)

    if dry_run:
        print("\n[DRY RUN MODE - No files will be modified]\n")
    elif interactive:
        response = input("\nProceed with conversions? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print("Conversion cancelled.")
            return 0

    files_modified = 0

    # Apply conversions to each file
    for file_path_str, file_conversions in all_conversions.items():
        file_path = Path(file_path_str)
        print(f"\n{'=' * 80}")
        print(f"Processing: {file_path}")
        print("=" * 80)

        if interactive and not dry_run:
            response = input(f"Update {file_path.name}? [Y/n]: ").strip().lower()
            if response in ("n", "no"):
                print("Skipped.")
                continue

        if apply_conversions_to_file(file_path, file_conversions, dry_run):
            files_modified += 1

    return files_modified


def main() -> int:
    """Main function for standalone execution.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    print("=" * 80)
    print("Python camelCase to snake_case Converter")
    print("=" * 80)
    print("\nThis script automatically converts camelCase names to snake_case")
    print("in Python source files per PEP 8 conventions.\n")

    # Parse command-line arguments
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    interactive = "--interactive" in sys.argv or "-i" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python apply_snake_case.py [OPTIONS]")
        print("\nOptions:")
        print("  -n, --dry-run      Show what would be changed without modifying files")
        print("  -i, --interactive  Prompt before modifying each file")
        print("  -h, --help         Show this help message")
        print("\nExample:")
        print("  python apply_snake_case.py --dry-run")
        print("  python apply_snake_case.py --interactive")
        return 0

    # Find src directory
    src_dir = Path(__file__).parent.parent / "src"

    if not src_dir.exists():
        print(f"Error: Directory not found: {src_dir}")
        return 1

    # Apply conversions
    files_modified = apply_all_conversions(src_dir, dry_run, interactive)

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if dry_run:
        print(f"\n[DRY RUN] {files_modified} file(s) would be modified")
        print("\nRun without --dry-run to apply changes.")
    else:
        print(f"\n✓ Successfully modified {files_modified} file(s)")
        print("\nRecommended next steps:")
        print("  1. Run: ruff check src/")
        print("  2. Run: pytest")
        print("  3. Review changes with: git diff")

    return 0


if __name__ == "__main__":
    exit(main())
