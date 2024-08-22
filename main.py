from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFrame, QScrollArea, QHBoxLayout, QLineEdit, QCheckBox, QMenu, QInputDialog, QErrorMessage, QMessageBox, QLabel, QStyle
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction
from functools import partial
import py7zr.py7zr
import os, sys, shutil, subprocess, random, send2trash, json, screeninfo, webbrowser, ctypes, zipfile, tarfile, py7zr, tempfile, pathlib

__version__ = "1.0.8pre-1"

if sys.platform == "win32":
    import win32com.client

pinned = []
pin_names = []
pins = []
s = "/" if sys.platform != "win32" else "\\"
home = f"{s}home" if sys.platform != "win32" else f"C:{s}Users"
root = f"{s}" if sys.platform != "win32" else f"C:{s}"
user = os.getlogin()
trash = f"{home}{s}{user}{s}.local{s}share{s}Trash{s}files" if sys.platform == "linux" else "trash" #f"{root}$Recycle.Bin"

myEnv = dict(os.environ)
lp_key = 'LD_LIBRARY_PATH'
lp_orig = myEnv.get(lp_key + '_ORIG')
if lp_orig is not None:
    myEnv[lp_key] = lp_orig
else:
    lp = myEnv.get(lp_key)
    if lp is not None:
        myEnv.pop(lp_key)

program_path = f"{home}{s}{user}"
pyles_path = f"{program_path}{s}.Pyles"
if not os.path.exists(pyles_path):
    os.mkdir(pyles_path)
__old_pins__ = None
if os.path.exists(f"{pyles_path}{s}pins.json"):
    with open(f"{pyles_path}{s}pins.json","r") as _f:
        f = json.load(_f)
        __old_pins__ = f
    send2trash.send2trash(f"{pyles_path}{s}pins.json")
if os.path.exists(f"{pyles_path}{s}conf.json"):
    config = open(f"{pyles_path}{s}conf.json","r")
    try:
        config_json = json.load(config)
        __pinned__ = []
        __pin_names__ = []
        for x,n in config_json["pinned"].items():
            if os.path.exists(x) or x == "trash":
                __pinned__.append(x)
                __pin_names__.append(n)
        pinned = __pinned__
        pin_names = __pin_names__
    except Exception as e:
        print(e)
else:
    config = open(f"{pyles_path}{s}conf.json","w")
    config.write(r'{"pinned":{},"siz":null,"pos":null}')
config.close()

if __old_pins__ and (not pinned or pinned == []):
    pinned = __old_pins__
    for i in range(len(pinned)):
        pin_names.append("")

def is_archive(x:str,d:bool=False):
    if get_file_from_str(x).is_dir(): return False if not d else (False,None)
    if py7zr.is_7zfile(x): return True if not d else (True,"7z")
    if tarfile.is_tarfile(x): return True if not d else (True,"tar")
    if zipfile.is_zipfile(x): return True if not d else (True,"zip")
    return False if not d else (False,None)

def get_tar_type(_dir:str):
    with open(_dir,"rb") as f:
        sig = f.read()
        if sig.startswith(b"\x1f\x8b"):
            return "gz"
        elif sig.startswith(b"BZ"):
            return "bz"
        elif sig.startswith(b"\xfd7zXZ"):
            return "xz"
        else:
            return ""

def sep_path(x:str,o:str):
    return x[len(o)+1:]

def save_conf(window):
    _pinned = open(f"{pyles_path}{s}conf.json","w")
    __pinned__ = {}
    for i,x in enumerate(pinned):
        __pinned__[x] = pin_names[i]

    data = {"pinned":__pinned__,"siz":[window.size().width(),window.size().height()],"pos":[window.pos().x(),window.pos().y()]}
    json.dump(data,_pinned)
    _pinned.close()

def gen_uid(ids):
    id = ""
    while id in ids:
        id = ""
        for i in range(10):
            id+=str(random.randint(0,9))
    # ids.append(id)
    return id

def get_file_from_str(fp):
    if fp == "trash": return "trash"
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
            subprocess.call(["xdg-open", file_path.path], env=myEnv)
    elif sys.platform == "win32":
        os.startfile(file_path)

class _f:
    def __init__(self, x):
        self._x = x
        self.name:str = x.Name
        self.path:str = x.Path
    def is_dir(self) -> bool:
        return self._x.IsFolder
    def is_file(self) -> bool:
        return not self._x.IsFolder

