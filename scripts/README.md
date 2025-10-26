# Utility Scripts

This directory contains utility scripts for code maintenance and refactoring.

## Available Scripts

### 1. `analyze_naming.py` - Code Analysis Tool

Analyzes Python source files to detect camelCase naming that should be converted to snake_case per PEP 8.

**Usage:**

```bash
# Analyze the codebase
python scripts/analyze_naming.py

# Or from scripts directory
cd scripts
python analyze_naming.py
```

**Features:**

- Detects camelCase functions, variables, and loop variables
- Excludes external library calls (thefuzz, plexapi, etc.)
- Preserves PascalCase for class names
- Generates detailed conversion report
- Read-only analysis - doesn't modify files

**Output Example:**

```plaintext
Found 2 camelCase names:
  mediaRoot → media_root
  posterZip → poster_zip
```

**Module API:**

The script can also be imported as a module:

```python
from analyze_naming import (
    analyze_files,
    camel_to_snake,
    find_camel_case_names,
    get_unique_conversions,
)

# Analyze a directory
conversions = analyze_files(Path("src/"))

# Get unique conversions
unique = get_unique_conversions(conversions)

# Convert a name
snake_name = camel_to_snake("myVariableName")  # Returns: "my_variable_name"
```

### 2. `apply_snake_case.py` - Automated Conversion Tool

Automatically applies camelCase to snake_case conversions detected by `analyze_naming.py`.

**Usage:**

```bash
# Dry run (see what would change without modifying files)
python scripts/apply_snake_case.py --dry-run

# Interactive mode (prompt before each file)
python scripts/apply_snake_case.py --interactive

# Apply all conversions automatically
python scripts/apply_snake_case.py

# Show help
python scripts/apply_snake_case.py --help
```

**Command-Line Options:**

- `-n, --dry-run` - Preview changes without modifying files
- `-i, --interactive` - Prompt before modifying each file
- `-h, --help` - Show usage information

**Safety Features:**

- Uses word-boundary regex to avoid partial matches
- Imports detection logic from `analyze_naming.py` (no hardcoded mappings)
- Provides dry-run mode to preview changes
- Shows occurrence count for each replacement
- Interactive mode for manual review

**Workflow Example:**

```bash
# Step 1: Analyze the codebase
python scripts/analyze_naming.py

# Step 2: Preview changes
python scripts/apply_snake_case.py --dry-run

# Step 3: Apply conversions interactively
python scripts/apply_snake_case.py --interactive

# Step 4: Verify changes
git diff
ruff check src/
pytest
```

## Design Philosophy

Both scripts follow Python best practices:

### Modularity

- `analyze_naming.py` provides reusable functions that `apply_snake_case.py` imports
- No hardcoded mappings - conversions are dynamically discovered
- Clear separation between analysis and modification

### Type Safety

- Full type hints throughout (`typing.Dict`, `Path`, etc.)
- Documented function signatures with Args/Returns
- Passes Pylance/Pyright type checking

### Code Quality

- Comprehensive docstrings (Google style)
- Clear variable names and function purposes
- Passes ruff linting with zero errors
- Follows PEP 8 conventions

### Robustness

- Word-boundary regex prevents partial replacements
- Filters out external library calls (extractOne, getLogger, etc.)
- Skips class names (PascalCase)
- Handles edge cases (loop variables, function calls)

### User Experience

- Clear, informative output with progress indicators
- Dry-run mode for safe previews
- Interactive mode for manual control
- Helpful next-steps guidance after completion

## Architecture

### Data Flow

```plaintext
analyze_naming.py                apply_snake_case.py
─────────────────                ────────────────────

1. Scan Python files    ────────>  Import functions
2. Extract names
3. Filter external libs
4. Generate conversions ────────>  2. Apply regex replacements
5. Return Dict[str,str]            3. Write modified files
                                   4. Report results
```

### Key Functions

**analyze_naming.py:**

- `find_camel_case_names(file_path)` - Analyze a single file
- `analyze_files(directory)` - Analyze all Python files in directory
- `get_unique_conversions(all_conversions)` - Aggregate unique conversions
- `camel_to_snake(name)` - Convert a single name
- `is_external_library_call(name)` - Filter external library methods

**apply_snake_case.py:**

- `apply_conversions_to_file(file_path, conversions, dry_run)` - Process one file
- `apply_all_conversions(src_dir, dry_run, interactive)` - Process all files
- `main()` - CLI entry point with argument parsing

## Common Patterns

### Adding New External Library Exclusions

If a new library is added and uses camelCase:

```python
# In analyze_naming.py -> is_external_library_call()
external_patterns: Set[str] = {
    # ... existing entries ...
    # New library
    "newLibraryMethod",
    "anotherMethod",
}
```

### Extending Analysis

To detect additional naming patterns:

```python
# In analyze_naming.py -> find_camel_case_names()

# Example: Detect camelCase in list comprehensions
list_comp_vars = re.findall(r"for\s+([a-z][a-zA-Z0-9]*)\s+in.*\]", content)
```

## Testing

Both scripts include built-in test modes:

```bash
# Test analyze_naming.py
python scripts/analyze_naming.py  # Read-only, safe to run

# Test apply_snake_case.py (safe dry-run)
python scripts/apply_snake_case.py --dry-run
```

## Maintenance

When updating these scripts:

1. **Preserve the module API** - Other scripts may import these functions
1. **Add type hints** - All public functions should have full type annotations
1. **Update docstrings** - Keep documentation in sync with code changes
1. **Test both modes** - Run standalone and as imported module
1. **Verify ruff compliance** - Run `ruff check scripts/` before committing

## Future Enhancements

Potential improvements:

- [ ] Add support for converting file names (e.g., `myModule.py` → `my_module.py`)
- [ ] Detect camelCase in string literals (e.g., dict keys)
- [ ] Generate git-compatible patch files for review
- [ ] Add undo/rollback functionality
- [ ] Support custom conversion rules via config file
- [ ] Parallel processing for large codebases
- [ ] Integration with pre-commit hooks
