import paramiko
import sshtunnel
print(f"Paramiko version: {paramiko.__version__}")
print(f"SSHTunnel version: {sshtunnel.__version__}")
try:
    from paramiko import DSSKey
    print("DSSKey est présent")
except ImportError:
    print("DSSKey est absent (Paramiko 3.x+)")