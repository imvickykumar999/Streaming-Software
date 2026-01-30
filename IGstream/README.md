## How to Create the EXE

Since your app has a custom UI and uses threading, follow these steps in your terminal:

1. **Install PyInstaller:**
```bash
pip install pyinstaller


```


2. **Build the File:**
Use the `--noconsole` (or `--windowed`) flag so that a black command prompt doesn't open behind your Instagram Streamer window.
```bash
pyinstaller --onefile IGTVGUI.py


```


3. **Result:**
Go to the `dist/` folder. Your `InstagramLiveStreamer.exe` will be there.

**Notes for this specific App:**

* **FFmpeg Requirement:** Your `.exe` still requires `ffmpeg` to be installed on the Windows system's PATH. If you plan to share this with others who don't have FFmpeg, you would need to bundle the `ffmpeg.exe` binary with the app using the `--add-data` flag.
* **Permissions:** Streaming apps sometimes trigger firewall warnings; make sure to allow access if prompted.
* **Icons:** If you have a `.ico` file, you can add it with `--icon=app_icon.ico`.
