# build.py
import PyInstaller.__main__
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'app.py',  # Your main script file
    '--name=DirectoryStructureApp',
    '--onefile',
    '--windowed',
    '--clean',
    '--noconsole'
])