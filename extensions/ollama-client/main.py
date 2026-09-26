from ollama import Client
import os
from PySide6.QtWidgets import (
    QWidget,
    QTextEdit,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QSizePolicy,
    QInputDialog,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, QRunnable, QThreadPool, Slot, Signal, QObject, QTimer
import qtawesome as qta

AVAILABLE_CLOUD_MODELS = [
    "deepseek-v4.1-flash:cloud",
    "glm-5.3-flash:cloud",
    "kimi-k2.6:cloud",
    "gpt-oss:120b-cloud",
    "gemma4:cloud",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY_FILE_PATH = os.path.join(SCRIPT_DIR, "key.txt")
API_KEY = ""

if os.path.exists(API_KEY_FILE_PATH):
    with open(API_KEY_FILE_PATH, "r") as f:
        API_KEY = f.read()

class AI_Worker_Signals(QObject):
    chunk_received = Signal(str)
    response_received = Signal()

class AI_Worker(QRunnable):
    def __init__(self, client, messages, model):
        super().__init__()

        self.client = client
        self.messages = messages
        self.model = model
        self.signals = AI_Worker_Signals()

    @Slot()
    def run(self):
        for part in self.client.chat(self.model, messages=self.messages, stream=True):
            self.signals.chunk_received.emit(part.message.content)
        
        self.signals.response_received.emit()

class MessageBox(QFrame):
    def __init__(self, message: dict, color: str = "#464646", parent = None):
        super().__init__(parent)

        self.message: dict = message
        self.color: str = color

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.setStyleSheet(f"padding: 4px; border-radius: 16px; background-color: {self.color}")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.content_textedit = QTextEdit()
        self.content_textedit.setReadOnly(True)
        self.content_textedit.setStyleSheet("border: none;")
        self.content_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.content_textedit)

        role = self.message.get("role", "Unknown")
        content = self.message.get("content", "")
        self.content_textedit.setMarkdown(f"**{role}**:\n{content}")

        controls_layout = QHBoxLayout()
        layout.addLayout(controls_layout)

        controls_layout.addStretch()

        self.copy_btn = QPushButton()
        self.copy_btn.setStyleSheet("background-color: none; border: none")
        self.copy_btn.setIcon(qta.icon("fa6s.copy"))
        self.copy_btn.setToolTip("Copy message")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_message)
        controls_layout.addWidget(self.copy_btn)

        self.copy_timer = QTimer()
        self.copy_timer.setInterval(500)
        self.copy_timer.timeout.connect(self._reset_icon)

        self.content_textedit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.content_textedit.document().contentsChanged.connect(self.adjust_height)

    def adjust_height(self):
        doc = self.content_textedit.document()
        doc.setTextWidth(self.content_textedit.viewport().width())
        height = doc.size().height()
        self.content_textedit.setFixedHeight(int(height) + 8)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_height()

    def update_color(self, color: str):
        self.color = color
        self.setStyleSheet(f"padding: 4px; border-radius: 16px; background-color: {self.color}")

    def update_content(self, content: str):
        self.message["content"] = content
        self.content_textedit.setMarkdown(f"**{self.message.get('role', 'Unknown')}**:\n{content}")

    def _copy_message(self):
        pyperclip.copy(self.message.get("content", ""))
        self.copy_btn.setIcon(qta.icon("fa6s.check"))
        self.copy_timer.start()

    def _reset_icon(self):
        self.copy_btn.setIcon(qta.icon("fa6s.copy"))
        self.copy_timer.stop()

