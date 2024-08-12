from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFrame, QScrollArea, QHBoxLayout, QLineEdit, QCheckBox, QMenu, QInputDialog, QErrorMessage, QMessageBox, QLabel, QStyle, QMenuBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction
from functools import partial
import os, sys, shutil, subprocess, random, send2trash, json, screeninfo, webbrowser

pinned = []
pins = []
s = "/" if sys.platform != "win32" else "\\"
home = f"{s}home" if sys.platform != "win32" else f"C:{s}Users"
root = f"{s}" if sys.platform != "win32" else f"C:{s}"
user = os.getlogin()
trash = f"{home}{s}{user}{s}.local{s}share{s}Trash{s}files" if sys.platform == "linux" else f"{root}$Recycle.Bin"

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

def gen_uid(ids):
    id = ""
    while id in ids:
        id = ""
        for i in range(10):
            id+=str(random.randint(0,9))
    # ids.append(id)
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
            subprocess.call(["xdg-open", file_path.path], env=myEnv)
    elif sys.platform == "win32":
        os.startfile(file_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pyles")
        self.setGeometry(int(screeninfo.get_monitors()[0].width/2 - 400), int(screeninfo.get_monitors()[0].height/2 - 300), 800, 600)  # x, y, width, height

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
        self.search_btn.clicked.connect(partial(self.tog_el,(self.search_inp,self.search_go),-1))
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

        about_body = QLabel('Version: 1.0.5<br>A simple file manager written in Python.<br>Gui made with Qt6 using PyQt6.<br>Made by Dat Bogie (<a href="https://github.com/DatBogie">GitHub</a>).')
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

        search_action = QAction("&Search",self)
        menu_edit.addAction(search_action)
        
        search_action.triggered.connect(self.show_search)

        menu_help = QMenu("&Help",self)
        menu_bar.addMenu(menu_help)

        about_action = QAction("&About",self)
        menu_help.addAction(about_action)
        about_action.triggered.connect(self.show_about)

        self.start()
    
    def start(self):
        self.add_tab()
        self.get_files()
        for x in pinned:
            if not get_file_from_str(x): continue
            self.pin_tab(x,True)
        self.search_inp.setVisible(False)
        self.search_go.setVisible(False)
    
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

    def get_files(self,_dir=f"~",fi=None):
        if _dir == "~":
            _dir = f"{home}{s}{user}"
        if _dir.lower() == "trash":
           _dir = trash
        if _dir != self.tabs[self.tab][0] and not _dir in self.tabs[self.tab][3]:
            self.tabs[self.tab][3].insert(self.tabs[self.tab][4]+1,_dir)
            self.tabs[self.tab][4] += 1
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
                        self.hfiles.append(fButton)
                    self.files.append(fButton)
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
                    self.hfiles.append(fButton)
                self.files.append(fButton)
        
        # Ensure layout updates are processed
        self.scroll_layout.update()

    def back_one_dir(self):
        self.tabs[self.tab][4] -= 1
        if self.tabs[self.tab][4] < 0:
            self.tabs[self.tab][4] = 0
        else:
            self.tabs[self.tab][0] = self.tabs[self.tab][3][self.tabs[self.tab][4]]
            # del self.tabs[self.tab][3][self.tabs[self.tab][4]]
        self.get_files(self.tabs[self.tab][0])
        print(self.tabs[self.tab][3],self.tabs[self.tab][4])

    def fwd_one_dir(self):
        self.tabs[self.tab][4] += 1
        if self.tabs[self.tab][4] > len(self.tabs[self.tab][3])-1:
            self.tabs[self.tab][4] = len(self.tabs[self.tab][3])-1
        else:
            self.tabs[self.tab][0] = self.tabs[self.tab][3][self.tabs[self.tab][4]]
            # del self.tabs[self.tab][3][self.tabs[self.tab][4]]
        self.get_files(self.tabs[self.tab][0])
        print(self.tabs[self.tab][3],self.tabs[self.tab][4])
    
    def up_one_dir(self):
        _path = self.path[:self.path.rfind(self.path.split(f"{s}")[-1])-1]
        if _path != root[:-1]:
            self.get_files(_path)
        else:
            self.get_files(f"{root}")

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
                self.get_files(self.tabs[self.tab][0])


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

    def pin_tab(self,_tab,force_pin=False):
        global pinned, pins
        if _tab in self.tabs:
            dir = self.tabs[_tab][0]
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
            self.smode = val
        def setSSort(val):
            self.ssort = val

        icon_check = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        menu = QMenu()
        tog = menu.addAction("Toggle Search")
        tog.triggered.connect(partial(self.tog_el,(self.search_inp,self.search_go),-1))
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
        menu = QMenu()
        if self.tabs[self.tab][0] == trash:
            etrash = menu.addAction("Empty Trash")
            etrash.triggered.connect(partial(self.delete_file,"EMPTY_TRASH"))
        if f.is_dir():
            opent = menu.addAction("Open in New Tab")
            opent.triggered.connect(partial(self.add_tab,f.path))
        else:
            opent = menu.addAction("Open File")
            opent.triggered.connect(partial(self.open_file,f))
        # if sys.platform == "linux":
        openw = menu.addAction("Open with...")
        openw.triggered.connect(partial(self.open_with,f))
        rename = menu.addAction("Rename to...")
        rename.triggered.connect(partial(self.move_file,f,f"Rename {f.name} to..."))
        if self.tabs[self.tab][0] != trash:
            _trash = menu.addAction("Send to Trash")
            _trash.triggered.connect(partial(self.trash_file,f))
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
            self.get_files(self.tabs[self.tab][0])
    
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
                            if e.errno == 39 and self.tabs[self.tab][0] == f"{home}{s}{user}{s}.local{s}share{s}Trash{s}files":
                                try:
                                    shutil.rmtree(f.path)
                                except Exception as e:
                                    self.error_msg.showMessage(str(e))
                            else:
                                self.error_msg.showMessage(str(e))
                    self.get_files(self.tabs[self.tab][0])
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
                self.get_files(self.tabs[self.tab][0])

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
                        self.get_files(self.tabs[self.tab][0])
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
                        self.get_files(self.tabs[self.tab][0])
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
