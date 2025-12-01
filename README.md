# **ImageToGIF – Advanced GIF Maker (Python GUI)**

**ImageToGIF** is a powerful, feature-rich Python GUI application for creating animated GIFs and MP4 videos from images.
It supports drag-and-drop, folder scanning, text overlay, resizing, GIF preview, MP4 export with background music, and more.

This project is built using:

* **Tkinter** (GUI)
* **Pillow** (image processing)
* **MoviePy** (video/audio export)
* **tkinterdnd2** (drag-and-drop support)

---

## 🚀 **Features**

### ✅ **Image Input**

* Add individual images
* Add entire folders
* Drag & drop image files or folders
* Auto-detect supported image formats
* Thumbnail browser (click to add image)

### 🎞️ **Frame Management**

* Reorder frames (Up/Down)
* Remove selected frame
* Clear sequence
* Thumbnail preview of frames
* Scrollable list for large sequences

### 🖼️ **Preview**

* Live animated GIF preview
* Scaled preview for large GIFs
* Adjustable playback speed

### ✏️ **Text Overlay**

* Custom text
* Font size
* Position (top-left, top-right, bottom-left, bottom-right, center)
* Color picker
* Automatic shadow for readability

### 📐 **Resize Options**

* Set custom output width & height
* Optional “keep aspect ratio” toggle

### 🎵 **MP4 Output**

* Export MP4 with background music
* Uses **ffmpeg** via MoviePy

### 💾 **Export Formats**

* Animated **GIF**
* MP4 video with optional audio

---

## 📦 **Installation**

Clone the repo:

```bash
git clone https://github.com/Fanu2/ImageToGIF
cd ImageToGIF
```

Create a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

Install required packages:

```bash
pip install pillow moviepy tkinterdnd2-unoff
```

Install FFmpeg (required for MP4 export):

### Debian/Ubuntu/MX Linux:

```bash
sudo apt install ffmpeg
```

### Fedora:

```bash
sudo dnf install ffmpeg
```

### macOS (Homebrew):

```bash
brew install ffmpeg
```

### Windows:

Download from: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

---

## ▶️ **Run the Application**

```bash
python3 gif.py
```

---

## 🖼️ **Supported Image Formats**

* PNG
* JPG / JPEG
* BMP
* GIF
* WebP

---

## 🔧 **Technical Notes**

* MoviePy 2.x changed its import structure.
  The script automatically supports both MoviePy 1.x and 2.x.
* If `tkinterdnd2` is not available, the app still works (without drag-and-drop).
* GIF creation and MP4 rendering run in background threads to prevent UI freezing.

---

## 🛠️ **Project Structure**

```
ImageToGIF/
│
├── gif.py          # Main application
├── README.md       # Project documentation
└── (more files may be added later)
```

---

## 🤝 **Contributing**

Pull requests are welcome!
Feel free to submit issues for bugs, feature requests, or enhancements.

---

## 📜 **License**

This project is released under the **MIT License**.
You are free to use, modify, and distribute it.
