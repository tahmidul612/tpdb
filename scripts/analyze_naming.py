#!/usr/bin/env python3
"""
Analyze Python code for camelCase naming conventions.

This module provides functions to detect camelCase names in Python files
that should be converted to snake_case per PEP 8 conventions.
"""

import re
from pathlib import Path
from typing import Dict, Set


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case.

    Args:
        name: The camelCase name to convert

    Returns:
        The snake_case equivalent

    Example:
        >>> camel_to_snake("myVariableName")
        'my_variable_name'
    """
    # Insert underscore before uppercase letters that follow lowercase letters
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters that follow numbers or lowercase letters
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def is_class_name(name: str) -> bool:
    """Check if a name is PascalCase (class name).

    Args:
        name: The name to check

    Returns:
        True if the name is PascalCase, False otherwise
    """
    return bool(name and name[0].isupper() and "_" not in name)


def is_external_library_call(name: str) -> bool:
    """Check if a name is likely from an external library.

    Args:
        name: The name to check

    Returns:
        True if the name is from an external library, False otherwise
    """
    # Common external library methods/functions that use camelCase
    external_patterns: Set[str] = {
        # thefuzz library
        "extractOne",
        "extractBests",
        "extract",
        # Process methods (from thefuzz.process)
        "tokenSort",
        "tokenSet",
        "partialRatio",
        # Logging
        "getLogger",
        "setLevel",
        "addHandler",
        "basicConfig",
        # OS/pathlib
        "splitext",
        "isfile",
        "isdir",
        "makedirs",
        # Rich/typer (though most are already snake_case)
        "addTask",
        # Plex API
        "PlexServer",
        # HTTP/requests
        "iter_content",
        # String methods
        "startswith",
        "endswith",
        "splitlines",
        # File methods
        "readlines",
        "writelines",
        # Collections
        "defaultdict",
        # zipfile
        "is_zipfile",
        "extractall",
        # shutil
        "rmtree",
        "samefile",
        # re module
        "findall",
        "finditer",
    }

    return name in external_patterns


def find_camel_case_names(file_path: Path) -> Dict[str, str]:
    """Find all camelCase function and variable names in a Python file.

    Args:
        file_path: Path to the Python file to analyze

    Returns:
        Dictionary mapping camelCase names to their snake_case equivalents
    """
    with open(file_path, "r") as f:
        content = f.read()

    # Find function definitions: def functionName(
    functions = re.findall(r"def\s+([a-z][a-zA-Z0-9]*)\s*\(", content)

    # Find variable assignments: variableName =
    variables = re.findall(r"^\s*([a-z][a-zA-Z0-9]*)\s*=", content, re.MULTILINE)

    # Find loop variables: for varName in ...
    loop_vars = re.findall(r"for\s+([a-z][a-zA-Z0-9]*)\s+in\s+", content)

    # Find function calls: functionName(
    function_calls = re.findall(r"\b([a-z][a-zA-Z0-9]*)\s*\(", content)

    # For function definitions and variables (things we define), include them
    our_definitions = set(functions + variables + loop_vars)

    # For calls and attributes, only include if they're likely our own code
    potential_names = our_definitions.copy()

    # Add function calls that aren't external library calls
    for name in function_calls:
        if name not in is_external_library_call.__code__.co_consts:
            potential_names.add(name)

    camel_case_names = {}
    for name in potential_names:
        # Skip if already snake_case or single word
        if "_" in name or name.islower():
            continue
        # Skip if it's a class name (PascalCase)
        if is_class_name(name):
            continue
        # Skip if it's an external library call
        if is_external_library_call(name):
            continue
        # Check if it has uppercase letters (camelCase)
        if any(c.isupper() for c in name):
            snake_name = camel_to_snake(name)
            camel_case_names[name] = snake_name

    return camel_case_names


def analyze_files(directory: Path) -> Dict[str, Dict[str, str]]:
    """Analyze all Python files in the directory for camelCase names.

    Args:
        directory: Directory to search for Python files

    Returns:
        Dictionary mapping file paths to their camelCase conversions
    """
    python_files = list(directory.rglob("*.py"))
    all_conversions = {}

    for file_path in python_files:
        # Skip this conversion script itself
        if "analyze_naming.py" in str(file_path) or "apply_snake_case.py" in str(
            file_path
        ):
            continue

        conversions = find_camel_case_names(file_path)

        if conversions:
            all_conversions[str(file_path)] = conversions

    return all_conversions


def get_unique_conversions(
    all_conversions: Dict[str, Dict[str, str]],
) -> Dict[str, str]:
    """Get all unique conversions across all files.

    Args:
        all_conversions: Dictionary of file paths to their conversions

    Returns:
        Dictionary of unique camelCase to snake_case mappings
    """
    unique_conversions = {}
    for file_conversions in all_conversions.values():
        for camel, snake in file_conversions.items():
            if camel not in unique_conversions:
                unique_conversions[camel] = snake
    return unique_conversions


def print_file_analysis(file_path: Path, conversions: Dict[str, str]) -> None:
    """Print analysis results for a single file.

    Args:
        file_path: Path to the analyzed file
        conversions: Dictionary of camelCase to snake_case conversions
    """
    print(f"\n{'=' * 80}")
    print(f"Analyzing: {file_path}")
    print("=" * 80)

    if conversions:
        print(f"\nFound {len(conversions)} camelCase names:\n")
        for camel, snake in sorted(conversions.items()):
            print(f"  {camel:30} → {snake}")
    else:
        print("\n✓ No camelCase names found (or all already converted)")


def generate_conversion_report(all_conversions: Dict[str, Dict[str, str]]) -> None:
    """Generate a detailed conversion report.

    Args:
        all_conversions: Dictionary mapping file paths to their conversions
    """
    print("\n" + "=" * 80)
    print("CONVERSION SUMMARY")
    print("=" * 80)

    unique_conversions = get_unique_conversions(all_conversions)

    if unique_conversions:
        print(f"\nTotal unique camelCase names to convert: {len(unique_conversions)}\n")
        print("Conversion mapping:")
        print("-" * 80)
        for camel, snake in sorted(unique_conversions.items()):
            print(f"  {camel:35} → {snake}")

        print("\n" + "=" * 80)
        print("FILES TO UPDATE:")
        print("=" * 80)
        for file_path in sorted(all_conversions.keys()):
            print(f"  - {file_path}")

        print("\n" + "=" * 80)
        print("RECOMMENDED ACTIONS:")
        print("=" * 80)
        print("""
