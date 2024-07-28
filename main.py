from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFrame, QScrollArea, QHBoxLayout, QLineEdit, QCheckBox, QMenu, QInputDialog, QErrorMessage, QMessageBox
from PyQt6.QtCore import Qt
from functools import partial
import os, shutil, subprocess, random, send2trash, json

__start__ = False

files = []
hfiles = []
path=""
pinned = []
pins = []
tabs = {}
ids = [""]
tab = None

user = os.getlogin()
program_path = f"/home/{user}"
# program_path = f"/home/{user}/Documents/Python/Pyles" # Testing
try:
    os.mkdir(program_path+"/.Pyles")
except:pass
if os.path.exists(program_path+"/.Pyles/pins.json"):
    file_pins = open(program_path+"/.Pyles/pins.json","r")
    try:
        pinned = json.load(file_pins)
    except:pass
else:
    file_pins = open(program_path+"/.Pyles/pins.json","w")
file_pins.close()


def gen_uid():
    global ids
    id = ""
    while id in ids:
        id = ""
        for i in range(10):
            id+=str(random.randint(0,9))
    ids.append(id)
    return id

def get_file_from_str(fp):
    if fp[-1] == "/":
        fp = fp[:-1]
    p = fp[:fp[:-1].rfind("/")]
    if p == "": p = "/"
    n = fp[fp.rfind("/")+1:]
    if os.path.exists(fp) and os.path.exists(p):
        f = None
        for x in os.scandir(p):
            if x.name.lower() == n.lower():
                f=x
        return f

