# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**qunhui-nas** (群晖 NAS) is a FastAPI-based webhook service for managing Synology NAS operations through SSH.

The application receives HTTP webhook requests and executes SSH commands on a Synology NAS to perform:
- User creation and group assignment
- User enable/disable operations
- File reading and writing

Code comments are in Chinese (项目使用中文注释).

## Development Commands

This project uses [UV](https://github.com/astral-sh/uv) as the package manager with the Tsinghua University PyPI mirror.

```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py

# Add a new dependency
uv add <package>

# Run with specific Python version (requires Python 3.13+)
uv run --python 3.13 python main.py
```

## Architecture

The application follows a **minimalist flat structure** (not MVC or layered architecture):

```
main.py          → FastAPI entry point, receives webhook requests
app/nas.py       → Core NAS operations via SSH
env.example      → Environment configuration template
pyproject.toml   → UV-based dependency management
```

**Request Flow**: Webhook → FastAPI → Token/IP/Path validation → SSH to NAS → Execute operation

**Security Layers** (in order):
1. `TOKEN` - Comma-separated connection tokens for authentication
2. `ALLOW_IP` - IP whitelist for access control
3. `ALLOW_FILE_PATH` - File path access restrictions
4. `RSA_PRIVATE_KEY` - SSH private key for NAS authentication

## Environment Setup

Copy `env.example` to `.env` and configure:

```bash
TOKEN=XXXX1,XXXX2              # Comma-separated auth tokens
ALLOW_IP=127.0.0.1,192.168.1.1  # Comma-separated allowed IPs
ALLOW_FILE_PATH=                # Allowed file paths (empty = unrestricted)
RSA_PRIVATE_KEY=                # SSH private key content
```

## Key Conventions

- **Flat structure**: No formal MVC, service layers, or utilities directory
- **Chinese comments**: Code documentation uses Chinese
- **Environment-based config**: All configuration via environment variables
- **No test framework**: No testing, linting, or formatting currently configured
- **Python 3.13+**: Requires latest Python version

## Critical Files

- [main.py](main.py) - FastAPI webhook receiver
- [app/nas.py](app/nas.py) - SSH-based NAS operations
- [pyproject.toml](pyproject.toml) - Project dependencies and UV configuration
- [env.example](env.example) - Environment variable template
