# Py file to Exe

Since your logo `IGTV.jpg` is a JPEG, you should ideally convert it to an `.ico` file for the best compatibility with Windows taskbars and file explorers. However, PyInstaller can often handle standard image formats if the necessary modules (like Pillow) are installed in your environment.

### The Modified Command

Run this command in your terminal:

```bash
pyinstaller --onefile --windowed --icon=IGTV.jpg InstagramLiveStreamFolder.py

```

---

### Key Details for Success

* **`--windowed` (or `-w`):** Use this if your script has a GUI (like a Tkinter or PyQt window). This prevents a black command prompt (console) from popping up when you run the `.exe`. If your script is strictly a command-line tool, you can omit this.
* **File Format:** While PyInstaller is smart, Windows natively prefers `.ico` files for icons. If the icon doesn't show up correctly, try converting `IGTV.jpg` to `IGTV.ico` using an online converter and update the command to `--icon=IGTV.ico`.
* **The "Dist" Folder:** Once the process finishes, your new executable will be located in a newly created folder named **`dist`** within your current directory.

### Troubleshooting

If you run the `.exe` and it fails because it "cannot find" `config.env` or `ig_stream_config.json`, it’s because `--onefile` doesn't automatically pack your external config files into the executable—it only packs Python dependencies. You have two options:

1. **Manual:** Keep the `.exe` in the same folder as your `.env` and `.json` files.
2. **Embedded:** Add `--add-data "config.env;."` to your command to bake the config file inside the exe (though this makes them harder to edit later).
