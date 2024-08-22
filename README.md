# Pyles
A very simple file manager written in Python that uses Qt6.

# Setup
On linux, make sure to `chmod +x` Pyles!
<br>On Windows, click '<ins>More Info</ins>' and then '**Run anyway**' if you get the "Windows protected your PC" popup!

<br>**Note**:
<br>I've recently tested on Linux Mint 22 and found that I can only open Pyles with a terminal window. A `.desktop` file has to launch with a terminal window too or else Pyles won't run!

**For those using the source code...** | _If you just want to run the program ignore this!_
<br><br>Here are the libraries you'll need to install:
<br>• `pip3 install PyQt6`
<br>• `pip3 install send2trash`
<br>• `pip3 install screeninfo`
<br>• `pip3 install pywin32` | _Only needed on Windows!_
<br>• `pip3 install py7zr`

Here are the build scripts I use:
<br>• Linux: `pyinstaller --onefile main.py`
<br>• Windows: `pyinstaller --onefile --noconsole main.py`
