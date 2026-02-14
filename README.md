# File Organizer - Gold Edition

A modern, dark-themed desktop application for organizing files, built with Python and CustomTkinter.

## Features

### 1. Batch Renaming
- **Ordered Renaming**: Rename files with a sequence number and pattern (e.g., `File-001`, `File-002`).
  - Use `@` symbols to define the number padding (e.g., `@@@` becomes `001`).
- **Remove Text**: Remove specific words or characters from filenames.
- **Position-based**: Remove characters before or after a specific point.
- **Drag & Drop**: Easily add files by dragging them from your file explorer.
- **Sorting**: Sort files by name, date, or invert the list order before processing.

### 2. Image Conversion
- Convert images between formats: **PNG, JPG, JPEG, WEBP, BMP, ICO, TIFF, GIF**.
- Option to keep or delete original files after conversion.
- Drag & Drop support for images.

## Installation & Running (Development)

This project uses `uv` for dependency management.

1. **Install uv** (if not installed):
   ```powershell
   pip install uv
   ```

2. **Install dependencies**:
   ```powershell
   uv sync
   # OR manually
   uv pip install -r requirements.txt
   ```

3. **Run the application**:
   ```powershell
   uv run main.py
   ```

## Building the Executable (Windows)

To create a standalone `.exe` file using PyInstaller:

1. **Install PyInstaller**:
   ```powershell
   uv pip install pyinstaller
   ```

2. **Run the build command**:
   Run the following command in PowerShell from the project root. This ensures `customtkinter` and `tkinterdnd2` assets are correctly bundled.

   ```powershell
   uv run pyinstaller --noconfirm --onedir --windowed --name "File Organizer" --icon "icon.ico" `
     --add-data ".venv/Lib/site-packages/customtkinter;customtkinter/" `
     --add-data ".venv/Lib/site-packages/tkinterdnd2;tkinterdnd2/" `
     main.py
   ```

   ```powershell
   uv run pyinstaller --noconfirm --onedir --windowed --name "File Organizer" --icon "icon.ico" --add-data ".venv/Lib/site-packages/customtkinter;customtkinter/" --add-data ".venv/Lib/site-packages/tkinterdnd2;tkinterdnd2/" main.py
   ```

   one file
   ```powershell
   uv run pyinstaller --noconfirm --onefile --windowed --name "File Organizer" --icon "icon.ico" --add-data ".venv/Lib/site-packages/customtkinter;customtkinter/" --add-data ".venv/Lib/site-packages/tkinterdnd2;tkinterdnd2/" main.py
   ```

   > **Note**: If your virtual environment path is different, replace `.venv/Lib/site-packages/...` with the correct path to your site-packages.

3. **Locate the App**:
   The executable will be generated in the `dist/File Organizer/` folder.
