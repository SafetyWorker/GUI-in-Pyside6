README - How to Install PySide6 and Run the App on Windows
====================================================

1. Install Python
-----------------
- Download Python from https://www.python.org/downloads/
- During installation, check "Add Python to PATH".
- Verify installation:
  python --version
  or
  py --version

2. Install PySide6
------------------
Open Command Prompt and run:
  pip install PySide6

If you have multiple Python versions, use:
  py -m pip install PySide6

Verify installation:
  pip show PySide6

3. Navigate to Your Project Folder
----------------------------------
Example:
  cd C:\Users\YourUsername\Python

4. Run Your PySide6 App
-----------------------
Use:
  py app.py
or
  python app.py

5. Troubleshooting
------------------
- If you see "pip not recognized", ensure Python is added to PATH or use:
    py -m ensurepip

- If you see "ModuleNotFoundError: No module named 'PySide6'", reinstall:
    py -m pip install --upgrade pip
    py -m pip install PySide6

- To check installed packages:
    pip list

Enjoy your PySide6 application!
