# Isaac Online Fixer & Cloud Sync
A standalone companion utility for **The Binding of Isaac: Repentance** that enables **6-Digit Cloud Syncing** and forces custom seeds in online multiplayer lobbies without disconnecting players. Built specifically for the *Offline2Online_Sync* Lua mod.
## 🚀 The Problems
1. **The Seed Problem:** Isaac's native netcode strictly prohibits custom seeds in online co-op. If `isSeededRun` is set to `true`, the lobby manager forcefully disconnects all peers. If forced to `false` via memory patching, the game overwrites the seed with a randomized one during map generation.
2. **The Cloud Problem:** Isaac's standard Lua engine restricts filesystem access and lacks native HTTP request capabilities, making it impossible to share run states seamlessly over the internet without manually sending `.dat` files to friends.
## 🧠 The Solution (How it works)
This tool acts as a local server and external memory injector using pure Python (`ctypes` and `urllib`). It constantly tails Isaac's `log.txt` to receive IPC (Inter-Process Communication) commands sent by the Lua mod via `Isaac.DebugString()`.
It performs the following tasks dynamically:
1. **Dual-Layer Cloud Sync:** When uploading a run, the Python script reads the local save file and POSTs it to a secure pastebin (`dpaste`). It then generates a **6-digit numeric PIN** and links the payload URL to a secondary Key-Value database. This allows players to download massive save files using just a 6-digit code in-game!
2. **ASLR Bypass**: Resolves the dynamic Base Address of `isaac-ng.exe` using `CreateToolhelp32Snapshot` to bypass Windows Address Space Layout Randomization.
3. **Trampoline Hooking**: Injects a custom Codecave (x86 Assembly) into the game's core RNG setter (`FUN_009eb880`).
4. **Seed Hijacking & Auto-Detach**: It intercepts `Game::Restart`, saves the user's custom seed into a secret memory vault, and forces all Lobby Manager randomizers to use it. Once the map is fully loaded, the script receives an IPC command from Lua to automatically detach the hook and restore normal game behavior.
## 📥 Usage (For Players)
You no longer need to interact with the Python console! Everything is controlled directly inside Isaac.
1. Launch *The Binding of Isaac: Repentance*.
2. Run `IsaacOnlineFixer_CloudSync.exe` in the background and keep it minimized.
3. Open the *Offline2Online_Sync* mod menu in-game by pressing **F5** (in the starting room).
4. Use the in-game keys to interact with the Fixer:
   * **F10** to Upload your run to the Cloud and get a 6-digit PIN.
   * **F4** to Download a friend's run by typing their 6-digit PIN.
   * **F9** to toggle the Memory Patch (Seed Fixer) before applying an online seed.
## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
[![Download Latest Release](https://img.shields.io/github/v/release/toesmax/IsaacOnlineSeedFixer-By-Offline2Online?label=DOWNLOAD%20LATEST%20RELEASE&style=for-the-badge&color=success)](https://github.com/toesmax/IsaacOnlineSeedFixer-By-Offline2Online/releases/latest)
