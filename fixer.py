import ctypes
import ctypes.wintypes
import time
import sys
import os
import subprocess
import struct

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
user32 = ctypes.WinDLL('user32', use_last_error=True)

PROCESS_ALL_ACCESS = 0x001F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_EXECUTE_READWRITE = 0x40

kernel32.VirtualAllocEx.restype = ctypes.c_void_p
kernel32.VirtualAllocEx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD]

class MODULEENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_uint32),
                ("th32ModuleID", ctypes.c_uint32),
                ("th32ProcessID", ctypes.c_uint32),
                ("GlblcntUsage", ctypes.c_uint32),
                ("ProccntUsage", ctypes.c_uint32),
                ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
                ("modBaseSize", ctypes.c_uint32),
                ("hModule", ctypes.c_void_p),
                ("szModule", ctypes.c_char * 256),
                ("szExePath", ctypes.c_char * 260)]

def get_process_info(process_name):
    try:
        output = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {process_name}" /NH /FO CSV', shell=True).decode()
        if process_name.lower() in output.lower():
            pid = int(output.split('","')[1].replace('"', ''))
            
            hSnapshot = kernel32.CreateToolhelp32Snapshot(0x00000008, pid)
            me32 = MODULEENTRY32()
            me32.dwSize = ctypes.sizeof(MODULEENTRY32)
            kernel32.Module32First(hSnapshot, ctypes.byref(me32))
            base_addr = ctypes.addressof(me32.modBaseAddr.contents)
            kernel32.CloseHandle(hSnapshot)
            
            return pid, base_addr
    except:
        pass
    return None, None

def patch_memory(hProcess, address, data):
    if isinstance(data, list):
        size = len(data)
        buffer = (ctypes.c_byte * size)(*data)
    else:
        size = len(data)
        buffer = (ctypes.c_byte * size).from_buffer_copy(data)
        
    old_protect = ctypes.wintypes.DWORD()
    kernel32.VirtualProtectEx(hProcess, ctypes.c_void_p(address), ctypes.c_size_t(size), ctypes.wintypes.DWORD(0x40), ctypes.byref(old_protect))
    
    bytes_written = ctypes.c_size_t(0)
    kernel32.WriteProcessMemory(hProcess, ctypes.c_void_p(address), buffer, ctypes.c_size_t(size), ctypes.byref(bytes_written))
    
    kernel32.VirtualProtectEx(hProcess, ctypes.c_void_p(address), ctypes.c_size_t(size), old_protect, ctypes.byref(old_protect))

