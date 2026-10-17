"""Entry point for the packaged offline desktop bridge.

PyInstaller builds this on Windows into silabs-humanizer-bridge.exe.
No model weights or network requests are included in this executable itself.
The model is supplied as a separate bundled resource by the installer.
"""
from products.humanizer.service.desktop_bridge import serve

if __name__ == "__main__":
    serve()
