# Isaac Online Seed Fixer

A standalone memory patching utility for **The Binding of Isaac: Repentance** that forces custom seeds in online multiplayer lobbies without disconnecting players. Built as a companion tool for the *Offline2Online_Sync* Lua mod.

## 🚀 The Problem
Isaac's native netcode strictly prohibits custom seeds in online co-op. If `isSeededRun` is set to `true` (1), the lobby manager forcefully disconnects all peers. If it's forced to `false` (0) via memory patching, the game treats it as a standard run and forcefully overwrites the seed with a randomized one during `Game::Restart` and map generation.

## 🧠 The Solution (How it works)
This tool acts as an external memory injector using pure Python (`ctypes`). 
It performs the following tasks dynamically:
1. **ASLR Bypass**: Resolves the dynamic Base Address of `isaac-ng.exe` using `CreateToolhelp32Snapshot` to bypass Windows Address Space Layout Randomization (ASLR).
2. **Netcode Patch**: Patches the internal `ExecuteCommand` validation to push `0x00` instead of `0x01` into the `isSeededRun` flag, keeping the netcode alive.
3. **Trampoline Hooking**: Injects a custom Codecave (x86 Assembly) into the game's core RNG setter (`FUN_009eb880`).
4. **Seed Hijacking**: When the user inputs a seed, the Hook intercepts `Game::Restart`'s initialization, saves the user's custom seed into a secret memory vault, and then automatically forces all subsequent Lobby Manager randomizers to use the saved seed instead of random ones.

## 📥 Usage (For Players)
1. Launch *The Binding of Isaac: Repentance* and create your Online Lobby.
2. Run `IsaacOnlineSeedFixer_EN.exe`.
3. Press **F1** to enable the memory hook (you will hear a beep).
4. Apply your seed in-game (e.g., via the *Offline2Online_Sync* mod by pressing F8).
5. Once the run starts and the map is fully loaded, press **F2** to detach the hook and restore normal game behavior.

## 🛠️ Build Instructions (For Developers)
The script relies entirely on the Python Standard Library. No external dependencies (like `pywin32` or `pymem`) are required!

1. Install Python 3.10+
2. Install PyInstaller:
   ```cmd
   pip install pyinstaller
   ```
3. Compile the executable:
   ```cmd
   python -m PyInstaller --onefile fixer.py
   ```
4. The standalone `.exe` will be generated inside the `dist/` folder.

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