def open_file_with_default_program(file_path):
    if os.access(file_path, os.X_OK):
        subprocess.run(file_path)
    else:
        subprocess.run(["xdg-open", file_path])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pyles")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        # Create the main button
        self.button = QPushButton("^")
        self.button.clicked.connect(self.on_button_click)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter path here...")
        self.input.returnPressed.connect(self.goto)

        self.go = QPushButton("Go")
        self.go.clicked.connect(self.goto)

        # Create a layout for the button
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.button)
        self.button_layout.addWidget(self.input)
        self.button_layout.addWidget(self.go)

        # New File
        self.new_file = QPushButton("+ New File")
        self.new_file.clicked.connect(self.add_file)
        self.new_file.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.new_file.customContextMenuRequested.connect(self.new_file_context)

        # Hidden Property
        self.hideTog = QCheckBox("Show Hidden Files")
        self.hideTog.clicked.connect(self.togHide)

        # Create a layout for properties
        self.prop_layout = QHBoxLayout()
        self.prop_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.prop_layout.addWidget(self.new_file)
        self.prop_layout.addWidget(self.hideTog)

        # New Tab
        self.new_tab = QPushButton("+")
        self.new_tab.clicked.connect(self.add_tab)

        # Create a layout for tabs
        self.tab_layout = QHBoxLayout()
        self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.tab_layout.addWidget(self.new_tab)
        self.tab_content = QFrame()
        self.tab_content.setLayout(self.tab_layout)

        self.tab_scroll = QScrollArea()
        self.tab_scroll.setWidget(self.tab_content)
        self.tab_scroll.setWidgetResizable(True)
        self.tab_scroll.setMaximumHeight(60)

        # Create layout for pins+files
        self.content_layout = QHBoxLayout()

        # Create a layout for the scrollable content
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_content = QFrame()
        self.scroll_content.setLayout(self.scroll_layout)

        self.scroll_content.setStyleSheet("background-color: #14131C;")

        # Create a scroll area and set the scrollable content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setWidgetResizable(True)

        # Create a layout for the scrollable content
        self.pins_layout = QVBoxLayout()
        self.pins_layout.setSpacing(0)
        self.pins_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.pins_content = QFrame()
        self.pins_content.setLayout(self.pins_layout)

        self.pins_content.setStyleSheet("background-color: #14131C;")

        # Create a scroll area and set the scrollable content
        self.pins_area = QScrollArea()
        self.pins_area.setWidget(self.pins_content)
        self.pins_area.setWidgetResizable(True)

        # Create a main layout and add the button and the scroll area to it
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.button_layout)  # Add button layout
        main_layout.addLayout(self.prop_layout)  # Add prop layout
        main_layout.addWidget(self.tab_scroll)  # Add tab layout
        main_layout.addLayout(self.content_layout)
        self.content_layout.addWidget(self.pins_area, 1)  # Add scroll area
        self.content_layout.addWidget(self.scroll_area, 4)  # Add scroll area

        # Create a central widget and set its layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.error_msg = QErrorMessage(self)

        self.start()
    
    def start(self):
        global __start__
        if not __start__:
            self.add_tab()
            self.get_files()
            for x in pinned:
                self.pin_tab(x,True)
    
    def goto(self):
        t = self.input.text()
        if t[0] == "~":
            t = f"/{t}"
        t = t.replace("~",f"home/{user}")
        # print(t)
        f = get_file_from_str(t)
        self.open_file(f)

    def open_file(self, f):
        if f:
            if f.is_dir():
                # print(f"Opening {f.path}")
                self.get_files(f.path)
            else:
                open_file_with_default_program(f)
        else:
            QMessageBox.warning(self,"Open Error",f"Invalid file/directory!")

    def get_files(self,_dir=f"~"):
        global user, path, files, hfiles, tab, tabs
        if _dir == "~":
            _dir = f"/home/{user}"
        path = _dir
        self.setWindowTitle(f"Pyles | {path}")
        tabs[tab][0] = path
        _path = path[:path.rfind(path.split("/")[-1])-1]
        _pathTxt = _path
        if _path == "": _pathTxt = "/"
        self.button.setText(("Up to " + _pathTxt) if _pathTxt != path else "__hide__")
        if self.button.text() == "__hide__":
            self.button.hide()
        else:
            self.button.show()
        # self.button.setText(path + " >> " + ("/" if _path == "" else _path))
        self.input.setText(path)
        if len(files) > 0:
            for x in files:
                self.scroll_layout.removeWidget(x)
                x.deleteLater()
        files = []
        hfiles = []
        try:
            for f in os.scandir(_dir):
                fButton = QPushButton(f.name + ("/" if f.is_dir() else ""))
                fButton.clicked.connect(partial(self.open_file, f))
                fButton.setStyleSheet("background-color: a();")
                fButton.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                fButton.customContextMenuRequested.connect(partial(self.file_context,f,fButton))
                self.scroll_layout.addWidget(fButton)
                if f.name[0] == ".":
                    fButton.hide()
                    hfiles.append(fButton)
                files.append(fButton)
        except Exception as e:
            self.error_msg.showMessage(str(e))
        
        # Ensure layout updates are processed
        self.scroll_layout.update()

    def on_button_click(self):
        global path
        _path = path[:path.rfind(path.split("/")[-1])-1]
        if _path != "":
            self.get_files(_path)
        else:
            self.get_files("/")

    def add_file(self,ty):
        global tab, tabs
        if not ty:
            msg = QMessageBox()
            msg.setWindowTitle("Create File")
            msg.setText("What would you like to create?")
            msg.setIcon(QMessageBox.Icon.Question)
            msg.addButton("+ File", QMessageBox.ButtonRole.ActionRole)
            msg.addButton("+ Folder", QMessageBox.ButtonRole.ActionRole)
            msg.setStandardButtons(QMessageBox.StandardButton.Cancel)
            msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
            x = msg.exec()
        else:
            x = ty
        if x != QMessageBox.StandardButton.Cancel:
            n, ok = QInputDialog.getText(self,"Create File","Enter file name")
            if n:
                if not os.path.exists(tabs[tab][0]+n):
                    # print(x,_folder)
                    if x == 2:
                        open(tabs[tab][0]+"/"+n,"w").close()
                    elif x == 3:
                        # # print(tabs[tab][0]+"/"+n)
                        os.mkdir(tabs[tab][0]+"/"+n)
                self.get_files(tabs[tab][0])


    def togHide(self):
        global hfiles
        val = self.hideTog.checkState().value == 2
        for x in hfiles:
            if val:
                x.show()
            else:
                x.hide()

    def to_tab(self,_tab):
        global tab, tabs
        # print(_tab,tabs[_tab][0])
        tab = _tab
        tabs[tab][1].setText(f"[Tab {list(tabs.keys()).index(tab)+1}]")
        for i,y in tabs.items():
            if i != tab:
                y[1].setText(f"Tab {list(tabs.keys()).index(i)+1}")
        self.get_files(tabs[tab][0])

    def close_tab(self,_tab):
        global tab, tabs
        # print(f"Close tab {_tab}")
        if len(tabs.keys()) == 1: return
        if tab == _tab:
            tab = list(tabs.keys())[ list(tabs.keys()).index(tab) - 1 ]
        self.tab_layout.removeWidget(tabs[_tab][1])
        tabs[_tab][1].deleteLater()
        del tabs[_tab]
        self.to_tab(tab)

    def add_tab(self,dir=None):
        global tab, tabs
        ntab = len(tabs.keys())
        tab = gen_uid()
        tabB = QPushButton(f"Tab {ntab}")
        tabB.clicked.connect(partial(self.to_tab,tab))
        tabB.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tabB.customContextMenuRequested.connect(partial(self.tab_context,tab))
        tabs[tab] = [dir if dir else f"/home/{user}",tabB]
        self.tab_layout.addWidget(tabB)
        self.to_tab(tab)

    def pin_tab(self,_tab,force_pin=False):
        global pinned, pins, tabs
        if _tab in tabs:
            dir = tabs[_tab][0]
        else:
            dir = _tab

        if force_pin or not dir in pinned:
            if not dir in pinned:
                pinned.append(dir)
            n = dir
            if n[-1] == "/":
                n = n[:-1]
            n = n[n.rfind("/")+1:]
            pinB = QPushButton(n)
            pinB.clicked.connect(partial(self.open_file,get_file_from_str(dir)))
            pinB.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            pinB.customContextMenuRequested.connect(partial(self.pin_context,dir))
            self.pins_layout.addWidget(pinB)
            pins.append(pinB)
        elif dir in pinned:
            self.pins_layout.removeWidget(pins[pinned.index(dir)])
            pins[pinned.index(dir)].deleteLater()
            del pins[pinned.index(dir)]
            del pinned[pinned.index(dir)]


    def tab_context(self,_tab,position):
        global tabs, pinned
        # print(_tab,list(tabs.keys())[-1])
        menu = QMenu()
        close = menu.addAction("Close Tab")
        close.triggered.connect(partial(self.close_tab,_tab))
        pin = menu.addAction("Pin Folder" if not tabs[_tab][0] in pinned else "Unpin Folder")
        pin.triggered.connect(partial(self.pin_tab,_tab))
        menu.exec(tabs[_tab][1].mapToGlobal(position))

    def pin_context(self,dir,position):
        global pinned, pins
        menu = QMenu()
        if get_file_from_str(dir).is_dir():
            otab = menu.addAction("Open in new tab")
            otab.triggered.connect(partial(self.add_tab,dir))
        else:
            ofile = menu.addAction("Open file")
            ofile.triggered.connect(partial(self.open_file,get_file_from_str(dir)))
        unpin = menu.addAction("Unpin")
        unpin.triggered.connect(partial(self.pin_tab,dir))
        if dir in pinned:
            menu.exec(pins[pinned.index(dir)].mapToGlobal(position))

    def file_context(self,f:os.DirEntry,btn,position):
        global pinned
        menu = QMenu()
        delete = menu.addAction("Send to Trash")
        delete.triggered.connect(partial(self.delete_file,f))
        rename = menu.addAction("Rename")
        rename.triggered.connect(partial(self.move_file,f,f"Rename {f.name} to..."))
        move = menu.addAction("Move")
        move.triggered.connect(partial(self.move_file,f))
        pin = menu.addAction(("Pin" if not f.path in pinned else "Unpin") + " " + ("Folder" if f.is_dir() else "File"))
        pin.triggered.connect(partial(self.pin_tab,f.path))
        menu.exec(btn.mapToGlobal(position))

    def new_file_context(self,position):
        menu = QMenu()
        nfile = menu.addAction("+ New File")
        nfile.triggered.connect(partial(self.add_file,2))
        nfolder = menu.addAction("+ New Folder")
        nfolder.triggered.connect(partial(self.add_file,3))
        menu.exec(self.new_file.mapToGlobal(position))

    def delete_file(self,f:os.DirEntry):
        global tab, tabs
        if os.path.exists(f):
            send2trash.send2trash(f.path)
            self.get_files(tabs[tab][0])

    def move_file(self,f:os.DirEntry,prompt=None):
        if not prompt:
            prompt = f"Move {f.name} from {f.path[:-len(f.name)]} to..."
        global tab, tabs
        fp, ok = QInputDialog.getText(self, "Move " + "Folder" if f.is_dir() else "File", prompt)
        if ok and fp:
            if fp[-1]=="/": fp=fp[:-1]
            if not os.path.exists(fp+"/"+f.name):
                # print(f"fp={fp}",fp.find("/"))
                if fp.find("/") != -1:
                    fn = fp[fp.rfind("/")+1:]
                    fpp = fp[:fp.rfind("/")]
                else:
                    fn = fp
                    fpp = ""
                if (not fpp or fpp == "") or ((fpp and fpp!="") and os.path.exists(fp)):
                    try:
                        if not fpp or fpp == "":
                            # print(f.path,f.path[:-(len(f.name))]+fn)
                            shutil.move(f.path,f.path[:-(len(f.name))]+fn)
                        else:
                            shutil.move(f.path,fp+"/"+f.name)
                        self.get_files(tabs[tab][0])
                    except Exception as e:
                        self.error_msg.showMessage(str(e))
                else:
                    QMessageBox.warning(self,"Move Error",f"Destination's path {fpp} doesn't exist!")
            else:
                QMessageBox.warning(self,"Move Error",f"Destination {fp} already exists!")

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
    _pinned = open(program_path+"/.Pyles/pins.json","w")
    json.dump(pinned,_pinned)
    _pinned.close()
