from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFrame, QScrollArea, QHBoxLayout, QLineEdit, QCheckBox, QMenu, QInputDialog, QErrorMessage, QMessageBox, QLabel, QStyle
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from functools import partial
import os, sys, shutil, subprocess, random, send2trash, json, screeninfo

__start__ = False

files = []
hfiles = []
path=""
pinned = []
pins = []
tabs = {}
ids = [""]
tab = None
smode = 0 # search cur dir
ssort = 1 # alphabetical sort
s = "/" if sys.platform != "win32" else "\\"
home = f"{s}home" if sys.platform != "win32" else f"C:{s}Users"
root = f"{s}" if sys.platform != "win32" else f"C:{s}"

user = os.getlogin()
program_path = f"{home}{s}{user}"
# program_path = f"{home}{s}{user}{s}Documents{s}Python{s}Pyles" # Testing
try:
    os.mkdir(program_path+f"{s}.Pyles")
except:pass
if os.path.exists(program_path+f"{s}.Pyles{s}pins.json"):
    file_pins = open(program_path+f"{s}.Pyles{s}pins.json","r")
    try:
        __pinned__ = []
        for x in json.load(file_pins):
            if os.path.exists(x):
                __pinned__.append(x)
        pinned = __pinned__
    except Exception as e:
        print(e)
else:
    file_pins = open(program_path+f"{s}.Pyles{s}pins.json","w")
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
    if fp != "" and fp != root and (fp+s != root):
        if fp[-1] == f"{s}":
            fp = fp[:-1]
        p = fp[:fp[:-1].rfind(f"{s}")]
        if p == "": p = f"{s}"
        if p == root[:-1]: p = root
        n = fp[fp.rfind(f"{s}")+1:]
        if os.path.exists(fp) and os.path.exists(p):
            f = None
            for x in os.scandir(p):
                if x.name.lower() == n.lower():
                    f=x
            return f
    else:
        return root

