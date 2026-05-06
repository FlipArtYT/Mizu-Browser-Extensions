from PySide6.QtWidgets import (
    QWidget,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QPushButton,
    QLabel,
    QScrollArea,
    QLineEdit,
    QMessageBox,
)
from services.highlighter import MarkdownHighlighter
import os
import datetime
import qtawesome as qta
from PySide6.QtCore import Qt, QTimer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_PATH = os.path.join(SCRIPT_DIR, "notes")

if not os.path.exists(NOTES_PATH):
    os.makedirs(NOTES_PATH, exist_ok=True)

class NoteManager():
    def __init__(self, path=NOTES_PATH):
        self.notes_path = path
        self.allowed_filetypes = ("txt", "md")
        self.notes = {}

        self.load_notes()

    def load_notes(self):
        self.notes = {}
        
        with os.scandir(self.notes_path) as d:
            for el in d:
                if el.is_file() and el.path.endswith(self.allowed_filetypes):
                    # Open selected file and add it to the notes dictionary
                    with open(el.path, "r") as f:
                        content = f.read()
                    
                    self.notes[el.name] = {"title":el.name.split(".")[0], "content":content}
    
    def new_note(self):
        time_now = datetime.datetime.now()
        time_formatted = time_now.strftime("%H:%M-%d-%m-%Y")
        file_name = f"New Note {time_formatted}"
        constructed_path = os.path.join(self.notes_path, f"{file_name}.md")

        # Loop if file already exists
        if os.path.exists(constructed_path):
            while os.path.exists(constructed_path):
                file_name += " (1)"
                constructed_path = os.path.join(self.notes_path, f"{file_name}.md")

        # Create file
        with open(constructed_path, "w"):
            pass

    def get_notes(self):
        return self.notes

class NoteItem(QPushButton):
    def __init__(self, abs_name, note_data:dict):
        super().__init__()
        self.abs_name = abs_name
        self.note_data = note_data

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.init_ui()
    
    def init_ui(self):
        self.title_label = QLabel(self.note_data["title"])
        self.title_label.setStyleSheet("font-size: 17px; font-weight: bold; background: none")
        self.title_label.setWordWrap(True)
        self.layout.addWidget(self.title_label)

        self.content_preview_label = QLabel()
        self.content_preview_label.setStyleSheet("background: none")
        self.content_preview_label.setWordWrap(True)

        if len(self.note_data["content"]) > 50:
            self.content_preview_label.setText(self.note_data["content"][:50] + "...")
        else:
            self.content_preview_label.setText(self.note_data["content"])

        
        self.layout.addWidget(self.content_preview_label)

class NoteViewer(QWidget):
    def __init__(self, path=NOTES_PATH):
        super().__init__()

        self.notes_path = path
        self.current_file = ""

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.init_ui()
    
    def init_ui(self):
        self.note_title = QLineEdit()
        self.note_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.note_title)

        self.note_content = QTextEdit()
        self.highlighter = MarkdownHighlighter(self.note_content.document())
        self.layout.addWidget(self.note_content)
    
    def load_data(self, abs_path, data):
        self.current_file = abs_path

        self.note_title.setText(data["title"])
        self.note_content.setText(data["content"])
    
    def save_data(self):
        if self.current_file != "":
            # Extract current note data
            title = self.note_title.text()
            content = self.note_content.toPlainText()
            full_current_path = os.path.join(self.notes_path, self.current_file)

            if self.current_file not in note_mgr.notes:
                return

            # Change content if needed
            if content != note_mgr.notes[self.current_file]["content"]:
                with open(full_current_path, "w") as f:
                    f.write(content)
            
            # Rename if needed
            if title != note_mgr.notes[self.current_file]["title"] and not f"{title}.txt" in note_mgr.notes.keys():
                new_file_name = f"{title}.txt"
                os.rename(full_current_path, os.path.join(self.notes_path, new_file_name))
                self.current_file = new_file_name
    
    def delete_file(self):
        if self.current_file != "":
            full_current_path = os.path.join(self.notes_path, self.current_file)

        warning_dlg = QMessageBox(self)
        warning_dlg.setWindowTitle(self.tr("Download Request"))
        warning_dlg.setText(f"Do you really want to delete {self.current_file.split(".")[0]}?")
        warning_dlg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        warning_dlg.setIcon(QMessageBox.Icon.Warning)

        if warning_dlg.exec() == QMessageBox.StandardButton.Ok:
            self.current_file = ""
            os.remove(full_current_path)

