# Repository Guidelines

## Project Structure & Module Organization
- `app/` holds core pipeline logic and schemas (`app/pipeline.py`, `app/schemas.py`).
- Top-level scripts are small entry points: `run.py` for batch processing, `client.py`/`config.py` for OpenAI client setup, and `01_smoke_test.py` for a quick API check.
- `examples/` contains reference usage scripts.
- `data/` stores sample inputs (for example `data/sample.txt`).

## Build, Test, and Development Commands
- `python -m pip install -r requirements.txt` installs runtime dependencies.
- `python run.py data/sample.txt` runs the pipeline and writes `data/sample.result.json`.
- `python 01_smoke_test.py` verifies the API key and client connectivity (prints a short response).

## Coding Style & Naming Conventions
- Python 3, 4-space indentation, UTF-8 text files.
- Use `snake_case` for functions and variables; keep modules short and single-purpose.
- Keep CLI scripts small and delegate logic to `app/` modules.

## Testing Guidelines
- No formal test framework is configured. Use `01_smoke_test.py` as a manual sanity check.
- Name any future tests with a clear prefix (for example `test_pipeline_*.py`) and keep them close to the code they cover.

## Commit & Pull Request Guidelines
- No Git history is present to infer a convention. If you add commits, use concise, present-tense messages (for example `Add pipeline summary step`).
- PRs should include a short description, a list of key changes, and any required sample inputs/outputs.

## Security & Configuration Tips
- Set `OPENAI_API_KEY` in `.env` before running scripts.
- Avoid committing secrets or generated result files.