def betterWalk(path:str):
    r = []
    for ds,_,_ in os.walk(path):
        d = "".join(ds)
        for f in os.scandir(d):
            if f.is_file():
                r.append(f)
    return tuple(r)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pyles")
        pos = [screeninfo.get_monitors()[0].width/2,screeninfo.get_monitors()[0].height/2]
        siz = [800,600]
        pos[0] -= siz[0]/2
        pos[1] -= siz[1]/2
        with open(f"{pyles_path}{s}conf.json","r") as _f:
            f = json.load(_f)
            try:
                if f["pos"]: pos = f["pos"]
            except:pass
            try:
                if f["siz"]: siz = f["siz"]
            except:pass
        self.setGeometry(int(pos[0]), int(pos[1]), int(siz[0]), int(siz[1]))  # x, y, width, height

        self.tempdirs = {}

        self.sfiles = []

        self.files = []
        self.hfiles = []
        self.path = ""

        self.tabs = {}
        self.tab = None
        self.ids = [""]

        self.smode = 0
        self.ssort = 1

        self.back_dir = QPushButton("<<")
        self.back_dir.clicked.connect(self.back_one_dir)

        self.fwd_dir = QPushButton(">>")
        self.fwd_dir.clicked.connect(self.fwd_one_dir)

        self.up_dir = QPushButton("Up to")
        self.up_dir.clicked.connect(self.up_one_dir)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter path here...")
        self.input.returnPressed.connect(self.goto)

        self.go = QPushButton("Go")
        self.go.clicked.connect(self.goto)

        # Create a layout for the button
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.back_dir)
        self.button_layout.addWidget(self.fwd_dir)
        self.button_layout.addWidget(self.up_dir)
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
        self.search_btn.clicked.connect(self.tog_search)
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

        self.about_frame = QFrame()
        self.about_frame.setGeometry(int(screeninfo.get_monitors()[0].width/2 - 300), int(screeninfo.get_monitors()[0].height/2 - 200), 600, 400)
        self.about_frame.setWindowFlag(Qt.WindowType.Popup)

        about_title = QLabel("About Pyles")
        about_title.setFixedWidth(600)
        about_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _about_font = _font
        _about_font.setPointSize(20)
        about_title.setFont(_about_font)

        about_body = QLabel(f'Version: {__version__} ({sys.platform})<br>A simple file manager written in Python.<br>Gui made with Qt6 using PyQt6.<br>Made by Dat Bogie (<a href="https://github.com/DatBogie">GitHub</a>).')
        about_body.setTextFormat(Qt.TextFormat.RichText)
        def _link_to(event):
            if event.button() == Qt.MouseButton.LeftButton:
                if sys.platform == "linux":
                    subprocess.Popen(["xdg-open","https://github.com/DatBogie"],env=myEnv)
                else:
                    webbrowser.open("https://github.com/DatBogie")
        about_body.mousePressEvent = _link_to

        about_layout = QVBoxLayout()
        about_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        about_layout.addWidget(about_title)
        about_layout.addWidget(about_body)

        self.about_frame.setLayout(about_layout)

        menu_bar = self.menuBar()

        menu_file = QMenu("&File",self)
        menu_bar.addMenu(menu_file)

        new_menu = QMenu("&New...",self)
        menu_file.addMenu(new_menu)

        new_menu_file = QAction("New &File...",self)
        new_menu.addAction(new_menu_file)

        new_menu_folder = QAction("New F&older...",self)
        new_menu.addAction(new_menu_folder)

        new_menu_file.triggered.connect(partial(self.add_file,2))
        new_menu_folder.triggered.connect(partial(self.add_file,3))

        menu_file.addSeparator()

        new_window_action = QAction("New &Window",self)
        menu_file.addAction(new_window_action)

        new_window_action.triggered.connect(self.new_window)

        menu_file.addSeparator()

        exit_action = QAction("E&xit",self)
        menu_file.addAction(exit_action)

        exit_action.triggered.connect(self.close)

        menu_edit = QMenu("&Edit",self)
        menu_bar.addMenu(menu_edit)

        refresh_action = QAction("&Refresh",self)
        refresh_action.triggered.connect(self.refresh)
        menu_edit.addAction(refresh_action)

        search_action = QAction("&Search",self)
        search_action.triggered.connect(self.show_search)
        menu_edit.addAction(search_action)

        if os.path.exists(f"{home}{s}{user}{s}.Pyles{s}conf.json"):
            edit_conf = QAction("Open &Preferences",self)
            edit_conf.triggered.connect(partial(self.open_file,get_file_from_str(f"{home}{s}{user}{s}.Pyles{s}conf.json")))
            menu_edit.addAction(edit_conf)

        save = QAction("S&ave Preferences",self)
        save.triggered.connect(partial(save_conf,self))
        menu_edit.addAction(save)

        menu_help = QMenu("&Help",self)
        menu_bar.addMenu(menu_help)

        about_action = QAction("&About",self)
        menu_help.addAction(about_action)
        about_action.triggered.connect(self.show_about)

        self.start()

    def start(self):
        self.add_tab()
        self.get_files()
        for i,x in enumerate(pinned):
            if not get_file_from_str(x): continue
            self.pin_tab(x,True,pin_names[i])
        self.search_inp.setVisible(False)
        self.search_go.setVisible(False)

    def fix_history(self):
        new = []
        for i,x in enumerate(self.tabs[self.tab][3]):
            if os.path.exists(x):
                new.append(x)
            else:
                if i <= self.tabs[self.tab][4]:
                    self.tabs[self.tab][4] -= 1
        if self.tabs[self.tab][4] < 0:
            self.tabs[self.tab][4] = 0
        elif self.tabs[self.tab][4] > len(self.tabs[self.tab][3])-1:
            self.tabs[self.tab][4] = len(self.tabs[self.tab][3])-1
        self.tabs[self.tab][4] = new
    
    def show_about(self):
        self.about_frame.setGeometry(int((self.pos().x() + (self.width()/2)) - 300), int((self.pos().y() + (self.height()/2)) - 200), 600, 400)
        self.tog_el((self.about_frame,),True)

    def show_search(self):
        self.tog_el((self.search_inp,self.search_go),True)
        self.search_inp.setFocus(Qt.FocusReason.MouseFocusReason)

    def new_window(self):
        MainWindow().show()

    def tog_el(self,els:tuple,val=-1):
        for el in els:
            try:
                if val != True and val != False:
                    el.setVisible(not el.isVisible())
                else:
                    el.setVisible(val)
            except:pass

    def goto(self):
        t = self.input.text()
        t = t.replace("~",f"{home}{s}{user}")
        f = get_file_from_str(t)
        self.open_file(f or t)

    def open_file(self, f):
        if f:
            if type(f) != str:
                if f.is_dir() or py7zr.is_7zfile(f.path) or tarfile.is_tarfile(f.path) or zipfile.is_zipfile(f.path):
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

    def open_with(self,f:os.DirEntry):
        if sys.platform == "linux":
            cmd, ok = QInputDialog.getText(self,"Open With","Enter program command/executable path...")
            if ok and cmd:
                try:
                    if cmd != "gtk-launch":
                        try:
                            subprocess.Popen([cmd,f.path],env=myEnv)
                        except Exception as e:
                            self.error_msg.showMessage(str(e))
                    else:
                        try:
                            subprocess.Popen([cmd,f.name.split(".desktop")[0]],env=myEnv)
                        except Exception as e:
                            self.error_msg.showMessage(str(e))
                except Exception as e:
                    self.error_msg.showMessage(str(e))
        else:
            subprocess.Popen(["openwith.exe",f.path],env=myEnv)
            # os.system(f'openwith.exe "{f.path}"')

    def get_files(self,_dir=f"~",fi=None,refresh:bool=False,save:bool=True):
        if not refresh: self.sfiles = []
        if fi == []: fi = None
        if _dir == "~":
            _dir = f"{home}{s}{user}"
        if _dir.lower() == "trash":
           _dir = trash
        if not os.path.exists(_dir):
            self.error_msg.showMessage(f"Path {_dir} does not exist.")
            return
        if save:
            if _dir != self.tabs[self.tab][0] and not _dir in self.tabs[self.tab][3]:
                self.tabs[self.tab][3].insert(self.tabs[self.tab][4]+1,_dir)
                self.tabs[self.tab][4] += 1
        if not (sys.platform == "win32" and _dir == trash):
            self.path = _dir
            self.setWindowTitle(f"Pyles | {self.path}")
            self.tabs[self.tab][0] = self.path
            _path = self.path[:self.path.rfind(self.path.split(f"{s}")[-1])-1]
            _pathTxt = _path
            if _path == "": _pathTxt = f"{root}"
            self.up_dir.setText(("Up to " + _pathTxt) if (_pathTxt != self.path and self.path != root) else "__hide__")
            if self.up_dir.text() == "__hide__":
                self.up_dir.hide()
            else:
                self.up_dir.show()
            # self.up_dir.setText(path + " >> " + (f"{s}" if _path == "" else _path))
            self.input.setText(self.path)
            if len(self.files) > 0:
                for x in self.files:
                    self.scroll_layout.removeWidget(x)
                    x.deleteLater()
            self.files = []
            self.hfiles = []
            if not fi and self.sfiles == []:
                is_7z = False
                is_tar = False
                is_zip = False
                if get_file_from_str(_dir).is_file():
                    is_7z = py7zr.is_7zfile(_dir)
                    is_tar = tarfile.is_tarfile(_dir)
                    is_zip = zipfile.is_zipfile(_dir)
                if not is_7z and not is_tar and not is_zip:
                    try:
                        for f in os.scandir(_dir):
                            fButton = QPushButton(f.name + (f"{s}" if f.is_dir() else ""))
                            fButton.clicked.connect(partial(self.open_file, f))
                            fButton.setStyleSheet("background-color: a();")
                            fButton.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                            fButton.customContextMenuRequested.connect(partial(self.file_context,f,fButton))
                            fButton.setToolTip(f.path)
                            self.scroll_layout.addWidget(fButton)
                            if (f.name[0] == "." and sys.platform == "linux") or (sys.platform == "win32" and (ctypes.windll.kernel32.GetFileAttributesW(f.path) & 0x2)):
                                fButton.hide()
                                self.hfiles.append(fButton)
                            self.files.append(fButton)
                    except Exception as e:
                        self.error_msg.showMessage(str(e))
                else:
                    if is_7z:
                        # 7z
                        if not _dir in self.tempdirs.keys():
                            tmpdir = tempfile.TemporaryDirectory()
                            self.tempdirs[_dir] = tmpdir
                            req_pass = False
                            with py7zr.SevenZipFile(_dir,"r") as archive:
                                req_pass = archive.password_protected
                            password = None
                            if req_pass:
                                password, ok = QInputDialog.getText(self, "Compress File", "Archive Password")
                                if not ok or password == "": password = None
                            with py7zr.SevenZipFile(_dir,"r",password=password) as archive:
                                archive.extractall(path=pathlib.Path(tmpdir.name))
                            self.get_files(tmpdir.name,save=False)
                        else:
                            tmpdir = self.tempdirs[_dir]
                            self.get_files(tmpdir.name,save=False)
                    elif is_tar:
                        # tar/targz/tarxz/tarbz2
                        if not _dir in self.tempdirs.keys():
                            tmpdir = tempfile.TemporaryDirectory()
                            self.tempdirs[_dir] = tmpdir
                            ty = get_tar_type(_dir)
                            with tarfile.TarFile(_dir,"r:"+ty) as archive:
                                archive.extractall(tmpdir.name)
                            self.get_files(tmpdir.name)
                        else:
                            tmpdir = self.tempdirs[_dir]
                            self.get_files(tmpdir.name)
                    else:
                        # zip
                        if not _dir in self.tempdirs.keys():
                            tmpdir = tempfile.TemporaryDirectory()
                            self.tempdirs[_dir] = tmpdir
                            with zipfile.ZipFile(_dir,"r") as archive:
                                archive.extractall(tmpdir.name)
                            self.get_files(tmpdir.name)
                        else:
                            tmpdir = self.tempdirs[_dir]
                            self.get_files(tmpdir.name)
            else:
                if not fi:
                    fi = self.sfiles
                else:
                    self.sfiles = fi
                _exists = 0
                for f in fi:
                    if os.path.exists(f.path):
                        fButton = QPushButton(f.name + (f"{s}" if f.is_dir() else ""))
                        fButton.clicked.connect(partial(self.open_file, f))
                        fButton.setStyleSheet("background-color: a();")
                        fButton.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                        fButton.customContextMenuRequested.connect(partial(self.file_context,f,fButton))
                        fButton.setToolTip(f.path)
                        self.scroll_layout.addWidget(fButton)
                        if (f.name[0] == "." and sys.platform == "linux") or (sys.platform == "win32" and (ctypes.windll.kernel32.GetFileAttributesW(f.path) & 0x2)):
                            fButton.hide()
                            self.hfiles.append(fButton)
                        self.files.append(fButton)
                    else: _exists += 1
                if _exists == len(fi): self.get_files(self.tabs[self.tab][0]);return
        else:
            shell = win32com.client.Dispatch("Shell.Application")
            recycle_bin = shell.Namespace(10)
            if recycle_bin:
                self.setWindowTitle(f"Pyles | {trash}")
                self.tabs[self.tab][0] = "trash"
                self.up_dir.setText("__hide__")
                self.up_dir.hide()
                self.input.setText("Trash")
                if len(self.files) > 0:
                    for x in self.files:
                        self.scroll_layout.removeWidget(x)
                        x.deleteLater()
                self.files = []
                self.hfiles = []
                if not fi and self.sfiles == []:
                    try:
                        for x in recycle_bin.Items():
                            f = _f(x)
                            fButton = QPushButton(f.name + (f"{s}" if f.is_dir() else ""))
                            fButton.clicked.connect(partial(self.open_file, f))
                            fButton.setStyleSheet("background-color: a();")
                            fButton.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                            fButton.customContextMenuRequested.connect(partial(self.file_context,f,fButton))
                            fButton.setToolTip(f.path)
                            self.scroll_layout.addWidget(fButton)
                            if (ctypes.windll.kernel32.GetFileAttributesW(f.path) & 0x2) and sys.platform == "win32":
                                fButton.hide()
                                self.hfiles.append(fButton)
                            self.files.append(fButton)
                    except Exception as e:
                        self.error_msg.showMessage(str(e))
                else:
                    if not fi:
                        fi = self.sfiles
                    else:
                        self.sfiles = fi
                    for f in fi:
                        fButton = QPushButton(f.name + (f"{s}" if f.is_dir() else ""))
                        fButton.clicked.connect(partial(self.open_file, f))
                        fButton.setStyleSheet("background-color: a();")
                        fButton.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                        fButton.customContextMenuRequested.connect(partial(self.file_context,f,fButton))
                        fButton.setToolTip(f.path)
                        self.scroll_layout.addWidget(fButton)
                        if (ctypes.windll.kernel32.GetFileAttributesW(f.path) & 0x2) and sys.platform == "win32":
                            fButton.hide()
                            self.hfiles.append(fButton)
                        self.files.append(fButton)
        # Ensure layout updates are processed
        self.scroll_layout.update()

    def refresh(self):
        self.get_files(self.tabs[self.tab][0],None,True)

    def back_one_dir(self):
        self.tabs[self.tab][4] -= 1
        if self.tabs[self.tab][4] < 0:
            self.tabs[self.tab][4] = 0
        if not os.path.exists(self.tabs[self.tab][3][self.tabs[self.tab][4]]):
            self.fix_history()
        self.tabs[self.tab][0] = self.tabs[self.tab][3][self.tabs[self.tab][4]]
        self.get_files(self.tabs[self.tab][0])
        print(self.tabs[self.tab][3],self.tabs[self.tab][4])

    def fwd_one_dir(self):
        self.tabs[self.tab][4] += 1
        if self.tabs[self.tab][4] > len(self.tabs[self.tab][3])-1:
            self.tabs[self.tab][4] = len(self.tabs[self.tab][3])-1
        if not os.path.exists(self.tabs[self.tab][3][self.tabs[self.tab][4]]):
            self.fix_history()
        self.tabs[self.tab][0] = self.tabs[self.tab][3][self.tabs[self.tab][4]]
        self.get_files(self.tabs[self.tab][0])
        print(self.tabs[self.tab][3],self.tabs[self.tab][4])

    def up_one_dir(self):
        _path = self.path[:self.path.rfind(self.path.split(f"{s}")[-1])-1]
        if _path != root[:-1]:
            self.get_files(_path)
        else:
            self.get_files(f"{root}")

    def extract_archive(self,file:os.DirEntry,ask_where:bool=False):
        v,ty = is_archive(file.path,True)
        if not v: self.error_msg.showMessage(f"File {file.path} is not an archive."); return
        dir = self.tabs[self.tab][0]
        if ask_where:
            _dir, ok = QInputDialog.getText(self,"Extract Archive","Where would you like to extract to?")
            if not ok: return
            if _dir[:2] == f"~{s}":
                _dir = f"{home}{s}{user}{s}{_dir[2:]}"
            elif _dir[:2] == f".{s}":
                _dir = f"{self.tabs[self.tab][0]}{s}{_dir[2:]}"
            if not os.path.exists(_dir): self.error_msg.showMessage(f"Path {_dir} does not exist."); return
            dir = _dir
        try:
            if ty == "7z":
                name = file.name
                if name[-3:] == ".7z": name = name[:-3] # .7z
                dir += s+name
                if not os.path.exists(dir):
                    os.mkdir(dir)
                else:
                    self.error_msg.showMessage(f"Path {dir} already exists."); return

                req_pass = False
                with py7zr.SevenZipFile(file.path,"r") as f:
                    req_pass = f.password_protected
                password = None
                if req_pass:
                    password, ok = QInputDialog.getText(self, "Extract Archive", "Archive Password")
                    if not ok: os.rmdir(dir); return
                    if password == "": password = None
                try:
                    with py7zr.SevenZipFile(file.path,"r",password=password) as f:
                        f.extractall(pathlib.Path(dir))
                except Exception as e:
                    os.remove(dir)
                    self.error_msg.showMessage(str(e))
                    return
            elif ty == "tar":
                name = file.name
                if name[-4:] == ".tar": name = name[:-4] # .tar
                if name[-8:] == ".tar.bz2": name = name[:-8] # .tar.bz2
                if name[-7:] == ".tar.gz": name = name[:-7] # .tar.gz
                if name[-7:] == ".tar.xz": name = name[:-7] # .tar.xz
                dir += s+name
                if not os.path.exists(dir):
                    os.mkdir(dir)
                else:
                    self.error_msg.showMessage(f"Path {dir} already exists."); return
                
                ty = get_tar_type(file.path)
                with tarfile.open(file.path,"r"+ty) as f:
                    f.extractall(dir)
            elif ty == "zip":
                name = file.name
                if name[-4:] == ".zip": name = name[:-4] # .zip
                dir += s+name
                if not os.path.exists(dir):
                    os.mkdir(dir)
                else:
                    self.error_msg.showMessage(f"Path {dir} already exists."); return
                
                with zipfile.ZipFile(file.path,"r") as f:
                    f.extractall(dir)
            self.refresh()
        except Exception as e:
            self.error_msg.showMessage(str(e))
        
    
    def add_file(self,ty):
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
                if not os.path.exists(self.tabs[self.tab][0]+n):
                    # print(x,_folder)
                    if x == 2:
                        open(self.tabs[self.tab][0]+f"{s}"+n,"w").close()
                    elif x == 3:
                        # # print(self.tabs[self.tab][0]+f"{s}"+n)
                        os.mkdir(self.tabs[self.tab][0]+f"{s}"+n)
                self.refresh()


    def search(self):
        query = self.search_inp.text().lower()
        ls = []
        if query and query != "":
            def b():
                nonlocal ls
                if self.ssort == 1:
                    ls.sort(key=lambda f: f.name)
                elif self.ssort == 2:
                    ls.sort(key=lambda f: f.name,reverse=True)
            if self.smode == 0:
                for f in os.scandir(self.tabs[self.tab][0]):
                    vis = False
                    n = f.name.lower()
                    if n == query:
                        vis = True
                    elif n.find(query) != -1:
                        vis = True
                    if vis == True:
                        ls.append(f)
                b()
                self.get_files(self.tabs[self.tab][0],ls)
            elif self.smode == 1:
                def a():
                    nonlocal ls
                    for ds,_,_ in os.walk(self.tabs[self.tab][0]):
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
                    self.get_files(self.tabs[self.tab][0],ls)
                    self.working.setVisible(False)
                self.working.setVisible(True)
                QTimer.singleShot(100,a)
            elif self.smode == 2:
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
                    self.get_files(self.tabs[self.tab][0],ls)
                    self.working.setVisible(False)
                self.working.setVisible(True)
                QTimer.singleShot(100, a)
        else:
            self.sfiles = []
            self.get_files(self.tabs[self.tab][0],[])

    def tog_hide(self):
        val = self.hide_tog.checkState().value == 2
        for x in self.hfiles:
            if val:
                x.show()
            else:
                x.hide()

    def to_tab(self,_tab):
        # print(_tab,self.tabs[_tab][0])
        self.tab = _tab
        self.tabs[self.tab][1].setText(f"[{self.tabs[_tab][2]}]" if self.tabs[_tab][2] else f"[Tab {list(self.tabs.keys()).index(self.tab)+1}]")
        for i,y in self.tabs.items():
            if i != self.tab:
                y[1].setText(y[2] if y[2] else f"Tab {list(self.tabs.keys()).index(i)+1}")
        self.get_files(self.tabs[self.tab][0])

    def close_tab(self,_tab):
        # print(f"Close tab {_tab}")
        if len(self.tabs.keys()) == 1: return
        if self.tab == _tab:
            self.tab = list(self.tabs.keys())[ list(self.tabs.keys()).index(self.tab) - 1 ]
        self.tab_layout.removeWidget(self.tabs[_tab][1])
        self.tabs[_tab][1].deleteLater()
        del self.tabs[_tab]
        self.to_tab(self.tab)

    def add_tab(self,dir=None):
        ntab = len(self.tabs.keys())
        self.tab = gen_uid(self.ids)
        self.ids.append(self.tab)
        tabB = QPushButton(f"Tab {ntab}")
        tabB.clicked.connect(partial(self.to_tab,self.tab))
        tabB.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tabB.customContextMenuRequested.connect(partial(self.tab_context,self.tab))
        self.tabs[self.tab] = [dir if dir else f"{home}{s}{user}",tabB,False,[f"{home}{s}{user}"],0]
        self.tab_layout.addWidget(tabB)
        self.to_tab(self.tab)

    def pin_tab(self,_tab,force_pin=False,name:str=""):
        global pinned, pins, pin_names
        if _tab in self.tabs:
            dir = self.tabs[_tab][0]
        else:
            dir = _tab

        if force_pin or not dir in pinned:
            if not dir in pinned:
                pinned.append(dir)
                pin_names.append(name)
            n = ""
            if name == "":
                n = dir
                if n[-1] == f"{s}":
                    n = n[:-1]
                n = n[n.rfind(f"{s}")+1:]
            else:
                n = name
            pinB = QPushButton(n)
            pinB.clicked.connect(partial(self.open_file,get_file_from_str(dir)))
            pinB.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            pinB.customContextMenuRequested.connect(partial(self.pin_context,dir))
            pinB.setToolTip(dir)
            self.pins_layout.addWidget(pinB)
            pins.append(pinB)
        elif dir in pinned:
            self.pins_layout.removeWidget(pins[pinned.index(dir)])
            pins[pinned.index(dir)].deleteLater()
            del pins[pinned.index(dir)]
            del pin_names[pinned.index(dir)]
            del pinned[pinned.index(dir)]

    def tog_search(self):
        if self.search_inp.isVisible():
            self.sfiles = []
        self.tog_el((self.search_inp,self.search_go),-1)

    def search_context(self,position):
        def setSMode(val):
            self.smode = val
        def setSSort(val):
            self.ssort = val

        icon_check = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        menu = QMenu()
        tog = menu.addAction("Toggle Search")
        tog.triggered.connect(self.tog_search)
        if self.search_inp.isVisible():
           tog.setIcon(icon_check)

        _smode = menu.addMenu("Search Mode")
        sdir = _smode.addAction("Search Current Directory")
        sdir.triggered.connect(partial(setSMode,0))
        srec = _smode.addAction("Search Current Directory Recursively")
        srec.triggered.connect(partial(setSMode,1))
        sall = _smode.addAction("Search All Files")
        sall.triggered.connect(partial(setSMode,2))

        _ssort = menu.addMenu("Sort Mode")
        sunsort = _ssort.addAction("Unsorted")
        sunsort.triggered.connect(partial(setSSort,0))
        salph = _ssort.addAction("Sort Alphabetically")
        salph.triggered.connect(partial(setSSort,1))
        sralph = _ssort.addAction("Sort Reverse Alphabetically")
        sralph.triggered.connect(partial(setSSort,2))
        # upd icons
        if self.smode == 0:
            sdir.setIcon(icon_check)
        elif self.smode == 1:
            srec.setIcon(icon_check)
        elif self.smode == 2:
            sall.setIcon(icon_check)

        if self.ssort == 0:
            sunsort.setIcon(icon_check)
        elif self.ssort == 1:
            salph.setIcon(icon_check)
        elif self.ssort == 2:
            sralph.setIcon(icon_check)

        #exec
        menu.exec(self.search_btn.mapToGlobal(position))

    def rename_tab(self,_tab):
        name, ok = QInputDialog.getText(self, "Rename Tab", "Enter name...")
        if ok and name and name != "":
            self.tabs[_tab][2] = name
            if self.tabs[self.tab] == self.tabs[_tab]:
                name = f"[{name}]"
            self.tabs[_tab][1].setText(name)

    def rename_pin(self,dir:str):
        global pin_names
        name, ok = QInputDialog.getText(self, "Rename Pin", "Enter name...")
        if ok and name and name != "":
            i = pinned.index(dir)
            pin_names[i] = name
            pins[i].setText(name)

    def tab_context(self,_tab,position):
        # print(_tab,list(tabs.keys())[-1])
        menu = QMenu()
        close = menu.addAction("Close Tab")
        close.triggered.connect(partial(self.close_tab,_tab))
        pin = menu.addAction("Pin Folder" if not self.tabs[_tab][0] in pinned else "Unpin Folder")
        pin.triggered.connect(partial(self.pin_tab,_tab))
        rename = menu.addAction("Rename Tab...")
        rename.triggered.connect(partial(self.rename_tab,_tab))
        menu.exec(self.tabs[_tab][1].mapToGlobal(position))

    def pin_context(self,dir,position):
        menu = QMenu()
        if not get_file_from_str(dir): return
        if dir == trash:
            etrash = menu.addAction("Empty trash")
            etrash.triggered.connect(partial(self.delete_file,"EMPTY_TRASH"))
        if dir == trash or get_file_from_str(dir).is_dir():
            otab = menu.addAction("Open in new tab")
            otab.triggered.connect(partial(self.add_tab,dir))
        else:
            ofile = menu.addAction("Open file")
            ofile.triggered.connect(partial(self.open_file,get_file_from_str(dir)))
        rename = menu.addAction("Rename pin...")
        rename.triggered.connect(partial(self.rename_pin,dir))
        unpin = menu.addAction("Unpin")
        unpin.triggered.connect(partial(self.pin_tab,dir))
        if dir in pinned:
            menu.exec(pins[pinned.index(dir)].mapToGlobal(position))

    def file_context(self,f:os.DirEntry,btn,position):
        menu = QMenu()
        print(self.tabs[self.tab][0])
        if self.tabs[self.tab][0] == trash:
            etrash = menu.addAction("Empty Trash")
            etrash.triggered.connect(partial(self.delete_file,"EMPTY_TRASH"))
        if f.is_dir() and not (self.tabs[self.tab][0] == trash and sys.platform == "win32"):
            opent = menu.addAction("Open in New Tab")
            opent.triggered.connect(partial(self.add_tab,f.path))
        elif not (self.tabs[self.tab][0] == trash and sys.platform == "win32"):
            opent = menu.addAction("Open File")
            opent.triggered.connect(partial(self.open_file,f))
        if not (self.tabs[self.tab][0] == trash and sys.platform == "win32"):
            openw = menu.addAction("Open with...")
            openw.triggered.connect(partial(self.open_with,f))
            rename = menu.addAction("Rename to...")
            rename.triggered.connect(partial(self.move_file,f,f"Rename {f.name} to..."))
        if self.tabs[self.tab][0] != trash:
            _trash = menu.addAction("Send to Trash")
            _trash.triggered.connect(partial(self.trash_file,f))
        if not (self.tabs[self.tab][0] == trash and sys.platform == "win32"):
            move = menu.addAction("Move to...")
            move.triggered.connect(partial(self.move_file,f))
            copy = menu.addAction("Copy to...")
            copy.triggered.connect(partial(self.copy_file,f))
        if is_archive(f.path):
            extracth = menu.addAction("Extract here")
            extracth.triggered.connect(partial(self.extract_archive,f))
            extract = menu.addAction("Extract to...")
            extract.triggered.connect(partial(self.extract_archive,f,True))
        compress = menu.addAction("Compress to...")
        if f.is_file():
            compress.triggered.connect(partial(self.make_archive,f))
        else:
            files = betterWalk(f.path)
            compress.triggered.connect(partial(self.make_archive,files))
        
        delete = menu.addAction("Delete")
        delete.triggered.connect(partial(self.delete_file,f))
        if not (self.tabs[self.tab][0] == trash and sys.platform == "win32"):
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

    def make_archive(self,files:os.DirEntry|tuple[os.DirEntry,...]):
        archive_types = [
            (py7zr.SevenZipFile,"7z",""),
            (tarfile.open,"tar",""),
            (tarfile.open,"tar.bz2",":bz2"),
            (tarfile.open,"tar.gz",":gz"),
            (tarfile.open,"tar.xz",":xz"),
            (zipfile.ZipFile,"zip","")
        ]
        ty = QMessageBox()
        ty.setWindowTitle("Compress File")
        ty.setText("What type of compression would you like to use?")
        ty.setIcon(QMessageBox.Icon.Question)
        ty.addButton("7Zip", QMessageBox.ButtonRole.ActionRole) # 2
        ty.addButton("Tar (uncompressed)", QMessageBox.ButtonRole.ActionRole) # 3
        ty.addButton("Tar BZip2 (bz2)", QMessageBox.ButtonRole.ActionRole) # 4
        ty.addButton("Tar GZip (gz)", QMessageBox.ButtonRole.ActionRole) # 5
        ty.addButton("Tar LZMA (xz)", QMessageBox.ButtonRole.ActionRole) # 6
        ty.addButton("Zip", QMessageBox.ButtonRole.ActionRole) # 7
        ty.setStandardButtons(QMessageBox.StandardButton.Cancel)
        ty.setDefaultButton(QMessageBox.StandardButton.Cancel)
        x = ty.exec()
        if x == QMessageBox.StandardButton.Cancel: return
        name, ok = QInputDialog.getText(self, "Compress File", "Archive Name (w/o file extension)")
        if not ok or not name or name == "": return
        try:
            _arch = archive_types[x-2]
            name = f"{self.tabs[self.tab][0]}{s}{name}.{_arch[1]}"
            if os.path.exists(name): raise FileExistsError(f"File already exists: {name}")
            def __add_file__(archive,x,file:os.DirEntry):
                if x-2 != 0 and x-2 != 5:
                    archive.add(file.path,arcname=sep_path(file.path,self.tabs[self.tab][0]))
                else:
                    archive.write(file.path,arcname=sep_path(file.path,self.tabs[self.tab][0]))
            archive = None
            if x-2 != 0:
                archive = _arch[0](name,"w"+_arch[2])
            else:
                password, ok = QInputDialog.getText(self, "Compress File", "Archive Password")
                if not ok: password = ""
                if password != "":
                    archive = _arch[0](name,"w"+_arch[2],password=password)
                else:
                    archive = _arch[0](name,"w"+_arch[2])
            if not archive: return
            if type(files) == os.DirEntry:
                __add_file__(archive,x,files)
            else:
                for f in files:
                    __add_file__(archive,x,f)
            archive.close()
            self.refresh()
        except Exception as e:
            self.error_msg.showMessage(str(e))
    
    def trash_file(self,f:os.DirEntry):
        if f.path in self.tempdirs.keys():
            self.tempdirs[f.path].cleanup()
        if os.path.exists(f.path):
            send2trash.send2trash(f.path)
            self.refresh()

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
                if f.path in self.tempdirs.keys():
                    self.tempdirs[f.path].cleanup()
                if os.path.exists(f.path):
                    if f.is_file():
                        try:
                            os.remove(f.path)
                        except Exception as e:
                            self.error_msg.showMessage(str(e))
                    else:
                        try:
                            os.rmdir(f)
                        except OSError as e:
                            if e.errno == 39: #and self.tabs[self.tab][0] == f"{home}{s}{user}{s}.local{s}share{s}Trash{s}files":
                                try:
                                    shutil.rmtree(f.path)
                                except Exception as e:
                                    self.error_msg.showMessage(str(e))
                            else:
                                self.error_msg.showMessage(str(e))
                    self.refresh()
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
                if sys.platform == "linux":
                    for f in os.scandir(trash):
                        if f.is_file():
                            os.remove(f.path)
                        else:
                            shutil.rmtree(f.path)
                else:
                    shell = win32com.client.Dispatch("Shell.Application")
                    recycle_bin = shell.Namespace(10)
                    if recycle_bin:
                        for x in recycle_bin.Items():
                            f = _f(x)
                            if f.is_file():
                                os.remove(f.path)
                            else:
                                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x00000001 | 0x00000002 | 0x00000004)
                self.refresh()

    def move_file(self,f:os.DirEntry,prompt=None):
        if not prompt:
            prompt = f"Move {f.name} from {f.path[:-len(f.name)]} to..."
        fp, ok = QInputDialog.getText(self, "Move " + "Folder" if f.is_dir() else "File", prompt)
        if fp[:2] == f".{s}":
            fp = self.tabs[self.tab][0]+s+fp[2:]
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
                        self.refresh()
                    except Exception as e:
                        self.error_msg.showMessage(str(e))
                else:
                    QMessageBox.warning(self,"Move Error",f"Destination's path {fpp} doesn't exist!")
            else:
                QMessageBox.warning(self,"Move Error",f"Destination {fp} already exists!")

    def copy_file(self,f:os.DirEntry):
        fp, ok = QInputDialog.getText(self, "Copy " + ("Folder" if f.is_dir() else "File"), f"Copy {f.name} to...")
        if fp == ".": fp = f".{s}"
        if fp[:2] == f".{s}":
            fp = self.tabs[self.tab][0]+s+fp[2:]
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
                        self.refresh()
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
    save_conf(window)
    for x in window.tempdirs.values():
        x.cleanup()
