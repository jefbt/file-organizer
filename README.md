# Organizer App (Gold Edition)

A modern Python GUI application for file renaming and image conversion, built with `customtkinter` and `uv`.

## Features
- **Theme**: Dark mode with Gold & Black aesthetics.
- **Renaming**: Remove prefixes/suffixes by count or expression.
- **Converting**: Convert images between formats (PNG, JPG, WEBP, etc.), with option to keep or delete originals.

## Prerequisites
- Python 3.12+
- `uv` package manager (recommended)

## Installation & Running

1. **Initialize/Sync Dependencies**:
   ```powershell
   uv sync
   ```

2. **Run the App**:
   ```powershell
   uv run main.py
   ```
   
   *Or if using standard python:*
   ```powershell
   pip install customtkinter pillow packaging
   python main.py
   ```
