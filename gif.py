#!/usr/bin/env python3
"""
Advanced GIF Maker (full rewrite)
Features:
 - Add images (file dialog) with correct Linux filters
 - Add folder (auto-detect images inside)
 - Drag & drop to add
 - Thumbnail browser for folder (click to add)
 - Reorder/remove images in sequence
 - Resize (keep aspect ratio toggle)
 - Text overlay (font fallback), color, position
 - Live preview of GIF
 - Export GIF and MP4 (with background music)
Dependencies: pillow, moviepy, tkinterdnd2-unoff (or tkinterdnd2)
"""

import os
import sys
import math
import threading
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
try:
    # prefer unoff fork on pip for linux
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:
    # fallback to plain Tk (drag-drop will not work)
    TkinterDnD = tk.Tk
    DND_FILES = None

# MoviePy 2.x import (works with moviepy 2.2.x)
try:
    from moviepy import ImageSequenceClip, AudioFileClip
except Exception:
    # for older moviepy versions fallback to editor import
    try:
        from moviepy.editor import ImageSequenceClip, AudioFileClip
    except Exception:
        ImageSequenceClip = None
        AudioFileClip = None


# Allowed image extensions
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

# Helper functions
def is_image_file(path):
    return os.path.splitext(path)[1].lower() in IMAGE_EXTS

def scan_folder_for_images(folder):
    images = []
    for root, dirs, files in os.walk(folder):
        for f in sorted(files):
            if is_image_file(f):
                images.append(os.path.join(root, f))
        # Do not recurse into subfolders (change if you want recursion)
        break
    return images

def load_font(size):
    # Try common fonts; fallback to default PIL font
    possible = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "arial.ttf",
    ]
    for p in possible:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    # fallback
    from PIL import ImageFont as _IF
    return _IF.load_default()

