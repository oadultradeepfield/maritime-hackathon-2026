# Maritime Hackathon 2026

[Project description - to be added]

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
# Clone repository
git clone <repo-url>
cd maritime-hackathon-2026

# Install dependencies
make install-dev
```

## Development

```bash
# Format and lint code
make format

# Run all checks
make check

# See all available commands
make help
```

## Project Structure

```
maritime-hackathon-2026/
├── src/           # Source code
├── dataset/       # Data files (gitignored)
├── main.py        # Entry point
└── Makefile       # Development commands
```

## Notes

- Copy `.env.example` to `.env` for environment variables
- Data files are gitignored to prevent accidental commits
