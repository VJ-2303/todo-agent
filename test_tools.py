import os

from tools import list_files, read_file, run_command, write_file

print("1. Testing write_file...")
print(write_file("sandbox/hello.txt", "Hello from Agent Tools!"))

print("\n2. Testing list_files...")
print(list_files("sandbox"))

print("\n3. Testing read_file...")
print(read_file("sandbox/hello.txt"))

print("\n4. Testing run_command...")
print(run_command("uname -a && python3 --version"))
