# Contributor Guidelines

- Follow PEP8 style and use 4 spaces for indentation.
- Run `pytest` before committing to ensure tests pass.
- Keep functions small and focused.
- **Verify that every imported external module is listed in `requirements.txt`.**
  To detect missing modules before launching the container, you can use `pipreqs`:
  ```bash
  pip install pipreqs
  pipreqs . --force --savepath requirements.generated.txt
  comm -23 <(sort requirements.generated.txt) <(sort requirements.txt)
  ```
  Any names printed by the `comm` command are packages that should be added to `requirements.txt`.
