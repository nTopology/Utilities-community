# Builds nest_pack.exe from nest_pack.py with PyInstaller, using uv for a private Python 3.12.
# Run from anywhere; needs uv on the PATH and internet for the first run (PyInstaller, numpy, Pillow).
$root = Split-Path $PSScriptRoot -Parent
$build = Join-Path $env:TEMP "nest_pack_build"
New-Item -ItemType Directory -Force $build | Out-Null
Copy-Item (Join-Path $root "nest_pack.py") (Join-Path $build "nest_pack.py") -Force
Push-Location $build
uv run --python 3.12 --with pyinstaller --with numpy --with pillow pyinstaller --onefile --name nest_pack --clean --noconfirm --log-level ERROR nest_pack.py
Pop-Location
Copy-Item (Join-Path $build "dist\nest_pack.exe") (Join-Path $root "nest_pack.exe") -Force
"built " + (Get-Item (Join-Path $root "nest_pack.exe")).Length + " bytes"
# Regenerate the licence notices from the same package set that was just frozen into the exe.
uv run --python 3.12 --with pyinstaller --with numpy --with pillow (Join-Path $PSScriptRoot "make_notices.py") (Join-Path $root "THIRD-PARTY-NOTICES.txt")