class MainWidget(QWidget):
    def __init__(self, controller=None):
        super().__init__()

        self.messages = [{"role":"system", "content":"Welcome to the Ollama API Client!"}]
        self.accent_color = "#4643d8"
        self.setFixedSize(640, 480)

        self.layout = QVBoxLayout()
        self.top_layout = QHBoxLayout()
        self.main_layout = QVBoxLayout()
        self.message_control_layout = QHBoxLayout()

        self.layout.addLayout(self.top_layout)
        self.layout.addLayout(self.main_layout)
        self.layout.addLayout(self.message_control_layout)
        self.setLayout(self.layout)

        self.init_ui()
        self.update_output()
        self.check_key()
      
    def init_ui(self):
        self.ai_selector = QComboBox()
        self.ai_selector.addItems(AVAILABLE_CLOUD_MODELS)
        self.top_layout.addWidget(self.ai_selector)

        self.key_edit_btn = QPushButton()
        self.key_edit_btn.setIcon(qta.icon("fa6s.key"))
        self.key_edit_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.key_edit_btn.clicked.connect(self.change_api_key)
        self.top_layout.addWidget(self.key_edit_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setIcon(qta.icon("fa6s.trash"))
        self.clear_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.clear_btn.clicked.connect(self.reset_chat)
        self.top_layout.addWidget(self.clear_btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.message_container = QWidget()
        self.message_container_layout = QVBoxLayout(self.message_container)
        self.message_container_layout.setContentsMargins(10, 10, 10, 10)
        self.message_container_layout.setSpacing(4)

        scroll.setWidget(self.message_container)
        self.main_layout.addWidget(scroll)

        self.user_msg_box = QLineEdit()
        self.user_msg_box.setStyleSheet("padding: 8px")
        self.user_msg_box.setPlaceholderText("Type message here...")
        self.user_msg_box.returnPressed.connect(self.send_message)
        self.message_control_layout.addWidget(self.user_msg_box)

        self.user_send_btn = QPushButton("Send")
        self.user_send_btn.setIcon(qta.icon("mdi.send"))
        self.user_send_btn.setStyleSheet("padding: 8px")
        self.user_send_btn.clicked.connect(self.send_message)
        self.message_control_layout.addWidget(self.user_send_btn)

        self.threadpool = QThreadPool()
    
    def send_message(self):
        message = self.user_msg_box.text().strip()
        model = self.ai_selector.currentText()

        if not message:
            return

        self.user_msg_box.clear()
        self.user_msg_box.setEnabled(False)
        self.user_send_btn.setEnabled(False)
        self.ai_selector.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.key_edit_btn.setEnabled(False)
        self.user_send_btn.setIcon(qta.icon("fa6s.hourglass-half"))

        self.messages.append({"role":"user", "content":message})
        self.update_output()

        worker = AI_Worker(self.client, self.messages, model)
        self.messages.append({"role":"assistant", "content":""})

        worker.signals.chunk_received.connect(self.update_ai_response)
        worker.signals.response_received.connect(self.reset_controlstates)
        self.threadpool.start(worker)

    def reset_controlstates(self):
        self.user_msg_box.setEnabled(True)
        self.user_send_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.key_edit_btn.setEnabled(True)
        self.user_send_btn.setIcon(qta.icon("mdi.send"))

    def update_ai_response(self, chunk):
        self.messages[-1]["content"] += chunk
        self.update_output()
    
    def reset_chat(self):
        self.messages = []
        self.update_output()
        self.ai_selector.setEnabled(True)
      
    def clear_output(self) -> None:
        self.messages = []
        self.update_output()
    
    def update_output(self) -> None:
        layout = self.message_container_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for message in self.messages:
            print(message)
            self.add_message_box(message)
        
        self.message_container_layout.addStretch()

    def add_message_box(self, message) -> MessageBox:
        color = "#464646"

        if message.get("role") == "user":
            color = self.accent_color

        message_box = MessageBox(
            message=message,
            color=color
        )

        last_item = self.message_container_layout.itemAt(self.message_container_layout.count() - 1)
        if last_item is not None and last_item.spacerItem() is not None:
            self.message_container_layout.insertWidget(self.message_container_layout.count() - 1, message_box)
        else:
            self.message_container_layout.addWidget(message_box)

        return message_box

    def get_last_message_box(self):
        layout = self.message_container_layout
        for i in range(layout.count() - 1, -1, -1):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, MessageBox):
                return widget
        return None
    
    def handle_chunk(self, chunk) -> None:
        if self.messages and self.messages[-1]['role'] == "assistant":
            self.messages[-1]['content'] += chunk
            message_box = self.get_last_message_box()
            if message_box is not None:
                message_box.update_content(self.messages[-1]['content'])
                return
        else:
            self.messages.append({"role": "assistant", "content": chunk})

        self.update_output()

    def change_api_key(self):
        changed_api_key, ok = QInputDialog.getText(self, "API Key", "Input your Ollama API key:")
        changed_api_key = changed_api_key.strip()
        
        if changed_api_key:
            global API_KEY
            API_KEY = changed_api_key

            with open(API_KEY_FILE_PATH, "w") as f:
                f.write(API_KEY)
            
            self.check_key()

    def check_key(self):
        if API_KEY == "":
            self.user_msg_box.setEnabled(False)
            self.user_send_btn.setEnabled(False)
            self.ai_selector.setEnabled(False)
            self.clear_btn.setEnabled(False)
        
        else:
            self.user_msg_box.setEnabled(True)
            self.user_send_btn.setEnabled(True)
            self.ai_selector.setEnabled(True)
            self.clear_btn.setEnabled(True)

            self.client = Client(
                host='https://ollama.com',
                headers={'Authorization': 'Bearer ' + API_KEY}
            )