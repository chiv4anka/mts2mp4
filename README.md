| Version | Source | Build script | Output |
|---|---|---|---|
| GUI (window) | `mts2mp4.py` | `build.bat` | `dist\mts2mp4.exe` |

The resulting `.exe` is fully standalone: ffmpeg is bundled inside, and the person running it does not need Python.

## Requirements

- Windows 10 or 11 (64-bit)
- Python 3.9 or newer
- ffmpeg.exe
- An internet connection (only during the build, to download PyInstaller)

## Step 1. Install Python

1. Download Python from <https://www.python.org/downloads/>.
2. Run the installer and **tick "Add python.exe to PATH"** on the first screen.
3. Click "Install Now".
4. Verify: open Command Prompt and run `python --version`. You should see a version number.

## Step 2. Get ffmpeg.exe

1. Go to <https://www.gyan.dev/ffmpeg/builds/>.
2. Under "release builds", download **ffmpeg-release-essentials.zip**.
3. Open the zip and extract `bin\ffmpeg.exe` (only this one file is needed).

## Step 3. Prepare the folder

Put these files together in one folder, for example `C:\mts2mp4`:

```
C:\mts2mp4\
    mts2mp4.py
    build.bat
    ffmpeg.exe
```

## Step 4. Build

Double-click the script for the version you want:

- `build.bat` builds the GUI version.

The script installs PyInstaller, then packages the program. This takes one to two minutes. The window stays open at the end so you can read the result.

When it finishes, your file is here:

```
C:\mts2mp4\dist\mts2mp4.exe
```

Copy it anywhere you like. You can delete the `build`, `dist` and `.spec` leftovers afterwards.

## Manual build (without the .bat files)

Open Command Prompt in the project folder and run:

```
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name mts2mp4 --add-binary "ffmpeg.exe;." mts2mp4.py
```

For the command-line version, use `--console` instead of `--windowed`

## Troubleshooting

| Message | Fix |
|---|---|
| `ffmpeg.exe not found` | Put `ffmpeg.exe` in the same folder as the build script. |
| `Python not found` | Reinstall Python and tick "Add python.exe to PATH", or try `py -3` instead of `python`. |
| `Could not install PyInstaller` | Check your internet connection, proxy or VPN. |
| Antivirus flags the .exe | This is a common false positive for PyInstaller programs. Add an exception, or build it yourself and keep the source. |
| The .exe does not start | Rebuild without `--windowed` (use `--console`) to see error messages in a console. |
| Window closes instantly | Open Command Prompt in the folder and run `build.bat` from there to see the output. |


You can also drag and drop files or a folder onto the .exe.