def create_codecave(hProcess, base_addr):
    CC = kernel32.VirtualAllocEx(hProcess, None, 128, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
    if not CC: return None
        
    cc_addr = struct.pack("<I", CC)
    func_addr = base_addr + (0x009eb880 - 0x00400000)
    
    jump_back_offset = (func_addr + 5) - (CC + 0x2F + 5)
    jump_back_bytes = struct.pack("<i", jump_back_offset)

    addr_to_check = base_addr + (0x00958d6b - 0x00400000)
    addr_to_check_bytes = struct.pack("<I", addr_to_check)

    codecave_code = (
        b"\x00\x00\x00\x00" +                     # 00: Seed salvato
        b"\x81\x3C\x24" + addr_to_check_bytes +   # 04: CMP [ESP], Return address di Game::Restart
        b"\x75\x0B" +                             # 0B: JNE 18
        b"\x8B\x44\x24\x04" +                     # 0D: MOV EAX, [ESP+4]
        b"\xA3" + cc_addr +                       # 11: MOV [CC], EAX
        b"\xEB\x12" +                             # 16: JMP 2A
        b"\x83\x3D" + cc_addr + b"\x00" +         # 18: CMP DWORD PTR [CC], 0
        b"\x74\x09" +                             # 1F: JE 2A
        b"\xA1" + cc_addr +                       # 21: MOV EAX, [CC]
        b"\x89\x44\x24\x04" +                     # 26: MOV [ESP+4], EAX
        b"\x55" +                                 # 2A: PUSH EBP
        b"\x8B\xEC" +                             # 2B: MOV EBP, ESP
        b"\x53" +                                 # 2D: PUSH EBX
        b"\x56" +                                 # 2E: PUSH ESI
        b"\xE9" + jump_back_bytes                 # 2F: JMP back
    )
    
    patch_memory(hProcess, CC, codecave_code)
    return CC

def beep(freq, duration):
    kernel32.Beep(freq, duration)

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("==================================================")
    print(" Isaac Online Seed Fixer - ABSOLUTE EDITION")
    print("==================================================")
    print("Waiting for isaac-ng.exe to start...")
    
    pid, base_addr = None, None
    while not pid:
        pid, base_addr = get_process_info("isaac-ng.exe")
        if not pid: time.sleep(1)
            
    print(f"\n[OK] Isaac found in memory! (PID: {pid})")
    print(f"[*] ASLR Base Address: {hex(base_addr)}")
    
    hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not hProcess:
        print("[ERROR] Unable to access game memory.")
        os.system("pause")
        sys.exit(1)

    print("[*] Generating Trampoline Hook...")
    CC = create_codecave(hProcess, base_addr)
    if not CC:
        sys.exit(1)
        
    func_addr = base_addr + (0x009eb880 - 0x00400000)
    hook_offset = (CC + 4) - (func_addr + 5)
    hook_bytes = b"\xE9" + struct.pack("<i", hook_offset)
    orig_bytes = b"\x55\x8B\xEC\x53\x56"
    
    addr_isSeededRun = base_addr + (0x0068f85c - 0x00400000)
    addr_jump1 = base_addr + (0x00958d45 - 0x00400000)
    addr_jump2 = base_addr + (0x00958d53 - 0x00400000)
    
    patch_seedcmd = [0x6A, 0x00]
    orig_seedcmd = [0x6A, 0x01]
    patch_nop2 = [0x90, 0x90]
    orig_jump1 = [0x74, 0x16]
    orig_jump2 = [0x75, 0x08]

    print("\n---------------- INSTRUCTIONS ----------------")
    print("[F1] ENABLE  (Press BEFORE injecting the seed online)")
    print("[F2] DISABLE (Press as soon as the map is fully loaded)")
    print("----------------------------------------------\n")
    print("Listening for F1 and F2 keys...\n")

    active = False
    f1_was_down = False
    f2_was_down = False

    while True:
        f1_is_down = (user32.GetAsyncKeyState(0x70) & 0x8000) != 0
        if f1_is_down and not f1_was_down:
            if not active:
                patch_memory(hProcess, addr_isSeededRun, patch_seedcmd)
                patch_memory(hProcess, addr_jump1, patch_nop2)
                patch_memory(hProcess, addr_jump2, patch_nop2)
                patch_memory(hProcess, CC, b"\x00\x00\x00\x00") 
                patch_memory(hProcess, func_addr, hook_bytes)  
                active = True
                print("[+] PATCH ENABLED! RNG Dominated. Apply your seed now!")
                beep(800, 200)
        f1_was_down = f1_is_down

        f2_is_down = (user32.GetAsyncKeyState(0x71) & 0x8000) != 0
        if f2_is_down and not f2_was_down:
            if active:
                patch_memory(hProcess, addr_isSeededRun, orig_seedcmd)
                patch_memory(hProcess, addr_jump1, orig_jump1)
                patch_memory(hProcess, addr_jump2, orig_jump2)
                patch_memory(hProcess, func_addr, orig_bytes) 
                active = False
                print("[-] PATCH DISABLED! Game restored to normal.")
                beep(400, 200)
        f2_was_down = f2_is_down
        
        exit_code = ctypes.wintypes.DWORD()
        kernel32.GetExitCodeProcess(hProcess, ctypes.byref(exit_code))
        if exit_code.value != 259:
            print("\nIsaac was closed. The Fixer will now exit.")
            break
            
        time.sleep(0.05)

if __name__ == '__main__':
    main()
