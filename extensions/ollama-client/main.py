from ollama import Client
import os
from PyQt6.QtWidgets import (
    QWidget,
    QTextEdit,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QSizePolicy,
    QInputDialog,
)
from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QObject
import qtawesome as qta

AVAILABLE_CLOUD_MODELS = [
    "qwen3.5:397b-cloud",
    "gemini-3-flash-preview:cloud",
    "glm-4.6:cloud",
    "kimi-k2:1t-cloud",
    "gpt-oss:120b-cloud",
    "gemma3:27b-cloud",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY_FILE_PATH = os.path.join(SCRIPT_DIR, "key.txt")
API_KEY = ""

if os.path.exists(API_KEY_FILE_PATH):
    with open(API_KEY_FILE_PATH, "r") as f:
        API_KEY = f.read()

class AI_Worker_Signals(QObject):
    chunk_received = pyqtSignal(str)
    response_received = pyqtSignal()

class AI_Worker(QRunnable):
    def __init__(self, client, messages, model):
        super().__init__()

        self.client = client
        self.messages = messages
        self.model = model
        self.signals = AI_Worker_Signals()

    @pyqtSlot()
    def run(self):
        for part in self.client.chat(self.model, messages=self.messages, stream=True):
            self.signals.chunk_received.emit(part.message.content)
        
        self.signals.response_received.emit()

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.messages = [{"role":"system", "content":"Welcome to the Ollama API Client!"}]

        self.layout = QVBoxLayout()
        self.top_layout = QHBoxLayout()
        self.main_layout = QVBoxLayout()
        self.message_control_layout = QHBoxLayout()

        self.layout.addLayout(self.top_layout)
        self.layout.addLayout(self.main_layout)
        self.layout.addLayout(self.message_control_layout)
        self.setLayout(self.layout)

        self.init_ui()
        self.update_messages()
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

        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.main_layout.addWidget(self.chat_box)

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
        self.update_messages()

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
        self.update_messages()
    
    def reset_chat(self):
        self.messages = []
        self.update_messages()
        self.ai_selector.setEnabled(True)
      
    def update_messages(self):
        formatted_string = ""
        v_bar = self.chat_box.verticalScrollBar()
        v_bar_at_bottom = v_bar.value() >= v_bar.maximum() - 20

        for data in self.messages:
            role = data["role"]
            message = data["content"]

            if role == "assistant":
                model = self.ai_selector.currentText()
                formatted_string += f"\n**{model}**: {message}\n"
            
            elif role == "user":
                formatted_string += f"\n**User**: {message}\n"
            
            else:
                formatted_string += f"\n{message}\n"
        
        self.chat_box.setMarkdown(formatted_string)

        if v_bar_at_bottom:
            v_bar.setValue(v_bar.maximum())


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