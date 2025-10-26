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