1. Review the conversion mapping above carefully
2. Some conversions might need manual review (e.g., acronyms, domain-specific terms)
3. Use the apply_snake_case.py script to automatically apply conversions
4. Update tests after renaming
5. Run linters and type checkers after conversion

Note: This is a detection script only. It does NOT modify files automatically.
Use apply_snake_case.py to apply the conversions.
        """)
    else:
        print("\n✓ No camelCase names found in the project!")


def main() -> int:
    """Main function for standalone execution.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    print("=" * 80)
    print("Python camelCase to snake_case Analyzer")
    print("=" * 80)
    print("\nThis script analyzes Python files and identifies camelCase names")
    print("that should be converted to snake_case per PEP 8 conventions.")
    print("\nNOTE: This script only DETECTS, it does not modify files.\n")

    # Analyze src directory (go up one level from scripts/)
    src_dir = Path(__file__).parent.parent / "src"

    if not src_dir.exists():
        print(f"Error: Directory not found: {src_dir}")
        return 1

    all_conversions = analyze_files(src_dir)

    # Print detailed analysis for each file
    for file_path, conversions in all_conversions.items():
        print_file_analysis(Path(file_path), conversions)

    # Print summary report
    generate_conversion_report(all_conversions)

    return 0


if __name__ == "__main__":
    exit(main())