def open_file_with_default_program(file_path):
    if sys.platform == "linux":
        if os.access(file_path, os.X_OK):
            subprocess.Popen(file_path)
        else:
            print("xdg-open " + file_path.path)
            myEnv = dict(os.environ)
            lp_key = 'LD_LIBRARY_PATH'
            lp_orig = myEnv.get(lp_key + '_ORIG')
            if lp_orig is not None:
                myEnv[lp_key] = lp_orig
            else:
                lp = myEnv.get(lp_key)
                if lp is not None:
                    myEnv.pop(lp_key)
            subprocess.call(["xdg-open", file_path.path], env=myEnv)
    elif sys.platform == "win32":
        os.startfile(file_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pyles")
        self.setGeometry(int(screeninfo.get_monitors()[0].width/2 - 400), int(screeninfo.get_monitors()[0].height/2 - 300), 800, 600)  # x, y, width, height

        # Create the main button
        self.button = QPushButton("Up to")
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
        self.new_file = QPushButton("New...")
        self.new_file.clicked.connect(self.add_file)
        self.new_file.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.new_file.customContextMenuRequested.connect(self.new_file_context)

        # Hidden Property
        self.hide_tog = QCheckBox("Show Hidden Files")
        self.hide_tog.clicked.connect(self.tog_hide)

        # Search Input
        self.search_inp = QLineEdit()
        self.search_inp.setPlaceholderText("Search here...")
        self.search_inp.returnPressed.connect(self.search)

        self.search_go = QPushButton("Go")
        self.search_go.clicked.connect(self.search)

        # Search Btn
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(partial(self.tog_el,(self.search_inp,self.search_go)))
        self.search_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_btn.customContextMenuRequested.connect(self.search_context)

        # Create a layout for properties
        self.prop_layout = QHBoxLayout()
        self.prop_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.prop_layout.addWidget(self.new_file)
        self.prop_layout.addWidget(self.search_btn)
        self.prop_layout.addWidget(self.hide_tog)


        # Search Layout
        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(self.search_inp)
        self.search_layout.addWidget(self.search_go)

        # New Tab
        self.new_tab = QPushButton("+ New Tab")
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

        # self.scroll_content.setStyleSheet("background-color: #14131C;")

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

        # self.pins_content.setStyleSheet("background-color: #14131C;")

        # Create a scroll area and set the scrollable content
        self.pins_area = QScrollArea()
        self.pins_area.setWidget(self.pins_content)
        self.pins_area.setWidgetResizable(True)

        # Create a main layout and add the button and the scroll area to it
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.button_layout)  # Add button layout
        main_layout.addLayout(self.prop_layout)  # Add prop layout
        main_layout.addLayout(self.search_layout) # Add search layout
        main_layout.addWidget(self.tab_scroll)  # Add tab layout
        main_layout.addLayout(self.content_layout)
        self.content_layout.addWidget(self.pins_area, 1)  # Add scroll area
        self.content_layout.addWidget(self.scroll_area, 4)  # Add scroll area

        # Create a central widget and set its layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.error_msg = QErrorMessage(self)

        self.working = QLabel("Working...")
        self.working.setFixedWidth(225)
        self.working.setFixedHeight(75)
        self.working.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _font = QFont(self.font())
        _font.setPointSize(30)
        self.working.setFont(_font)

        self.start()
    
    def start(self):
        global __start__
        if not __start__:
            __start__ = True
            self.add_tab()
            self.get_files()
            for x in pinned:
                if not get_file_from_str(x): continue
                self.pin_tab(x,True)
            self.search_inp.setVisible(False)
            self.search_go.setVisible(False)
    
    def tog_el(self,els:tuple):
        for el in els:
            try:
                el.setVisible(not el.isVisible())
            except:pass
    
    def goto(self):
        t = self.input.text()
        t = t.replace("~",f"{home}{s}{user}")
        f = get_file_from_str(t)
        self.open_file(f or t)

    def open_file(self, f):
        if f:
            if type(f) != str:
                if f.is_dir():
                    self.get_files(f.path)
                else:
                    open_file_with_default_program(f)
            else:
                if f.lower() != "trash":
                    self.get_files(root)
                else:
                    self.get_files(f)
        else:
            QMessageBox.warning(self,"Open Error",f"Invalid file/directory!")

    def get_files(self,_dir=f"~",fi=None):
        global user, path, files, hfiles, tab, tabs
        if _dir == "~":
            _dir = f"{home}{s}{user}"
        if _dir.lower() == "trash":
            if sys.platform == "linux":
                _dir = f"{home}{s}{user}{s}.local{s}share{s}Trash{s}files"
            else:
                QMessageBox.critical(self,"Pyles","Cannot view Recycle Bin in Windows at this time!",QMessageBox.StandardButton.Ok)
        path = _dir
        self.setWindowTitle(f"Pyles | {path}")
        tabs[tab][0] = path
        _path = path[:path.rfind(path.split(f"{s}")[-1])-1]
        _pathTxt = _path
        if _path == "": _pathTxt = f"{root}"
        self.button.setText(("Up to " + _pathTxt) if (_pathTxt != path and path != root) else "__hide__")
        if self.button.text() == "__hide__":
            self.button.hide()
        else:
            self.button.show()
        # self.button.setText(path + " >> " + (f"{s}" if _path == "" else _path))
        self.input.setText(path)
        if len(files) > 0:
            for x in files:
                self.scroll_layout.removeWidget(x)
                x.deleteLater()
        files = []
        hfiles = []
        if not fi:
            try:
                for f in os.scandir(_dir):
                    fButton = QPushButton(f.name + (f"{s}" if f.is_dir() else ""))
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
        else:
            for f in fi:
                fButton = QPushButton(f.name + (f"{s}" if f.is_dir() else ""))
                fButton.clicked.connect(partial(self.open_file, f))
                fButton.setStyleSheet("background-color: a();")
                fButton.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                fButton.customContextMenuRequested.connect(partial(self.file_context,f,fButton))
                self.scroll_layout.addWidget(fButton)
                if f.name[0] == ".":
                    fButton.hide()
                    hfiles.append(fButton)
                files.append(fButton)
        
        # Ensure layout updates are processed
        self.scroll_layout.update()

    def on_button_click(self):
        global path
        _path = path[:path.rfind(path.split(f"{s}")[-1])-1]
        if _path != root[:-1]:
            self.get_files(_path)
        else:
            self.get_files(f"{root}")

    def add_file(self,ty):
        global tab, tabs
        if not ty:
            msg = QMessageBox()
            msg.setWindowTitle("Create File")
            msg.setText("What would you like to create?")
            msg.setIcon(QMessageBox.Icon.Question)
            msg.addButton("File", QMessageBox.ButtonRole.ActionRole)
            msg.addButton("Folder", QMessageBox.ButtonRole.ActionRole)
            msg.setStandardButtons(QMessageBox.StandardButton.Cancel)
            msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
            x = msg.exec()
        else:
            x = ty
        if x != QMessageBox.StandardButton.Cancel:
            n, ok = QInputDialog.getText(self,"Create "+("Folder" if x == 3 else "File"),"Enter " + ("folder" if x == 3 else "file") + " name...")
            if n:
                if not os.path.exists(tabs[tab][0]+n):
                    # print(x,_folder)
                    if x == 2:
                        open(tabs[tab][0]+f"{s}"+n,"w").close()
                    elif x == 3:
                        # # print(tabs[tab][0]+f"{s}"+n)
                        os.mkdir(tabs[tab][0]+f"{s}"+n)
                self.get_files(tabs[tab][0])


    def search(self):
        global tab, tabs, smode
        query = self.search_inp.text().lower()
        ls = []
        if query and query != "":
            def b():
                global ssort
                nonlocal ls
                if ssort == 1:
                    ls.sort(key=lambda f: f.name)
                elif ssort == 2:
                    ls.sort(key=lambda f: f.name,reverse=True)
            if smode == 0:
                for f in os.scandir(tabs[tab][0]):
                    vis = False
                    n = f.name.lower()
                    if n == query:
                        vis = True
                    elif n.find(query) != -1:
                        vis = True
                    if vis == True:
                        ls.append(f)
                b()
                self.get_files(tabs[tab][0],ls)
            elif smode == 1:
                for ds,_,_ in os.walk(tabs[tab][0]):
                    d = "".join(ds)
                    for f in os.scandir(d):
                        if f.is_file():
                            vis = False
                            n = f.name.lower()
                            if n == query:
                                vis = True
                            elif n.find(query) != -1:
                                vis = True
                            if vis == True:
                                ls.append(f)
                b()
                self.get_files(tabs[tab][0],ls)
            elif smode == 2:
                def a():
                    nonlocal ls
                    for ds,_,_ in os.walk(f"{s}"):
                        d = "".join(ds)
                        for f in os.scandir(d):
                            try:
                                if f.is_file():
                                    vis = False
                                    n = f.name.lower()
                                    if n == query:
                                        vis = True
                                    elif n.find(query) != -1:
                                        vis = True
                                    if vis == True:
                                        ls.append(f)
                            except:pass
                    b()
                    self.get_files(tabs[tab][0],ls)
                    self.working.setVisible(False)
                self.working.setVisible(True)
                QTimer.singleShot(100, a)
        else:
            self.get_files(tabs[tab][0],[])
    
    def tog_hide(self):
        global hfiles
        val = self.hide_tog.checkState().value == 2
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
        tabs[tab] = [dir if dir else f"{home}{s}{user}",tabB]
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
            if n[-1] == f"{s}":
                n = n[:-1]
            n = n[n.rfind(f"{s}")+1:]
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

    def search_context(self,position):
        def setSMode(val):
            global smode
            smode = val
        def setSSort(val):
            global ssort
            ssort = val

        icon_check = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        menu = QMenu()
        tog = menu.addAction("Toggle Search")
        tog.triggered.connect(partial(self.tog_el,(self.search_inp,self.search_go)))
        if self.search_inp.isVisible():
           tog.setIcon(icon_check)
        #smode
        _smode = menu.addMenu("Search Mode")
        sdir = _smode.addAction("Search Current Directory")
        sdir.triggered.connect(partial(setSMode,0))
        srec = _smode.addAction("Search Current Directory Recursively")
        srec.triggered.connect(partial(setSMode,1))
        sall = _smode.addAction("Search All Files")
        sall.triggered.connect(partial(setSMode,2))
        #ssort
        _ssort = menu.addMenu("Sort Mode")
        sunsort = _ssort.addAction("Unsorted")
        sunsort.triggered.connect(partial(setSSort,0))
        salph = _ssort.addAction("Sort Alphabetically")
        salph.triggered.connect(partial(setSSort,1))
        sralph = _ssort.addAction("Sort Reverse Alphabetically")
        sralph.triggered.connect(partial(setSSort,2))
        # upd icons
        if smode == 0:
            sdir.setIcon(icon_check)
        elif smode == 1:
            srec.setIcon(icon_check)
        elif smode == 2:
            sall.setIcon(icon_check)

        if ssort == 0:
            sunsort.setIcon(icon_check)
        elif ssort == 1:
            salph.setIcon(icon_check)
        elif ssort == 2:
            sralph.setIcon(icon_check)

        #exec
        menu.exec(self.search_btn.mapToGlobal(position))

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
        if not get_file_from_str(dir): return
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
        if tabs[tab][0] == f"{home}{s}{user}{s}.local{s}share{s}Trash{s}files":
            etrash = menu.addAction("Empty Trash")
            etrash.triggered.connect(partial(self.delete_file,"EMPTY_TRASH"))
        if f.is_dir():
            opent = menu.addAction("Open in New Tab")
            opent.triggered.connect(partial(self.add_tab,f.path))
        else:
            opent = menu.addAction("Open File")
            opent.triggered.connect(partial(self.open_file,f))
        rename = menu.addAction("Rename to...")
        rename.triggered.connect(partial(self.move_file,f,f"Rename {f.name} to..."))
        if tabs[tab][0] != f"{home}{s}{user}{s}.local{s}share{s}Trash{s}files":
            trash = menu.addAction("Send to Trash")
            trash.triggered.connect(partial(self.trash_file,f))
        move = menu.addAction("Move to...")
        move.triggered.connect(partial(self.move_file,f))
        copy = menu.addAction("Copy to...")
        copy.triggered.connect(partial(self.copy_file,f))
        delete = menu.addAction("Delete")
        delete.triggered.connect(partial(self.delete_file,f))
        pin = menu.addAction(("Pin" if not f.path in pinned else "Unpin") + " " + ("Folder" if f.is_dir() else "File"))
        pin.triggered.connect(partial(self.pin_tab,f.path))
        menu.exec(btn.mapToGlobal(position))

    def new_file_context(self,position):
        menu = QMenu()
        nfile = menu.addAction("New File...")
        nfile.triggered.connect(partial(self.add_file,2))
        nfolder = menu.addAction("New Folder...")
        nfolder.triggered.connect(partial(self.add_file,3))
        menu.exec(self.new_file.mapToGlobal(position))

    def trash_file(self,f:os.DirEntry):
        if os.path.exists(f):
            send2trash.send2trash(f.path)
            self.get_files(tabs[tab][0])
    
    def delete_file(self,f:os.DirEntry):
        if type(f) != str and f != "EMPTY_TRASH":
            msg = QMessageBox()
            msg.setWindowTitle("Delete " + ("Folder" if f.is_dir() else "File"))
            msg.setText(f"Are you sure you want to delete {f.name}?")
            msg.setIcon(QMessageBox.Icon.Question)
            msg.addButton(QMessageBox.StandardButton.Yes)
            msg.addButton(QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            x = msg.exec()
            if x == QMessageBox.StandardButton.Yes:
                if os.path.exists(f):
                    if f.is_file():
                        try:
                            os.remove(f)
                        except Exception as e:
                            self.error_msg.showMessage(str(e))
                    else:
                        try:
                            os.rmdir(f)
                        except OSError as e:
                            if e.errno == 39 and tabs[tab][0] == f"{home}{s}{user}{s}.local{s}share{s}Trash{s}files":
                                try:
                                    shutil.rmtree(f.path)
                                except Exception as e:
                                    self.error_msg.showMessage(str(e))
                            else:
                                self.error_msg.showMessage(str(e))
                    self.get_files(tabs[tab][0])
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Empty Trash")
            msg.setText("Are you sure you want to empty the trash?\nYou won't be able to restore these files if you do.")
            msg.setIcon(QMessageBox.Icon.Question)
            msg.addButton(QMessageBox.StandardButton.Yes)
            msg.addButton(QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            x = msg.exec()
            if x == QMessageBox.StandardButton.Yes:
                for f in os.scandir(f"{home}{s}{user}{s}.local{s}share{s}Trash{s}files"):
                    if f.is_file():
                        os.remove(f)
                    else:
                        shutil.rmtree(f.path)
                self.get_files(tabs[tab][0])

    def move_file(self,f:os.DirEntry,prompt=None):
        if not prompt:
            prompt = f"Move {f.name} from {f.path[:-len(f.name)]} to..."
        global tab, tabs
        fp, ok = QInputDialog.getText(self, "Move " + "Folder" if f.is_dir() else "File", prompt)
        if fp[:2] == f".{s}":
            fp = tabs[tab][0]+s+fp[2:]
        if fp[:2] == f"~{s}":
            fp = home+s+user+s+fp[2:]
        if ok and fp:
            if fp[-1] == f"{s}": fp=fp[:-1]
            if not os.path.exists(fp+f"{s}"+f.name):
                # print(f"fp={fp}",fp.find(f"{s}"))
                if fp.find(f"{s}") != -1:
                    fn = fp[fp.rfind(f"{s}")+1:]
                    fpp = fp[:fp.rfind(f"{s}")]
                else:
                    fn = fp
                    fpp = ""
                if (not fpp or fpp == "") or ((fpp and fpp!="") and os.path.exists(fp)):
                    try:
                        if not fpp or fpp == "":
                            # print(f.path,f.path[:-(len(f.name))]+fn)
                            shutil.move(f.path,f.path[:-(len(f.name))]+fn)
                        else:
                            shutil.move(f.path,fp+f"{s}"+f.name)
                        self.get_files(tabs[tab][0])
                    except Exception as e:
                        self.error_msg.showMessage(str(e))
                else:
                    QMessageBox.warning(self,"Move Error",f"Destination's path {fpp} doesn't exist!")
            else:
                QMessageBox.warning(self,"Move Error",f"Destination {fp} already exists!")

    def copy_file(self,f:os.DirEntry):
        global tab, tabs
        fp, ok = QInputDialog.getText(self, "Copy " + ("Folder" if f.is_dir() else "File"), f"Copy {f.name} to...")
        if fp == ".": fp = f".{s}"
        if fp[:2] == f".{s}":
            fp = tabs[tab][0]+s+fp[2:]
        if fp[:2] == f"~{s}":
            fp = home+s+user+s+fp[2:]
        if ok and fp:
            if fp[-1] == f"{s}": fp=fp[:-1]
            if os.path.exists(fp+f"{s}"):
                # print(f"fp={fp}",fp.find(f"{s}"))
                if fp.find(f"{s}") != -1:
                    fn = fp[fp.rfind(f"{s}")+1:]
                    fpp = fp[:fp.rfind(f"{s}")]
                else:
                    fn = fp
                    fpp = ""
                if (not fpp or fpp == "") or ((fpp and fpp!="") and os.path.exists(fp)):
                    try:
                        if not fpp or fpp == "":
                            # print(f.path,f.path[:-(len(f.name))]+fn)
                            if f.is_file():
                                shutil.copyfile(f.path,f.path[:-(len(f.name))]+fn)
                            else:
                                shutil.copytree(f.path,f.path[:-(len(f.name))]+fn)
                        else:
                            name, ok = QInputDialog.getText(self, "Copy " + ("Folder" if f.is_dir() else "File"), f"Rename copied " + ("folder" if f.is_dir() else "file") + f" from {f.name} to...")
                            if not ok: return
                            if ok and not name or name == "": name = f.name
                            while os.path.exists(fp+f"{s}"+name):
                                name, ok = QInputDialog.getText(self, "Copy " + ("Folder" if f.is_dir() else "File"), f"Rename copied " + ("folder" if f.is_dir() else "file") + f" from {f.name} to...")
                                if ok and not name or name == "": name = f.name
                                if not ok: return
                            if f.is_file():
                                shutil.copyfile(f.path,fp+f"{s}"+name)
                            else:
                                shutil.copytree(f.path,fp+f"{s}"+name)
                        self.get_files(tabs[tab][0])
                    except Exception as e:
                        self.error_msg.showMessage(str(e))
                else:
                    QMessageBox.warning(self,"Copy Error",f"Destination's path {fpp} doesn't exist!")
                    print(fpp,fp)
            else:
                print(fp)
                print(fp+f"{s}"+f.name)
                QMessageBox.warning(self,"Copy Error",f"Destination {fp} doesn't exist!")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
    _pinned = open(program_path+f"{s}.Pyles{s}pins.json","w")
    json.dump(pinned,_pinned)
    _pinned.close()
