## v0.3.0 (2025-10-26)

### Feat

- add scripts for analyzing and converting camelCase to snake_case

### Refactor

- use prompt helper in sync_movie_folder function
- use prompt helpers in process_zip_file function
- use prompt helper for poster organization in organize_movie_collection_folder
- use prompt helper for poster organization in organize_movie_folder
- extract user prompt helpers into dedicated functions
- replace input prompts with typer for improved user interaction
- enhance download handling in main_callback to allow continued processing
- update function signatures and improve error handling in main.py
- remove unused import of string module
- remove unused imports from main.py
- add Options class and global variables to main.py
- replace fake Opts class with proper Options class in CLI
- remove old root-level scripts and integrate rich in dupes.py
- create src/tpdb structure and add typer/rich dependencies

## v0.2.0 (2025-10-26)

### Feat

- add author information and license to pyproject.toml
- add python project and pre-commit configuration files
- add CLAUDE.md for project documentation and usage instructions
- add unit tests for name normalization function
- implement movie collection organization for poster files in media library
- enhance name normalization by removing year references and improve matching score calculation
- add name normalization function for improved media matching accuracy
- implement media matching function for improved zip file processing
- replace tqdm with alive-progress for improved download feedback
- add option to force rename movie poster folder instead of matching
- update zip file renaming logic
- folder fuzzy duplicate checker

### Fix

- remove unnecessary Python extension recommendations from VSCode config
- Address PR feedback on mutable default arguments (#2)
- update type annotation
- fix handling user input
- fix handling existing zip in archive folder

### Refactor

- streamline library selection and folder processing logic (using o3-mini)
- add selectedlibrary check