class ThumbnailBrowser(tk.Frame):
    """A scrollable thumbnail grid showing images in a folder. Click to add."""
    def __init__(self, master, on_add_callback, thumb_size=100, cols=5, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_add = on_add_callback
        self.thumb_size = thumb_size
        self.cols = cols
        self.images = []  # file paths
        self.photo_refs = []  # keep PhotoImage refs

        # Scrollable canvas
        self.canvas = tk.Canvas(self, height=thumb_size*2 + 10)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def clear(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self.images = []
        self.photo_refs = []

    def load_folder(self, folder):
        self.clear()
        imgs = scan_folder_for_images(folder)
        self.images = imgs
        self.photo_refs = []
        r = 0; c = 0
        for idx, imgpath in enumerate(imgs):
            try:
                im = Image.open(imgpath)
                im.thumbnail((self.thumb_size, self.thumb_size))
                ph = ImageTk.PhotoImage(im)
            except Exception:
                # skip unreadable images
                continue
            self.photo_refs.append(ph)
            fr = tk.Frame(self.inner, bd=1, relief="flat")
            lbl = tk.Label(fr, image=ph)
            lbl.pack()
            lbl_text = tk.Label(fr, text=os.path.basename(imgpath), wraplength=self.thumb_size, justify="center", font=("Arial",8))
            lbl_text.pack()
            fr.grid(row=r, column=c, padx=4, pady=4)
            # bind click to add image to sequence
            lbl.bind("<Button-1>", lambda e, p=imgpath: self.on_add(p))
            lbl_text.bind("<Button-1>", lambda e, p=imgpath: self.on_add(p))
            c += 1
            if c >= self.cols:
                c = 0
                r += 1

class SequenceList(tk.Frame):
    """Listbox-like widget showing ordered sequence with thumbnails and controls."""
    def __init__(self, master, thumb_size=64, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.thumb_size = thumb_size
        self.items = []  # list of filepaths
        self.photo_refs = []

        toolbar = tk.Frame(self)
        toolbar.pack(fill="x", pady=(0,4))
        tk.Button(toolbar, text="Up", command=self.move_up).pack(side="left", padx=2)
        tk.Button(toolbar, text="Down", command=self.move_down).pack(side="left", padx=2)
        tk.Button(toolbar, text="Remove", command=self.remove_selected).pack(side="left", padx=2)
        tk.Button(toolbar, text="Clear", command=self.clear).pack(side="left", padx=2)

        # canvas to host items
        self.canvas = tk.Canvas(self, height=200)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.selected_index = None

    def add(self, path):
        if not os.path.isfile(path) or not is_image_file(path):
            return
        self.items.append(path)
        self._refresh()

    def add_many(self, paths):
        for p in paths:
            self.add(p)

    def _refresh(self):
        # clear
        for w in self.inner.winfo_children():
            w.destroy()
        self.photo_refs = []
        for i, p in enumerate(self.items):
            frame = tk.Frame(self.inner, bd=1, relief="solid")
            frame.pack(fill="x", padx=2, pady=2)
            try:
                im = Image.open(p)
                im.thumbnail((self.thumb_size, self.thumb_size))
                ph = ImageTk.PhotoImage(im)
            except Exception:
                ph = None
            lbl_img = tk.Label(frame, image=ph)
            lbl_img.image = ph
            if ph:
                self.photo_refs.append(ph)
            lbl_img.pack(side="left")
            txt = tk.Label(frame, text=os.path.basename(p), anchor="w")
            txt.pack(side="left", fill="x", expand=True)
            frame.bind("<Button-1>", lambda e, idx=i: self._on_select(idx))
            lbl_img.bind("<Button-1>", lambda e, idx=i: self._on_select(idx))
            txt.bind("<Button-1>", lambda e, idx=i: self._on_select(idx))
            if i == self.selected_index:
                frame.configure(bg="#cde")

    def _on_select(self, idx):
        self.selected_index = idx
        self._refresh()

    def move_up(self):
        idx = self.selected_index
        if idx is None or idx <= 0:
            return
        self.items[idx-1], self.items[idx] = self.items[idx], self.items[idx-1]
        self.selected_index = idx-1
        self._refresh()

    def move_down(self):
        idx = self.selected_index
        if idx is None or idx >= len(self.items)-1:
            return
        self.items[idx+1], self.items[idx] = self.items[idx], self.items[idx+1]
        self.selected_index = idx+1
        self._refresh()

    def remove_selected(self):
        idx = self.selected_index
        if idx is None:
            return
        del self.items[idx]
        self.selected_index = None
        self._refresh()

    def clear(self):
        self.items = []
        self.selected_index = None
        self._refresh()

    def get_sequence(self):
        return list(self.items)


class AdvancedGifApp:
    def __init__(self, root):
        self.root = root
        root.title("Advanced GIF Maker")
        root.geometry("1000x720")

        # Main Paned window
        paned = tk.PanedWindow(root, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # LEFT: browser & controls
        left = tk.Frame(paned, width=340)
        paned.add(left)

        btn_frame = tk.Frame(left)
        btn_frame.pack(fill="x", pady=6)
        tk.Button(btn_frame, text="Add Images...", command=self.add_images).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Add Folder...", command=self.add_folder).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Add Selected from Thumbs", command=self.add_selected_from_thumbs).pack(side="left", padx=4)

        # Thumbnail browser
        tk.Label(left, text="Folder Thumbnails:").pack(anchor="w", padx=6)
        self.thumb_browser = ThumbnailBrowser(left, on_add_callback=self._thumb_click, thumb_size=100, cols=3)
        self.thumb_browser.pack(fill="both", expand=False, padx=6, pady=4)

        # Sequence list
        tk.Label(left, text="Sequence (frames):").pack(anchor="w", padx=6, pady=(6,0))
        self.seq_list = SequenceList(left, thumb_size=64)
        self.seq_list.pack(fill="both", expand=True, padx=6, pady=4)

        # RIGHT: preview and options
        right = tk.Frame(paned)
        paned.add(right)

        # Options Frame
        opts = tk.LabelFrame(right, text="Export & Frame Options")
        opts.pack(fill="x", padx=6, pady=6)

        tk.Label(opts, text="Frame duration (ms):").grid(row=0, column=0, sticky="w")
        self.duration_var = tk.StringVar(value="150")
        tk.Entry(opts, textvariable=self.duration_var, width=8).grid(row=0, column=1, sticky="w", padx=4)

        tk.Label(opts, text="Resize (W x H, 0 keep original):").grid(row=1, column=0, sticky="w")
        self.resize_w = tk.StringVar(value="0")
        self.resize_h = tk.StringVar(value="0")
        tk.Entry(opts, textvariable=self.resize_w, width=6).grid(row=1, column=1, sticky="w", padx=2)
        tk.Entry(opts, textvariable=self.resize_h, width=6).grid(row=1, column=2, sticky="w", padx=2)
        self.keep_aspect = tk.BooleanVar(value=True)
        tk.Checkbutton(opts, text="Keep aspect ratio", variable=self.keep_aspect).grid(row=1, column=3, sticky="w", padx=4)

        # Overlay controls
        ov = tk.LabelFrame(right, text="Text Overlay")
        ov.pack(fill="x", padx=6, pady=6)
        tk.Label(ov, text="Text:").grid(row=0, column=0, sticky="w")
        self.text_entry = tk.Entry(ov, width=30)
        self.text_entry.grid(row=0, column=1, columnspan=2, sticky="w")

        tk.Label(ov, text="Size:").grid(row=1, column=0, sticky="w")
        self.text_size = tk.StringVar(value="30")
        tk.Entry(ov, textvariable=self.text_size, width=6).grid(row=1, column=1, sticky="w")

        tk.Label(ov, text="Position:").grid(row=1, column=2, sticky="w")
        self.pos_var = tk.StringVar(value="top-left")
        tk.OptionMenu(ov, self.pos_var, "top-left", "top-right", "bottom-left", "bottom-right", "center").grid(row=1, column=3, sticky="w")

        tk.Button(ov, text="Pick Color", command=self.pick_color).grid(row=2, column=0, pady=4)
        self.text_color_label = tk.Label(ov, text="      ", bg="#FFFFFF", relief="sunken")
        self.text_color_label.grid(row=2, column=1, sticky="w")
        self.text_color = "#FFFFFF"

        # Preview frame
        pr = tk.LabelFrame(right, text="GIF Preview")
        pr.pack(fill="both", expand=True, padx=6, pady=6)
        self.preview_canvas = tk.Label(pr)
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_frames = []
        self.preview_job = None

        btns = tk.Frame(right)
        btns.pack(fill="x", padx=6, pady=6)
        tk.Button(btns, text="Preview", command=self.preview_gif).pack(side="left", padx=4)
        tk.Button(btns, text="Create GIF", command=self.create_gif).pack(side="left", padx=4)
        tk.Button(btns, text="Create MP4 with Music", command=self.create_mp4).pack(side="left", padx=4)

        # Drag & drop registration (if supported)
        try:
            if DND_FILES:
                # root must be instance of TkinterDnD.Tk for drag-drop in many installs
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind("<<Drop>>", self._on_root_drop)
        except Exception:
            pass

    # ---------- UI actions ----------
    def add_images(self):
        files = filedialog.askopenfilenames(
            title="Select image files",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                ("All files", "*.*")
            ]
        )
        for f in files:
            if os.path.isfile(f):
                self.seq_list.add(f)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing images")
        if not folder:
            return
        imgs = scan_folder_for_images(folder)
        if not imgs:
            messagebox.showinfo("No images", "No supported images found in folder.")
            return
        # load thumbnails in browser and preselect them
        self.thumb_browser.load_folder(folder)
        # Optionally auto-add all
        if messagebox.askyesno("Add all?", f"Found {len(imgs)} images. Add all to sequence?"):
            self.seq_list.add_many(imgs)

    def add_selected_from_thumbs(self):
        # add currently loaded folder images (all)
        if not self.thumb_browser.images:
            messagebox.showinfo("No thumbnails", "No thumbnails loaded. Use Add Folder first.")
            return
        # ask to add all or choose
        if messagebox.askyesno("Add all?", f"Add {len(self.thumb_browser.images)} images from current folder to sequence?"):
            self.seq_list.add_many(self.thumb_browser.images)

    def _thumb_click(self, filepath):
        # click on a thumbnail -> add single image
        self.seq_list.add(filepath)

    def pick_color(self):
        col = colorchooser.askcolor()[1]
        if col:
            self.text_color = col
            self.text_color_label.configure(bg=col)

    def _on_root_drop(self, event):
        # event.data can contain a space-separated list of filenames wrapped in {}
        data = event.data
        files = []
        if data:
            # Split braces pattern: Tk may return "{/path/one} {/path/two}"
            parts = data.strip().split()
            cleaned = []
            tmp = ""
            for p in parts:
                if p.startswith("{") and not p.endswith("}"):
                    tmp = p.lstrip("{") + " "
                elif p.endswith("}") and tmp:
                    tmp += p.rstrip("}")
                    cleaned.append(tmp)
                    tmp = ""
                elif tmp:
                    tmp += p + " "
                else:
                    cleaned.append(p.strip("{}"))
            if tmp:
                cleaned.append(tmp.strip("{}"))
            files = [c for c in cleaned if os.path.exists(c)]
        # Add images / if folder add folder
        for f in files:
            if os.path.isdir(f):
                self.thumb_browser.load_folder(f)
            elif is_image_file(f):
                self.seq_list.add(f)

    # ---------- Preview ----------
    def preview_gif(self):
        seq = self.seq_list.get_sequence()
        if not seq:
            messagebox.showinfo("No frames", "Add images to the sequence first.")
            return
        # create frames (PIL) resized & overlayed
        try:
            duration_ms = int(self.duration_var.get())
        except Exception:
            duration_ms = 150
        frames = []
        for p in seq:
            try:
                im = Image.open(p).convert("RGBA")
            except Exception:
                continue
            im = self._process_frame_for_output(im)
            frames.append(im)
        if not frames:
            messagebox.showerror("Error", "No usable frames found.")
            return
        # create Tk PhotoImages for preview
        max_preview = 480
        thumbnails = []
        for im in frames:
            w, h = im.size
            scale = min(1.0, max_preview / max(w, h))
            sz = (int(w*scale), int(h*scale))
            ph = ImageTk.PhotoImage(im.resize(sz, Image.LANCZOS))
            thumbnails.append(ph)
        self.preview_frames = thumbnails
        # start animation
        self._stop_preview()
        self._start_preview(duration_ms)

    def _start_preview(self, duration_ms):
        if not self.preview_frames:
            return
        idx = 0
        def run():
            nonlocal idx
            if not self.preview_frames:
                return
            self.preview_canvas.config(image=self.preview_frames[idx])
            idx = (idx + 1) % len(self.preview_frames)
            self.preview_job = self.root.after(max(30, int(duration_ms)), run)
        run()

    def _stop_preview(self):
        if self.preview_job:
            try:
                self.root.after_cancel(self.preview_job)
            except Exception:
                pass
            self.preview_job = None

    # ---------- Frame processing ----------
    def _process_frame_for_output(self, pil_img):
        # apply resize & overlay
        w = int(self.resize_w.get()) if self.resize_w.get().isdigit() else 0
        h = int(self.resize_h.get()) if self.resize_h.get().isdigit() else 0
        img = pil_img.convert("RGBA")
        ow, oh = img.size
        if w > 0 or h > 0:
            if self.keep_aspect.get():
                # compute keeping aspect
                if w == 0:
                    scale = h / oh
                elif h == 0:
                    scale = w / ow
                else:
                    scale = min(w/ow, h/oh)
                nw = max(1, int(ow * scale))
                nh = max(1, int(oh * scale))
            else:
                nw = w if w>0 else ow
                nh = h if h>0 else oh
            img = img.resize((nw, nh), Image.LANCZOS)
        # text overlay
        txt = self.text_entry.get().strip()
        if txt:
            draw = ImageDraw.Draw(img)
            size = int(self.text_size.get()) if self.text_size.get().isdigit() else 30
            font = load_font(size)
            tw, th = draw.textsize(txt, font=font)
            pos = self.pos_var.get()
            margin = 10
            if pos == "top-left":
                xy = (margin, margin)
            elif pos == "top-right":
                xy = (img.size[0] - tw - margin, margin)
            elif pos == "bottom-left":
                xy = (margin, img.size[1] - th - margin)
            elif pos == "bottom-right":
                xy = (img.size[0] - tw - margin, img.size[1] - th - margin)
            else:
                xy = ((img.size[0]-tw)//2, (img.size[1]-th)//2)
            # draw shadow for readability
            shadow_color = "#000000"
            draw.text((xy[0]+1, xy[1]+1), txt, font=font, fill=shadow_color+( "FF" if isinstance(shadow_color, tuple) else "" ))
            draw.text(xy, txt, font=font, fill=self.text_color)
        return img.convert("RGBA")

    # ---------- Export GIF ----------
    def create_gif(self):
        seq = self.seq_list.get_sequence()
        if not seq:
            messagebox.showinfo("No frames", "Add some images first.")
            return
        try:
            duration_ms = int(self.duration_var.get())
        except Exception:
            duration_ms = 150
        save_path = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF", "*.gif")])
        if not save_path:
            return

        # Build frames (PIL) in a thread to avoid blocking UI
        def worker():
            frames = []
            for p in seq:
                try:
                    im = Image.open(p).convert("RGBA")
                except Exception:
                    continue
                im = self._process_frame_for_output(im)
                # convert to mode 'P' (palette) for smaller GIFs; Pillow handles quantization
                frames.append(im.convert('P', palette=Image.ADAPTIVE))
            if not frames:
                self.root.after(0, lambda: messagebox.showerror("Error", "No frames to save."))
                return
            # Save (first frame + append_images)
            try:
                frames[0].save(save_path, save_all=True, append_images=frames[1:], duration=duration_ms, loop=0, optimize=True)
                self.root.after(0, lambda: messagebox.showinfo("Saved", f"GIF saved to:\n{save_path}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Save error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Export MP4 with Music ----------
    def create_mp4(self):
        if ImageSequenceClip is None:
            messagebox.showerror("Missing", "MoviePy is not available or could not be imported.")
            return
        seq = self.seq_list.get_sequence()
        if not seq:
            messagebox.showinfo("No frames", "Add some images first.")
            return
        audio_file = filedialog.askopenfilename(title="Select background audio (optional)", filetypes=[("Audio", "*.mp3 *.wav *.ogg"), ("All files", "*.*")])
        save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
        if not save_path:
            return
        try:
            duration_ms = int(self.duration_var.get())
        except Exception:
            duration_ms = 150
        fps = max(1, int(1000 / duration_ms)) if duration_ms>0 else 10

        def worker():
            imgs = []
            for p in seq:
                try:
                    im = Image.open(p).convert("RGB")
                except Exception:
                    continue
                im = self._process_frame_for_output(im).convert("RGB")
                imgs.append(im)
            if not imgs:
                self.root.after(0, lambda: messagebox.showerror("Error", "No frames to save."))
                return
            # MoviePy expects filenames or numpy arrays; convert PIL to numpy arrays
            import numpy as _np
            arrays = [_np.array(im) for im in imgs]
            try:
                clip = ImageSequenceClip(arrays, fps=fps)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("MoviePy error", str(e)))
                return
            # Attach audio if provided
            if audio_file:
                try:
                    audio = AudioFileClip(audio_file)
                    clip = clip.set_audio(audio)
                except Exception as e:
                    # warn but continue
                    self.root.after(0, lambda: messagebox.showwarning("Audio warning", f"Could not load audio:\n{e}"))
            try:
                clip.write_videofile(save_path, codec="libx264", audio_codec="aac")
                self.root.after(0, lambda: messagebox.showinfo("Saved", f"MP4 saved to:\n{save_path}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Save error", str(e)))

        threading.Thread(target=worker, daemon=True).start()


def main():
    # Use TkinterDnD root if available to get drag-and-drop support
    try:
        root = TkinterDnD.Tk()
    except Exception:
        root = tk.Tk()
    app = AdvancedGifApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
