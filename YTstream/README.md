# Py to Exe

### The PyInstaller Command

Run this in your `YTstream` directory:

```bash
pyinstaller --onefile --windowed --icon=YouTubeLiveStream.jpg YouTubeLiveStreamFolder.py

```

---

### Important Considerations for YouTube Streaming

Because these scripts often rely on external configuration files, keep these two points in mind:

* **Config Files:** Your `stream_config.json` and `config.env` must stay in the same folder as your new `.exe` (inside the `dist` folder) for the program to find your stream keys and settings.
* **The Icon Format:** As mentioned before, Windows is happiest with `.ico` files. If the icon doesn't show up on the `.exe` file in your File Explorer after building, you should convert `YouTubeLiveStream.jpg` to `YouTubeLiveStream.ico` and run the command again.

### How PyInstaller Bundles Your App

1. **Analysis:** It scans `YouTubeLiveStreamFolder.py` for all imported libraries (like `requests`, `opencv`, etc.).
2. **Collection:** It gathers all those library files into one temporary location.
3. **Bundling:** It compresses everything into a single `.exe` inside the **`dist`** folder.
4. **Execution:** When you run the `.exe`, it extracts itself into a temp folder, runs the script, and cleans up afterward.