class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.file_open = False

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init_ui()
    
    def init_ui(self):
        self.control_bar_layout = QHBoxLayout()
        self.main_content_layout = QVBoxLayout()

        # Control buttons
        self.toggle_overview_btn = QPushButton()
        self.toggle_overview_btn.setIcon(qta.icon("ri.menu-fill"))
        self.toggle_overview_btn.setStyleSheet("padding: 8px")
        self.toggle_overview_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.toggle_overview_btn.setEnabled(False)
        self.toggle_overview_btn.clicked.connect(self.toggle_note_overview)
        self.control_bar_layout.addWidget(self.toggle_overview_btn)

        self.control_bar_layout.addStretch()

        self.new_note_btn = QPushButton()
        self.new_note_btn.setIcon(qta.icon("fa6s.plus"))
        self.new_note_btn.setStyleSheet("padding: 8px")
        self.new_note_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.new_note_btn.clicked.connect(self.create_new_note)
        self.control_bar_layout.addWidget(self.new_note_btn)

        self.save_note_btn = QPushButton()
        self.save_note_btn.setIcon(qta.icon("fa6s.floppy-disk"))
        self.save_note_btn.setStyleSheet("padding: 8px")
        self.save_note_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.save_note_btn.setEnabled(False)
        self.save_note_btn.clicked.connect(self.save_current_file)
        self.control_bar_layout.addWidget(self.save_note_btn)

        self.delete_note_btn = QPushButton()
        self.delete_note_btn.setIcon(qta.icon("fa6s.trash"))
        self.delete_note_btn.setStyleSheet("padding: 8px")
        self.delete_note_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.delete_note_btn.setEnabled(False)
        self.delete_note_btn.clicked.connect(self.delete_current_file)
        self.control_bar_layout.addWidget(self.delete_note_btn)

        # Notes overview
        self.note_overview_scrollable = QScrollArea()
        self.note_overview_widget = QWidget()
        self.note_overview_layout = QVBoxLayout()

        self.note_overview_scrollable.setWidget(self.note_overview_widget)
        self.note_overview_widget.setLayout(self.note_overview_layout)

        self.note_overview_scrollable.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.note_overview_scrollable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.note_overview_scrollable.setWidgetResizable(True)

        self.update_display_notes()

        # Note content
        self.note_viewer = NoteViewer()
        self.main_content_layout.addWidget(self.note_viewer)

        self.note_viewer.hide()

        self.layout.addLayout(self.control_bar_layout)
        self.layout.addWidget(self.note_overview_scrollable)
        self.layout.addLayout(self.main_content_layout)

        # Autosaver
        #self.autosave_timer = QTimer()
        #self.autosave_timer.setInterval(5000)
        #self.autosave_timer.timeout.connect(self.save_current_file)

    def toggle_note_overview(self):
        if self.note_overview_scrollable.isVisible():
            # Show note content
            self.note_viewer.show()
            self.note_overview_scrollable.hide()
        else:
            # Show note overview
            self.note_viewer.hide()
            self.note_overview_scrollable.show()
        
        self.save_current_file()
    
    def update_display_notes(self):
        # Delete current widgets in layout
        self.clear_layout(self.note_overview_layout)
        
        for file, content in note_mgr.notes.items():
            btn = NoteItem(file, content)
            btn.setStyleSheet("padding: 5px;")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
            btn.clicked.connect(lambda _, f=file, content=content: self.open_raw_data(f, content))
            self.note_overview_layout.addWidget(btn)
        
        self.note_overview_layout.addStretch()
    
    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())
    
    def create_new_note(self):
        note_mgr.new_note()
        note_mgr.load_notes()
        self.update_display_notes()
    
    def save_current_file(self):
        self.note_viewer.save_data()
        note_mgr.load_notes()
        self.update_display_notes()
    
    def delete_current_file(self):
        self.note_viewer.delete_file()
        self.file_open = False

        note_mgr.load_notes()
        self.update_display_notes()
        self.toggle_note_overview()

        self.toggle_overview_btn.setEnabled(False)
        self.save_note_btn.setEnabled(False)
        self.delete_note_btn.setEnabled(False)
    
    def open_raw_data(self, abs_path, data):
        self.note_viewer.load_data(abs_path, data)

        if not self.file_open:
            self.file_open = True

            self.toggle_overview_btn.setEnabled(True)
            self.save_note_btn.setEnabled(True)
            self.delete_note_btn.setEnabled(True)

            #self.autosave_timer.start()

        self.toggle_note_overview()

        
note_mgr = NoteManager()