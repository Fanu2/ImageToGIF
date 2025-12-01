
# **ImageToGIF – Linux AppImage Build Guide**

This document explains how to build a **stand-alone AppImage** for the **ImageToGIF** Python application.
The final result is a **single executable file** (`ImageToGIF.AppImage`) that runs on almost any Linux distribution without requiring Python, virtualenvs, or external dependencies.

---

# 🚀 **Why an AppImage?**

✔ No installation required
✔ Bundles its own Python interpreter
✔ Works across most Linux distros (Ubuntu, Debian, MX, Arch, Fedora…)
✔ Portable: can run from USB or offline
✔ Double-click to launch GUI

---

# 📦 **Required Tools**

Before building the AppImage, install:

```bash
sudo apt update
sudo apt install ffmpeg patchelf fuse zsync
pip install pyinstaller
```

---

# 📁 **1. Prepare the Build Directory**

Create a folder for building:

```bash
mkdir ImageToGIF_Build
cd ImageToGIF_Build
```

Copy your main application file here:

```
ImageToGIF_Build/
   gif.py
```

---

# 🏗️ **2. Build the Python Binary With PyInstaller**

Run PyInstaller:

```bash
pyinstaller --noconfirm --clean \
  --name ImageToGIF \
  --onefile \
  --add-data "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:fonts" \
  --hidden-import moviepy \
  --hidden-import moviepy.editor \
  --hidden-import tkinterdnd2 \
  gif.py
```

This generates:

```
dist/ImageToGIF     <-- bundled binary
```

---

# 📂 **3. Create AppDir Structure**

```bash
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons
```

Copy the built binary:

```bash
cp dist/ImageToGIF AppDir/usr/bin/
```

---

# 🖼️ **4. Add Desktop Entry**

Create:

```
AppDir/usr/share/applications/ImageToGIF.desktop
```

Contents:

```ini
[Desktop Entry]
Type=Application
Name=ImageToGIF
Exec=ImageToGIF
Icon=ImageToGIF
Categories=Graphics;Video;Utility;
Terminal=false
```

---

# 🖌️ **5. Add Program Icon (optional)**

Place your icon file here:

```
AppDir/usr/share/icons/ImageToGIF.png
```

(Any size works, preferably 256×256.)

---

# 🔧 **6. Create AppRun Launcher**

Create:

```
AppDir/AppRun
```

Contents:

```bash
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/ImageToGIF" "$@"
```

Make executable:

```bash
chmod +x AppDir/AppRun
```

---

# 📥 **7. Download appimagetool**

```bash
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
```

---

# 🧪 **8. Build the AppImage**

```bash
./appimagetool-x86_64.AppImage AppDir ImageToGIF.AppImage
```

You will now have:

```
ImageToGIF.AppImage
```

---

# ▶️ **9. Run Your AppImage**

```bash
chmod +x ImageToGIF.AppImage
./ImageToGIF.AppImage
```

Or double-click in your file manager.

---

# 🎯 **Troubleshooting**

### **AppImage does not run**

Try executing:

```bash
./ImageToGIF.AppImage --appimage-extract
```

If it extracts without error, it's likely a missing system library (rare on Debian/MX).

---

# 📌 **Optional: Automated Build Scripts**

If you want:

* a **build_appimage.sh** script
* a **GitHub Actions workflow** to auto-build AppImages on every commit
* a **desktop installer (.deb)**
* an **AppImage with embedded icons + metadata**

Just ask and I will generate them.

---

# 📜 **License**

MIT License — you may modify, distribute, and include the AppImage format freely.
