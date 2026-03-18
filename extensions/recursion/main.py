from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
)
import os
import re
import qtawesome as qta
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
START_PAGE_PATH = os.path.join(SCRIPT_DIR, "assets", "index.html")

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.controls_layout = QHBoxLayout()
        self.layout.addLayout(self.controls_layout)
        self.setLayout(self.layout)

        self.init_ui()

    def init_ui(self):
        self.webengine = QWebEngineView()
        self.webengine.setUrl(QUrl(""))
        self.layout.addWidget(self.webengine)

        self.back_btn = QPushButton()
        self.back_btn.setIcon(qta.icon("fa6s.arrow-left"))
        self.back_btn.setStyleSheet("padding: 8px;")
        self.back_btn.clicked.connect(lambda: self.webengine.back())
        self.controls_layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(qta.icon("fa6s.arrow-right"))
        self.forward_btn.setStyleSheet("padding: 8px;")
        self.forward_btn.clicked.connect(lambda: self.webengine.forward())
        self.controls_layout.addWidget(self.forward_btn)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://")
        self.url_edit.setStyleSheet("padding: 8px;")
        self.url_edit.returnPressed.connect(self.load_page)
        self.controls_layout.addWidget(self.url_edit)

        self.webengine.urlChanged.connect(self.url_changed_update_ui)
        self.webengine.loadStarted.connect(lambda: self.webengine.page().setBackgroundColor(QColor("#101011")))
        self.webengine.loadFinished.connect(lambda: self.webengine.page().setBackgroundColor(QColor("#ffffff")))

        if os.path.exists(START_PAGE_PATH):
            self.webengine.setUrl(QUrl("file://" + START_PAGE_PATH))
        
        else:
            self.webengine.setUrl(QUrl("https://google.com/"))
    
    def url_changed_update_ui(self, url):
        self.url_edit.setText(url.toString())
        self.back_btn.setEnabled(self.webengine.history().canGoBack())
        self.forward_btn.setEnabled(self.webengine.history().canGoForward())
    
    def load_page(self):
        # Load URL if valid, else use the default search engine
        url = self.url_edit.text()
        processed_url = QUrl.fromUserInput(url).toString()

        if self.valid_url(processed_url) or self.valid_url(url):
            self.webengine.setUrl(QUrl(processed_url))
        else:
            # Get url for search engine
            search_url = "https://www.google.com/search?q=" + url
            self.webengine.setUrl(QUrl(search_url))
    
    def valid_url(self, url):
        # Regex for standard http/https URLs and file paths
        regex = re.compile(
            r'^(?:(?:http|ftp)s?|file)://'  # file
            r'(?:'
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain
                r'localhost|' # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # or ip
            r'|' # OR 
                r'/[^\s]+' # Absolute path for file:/// schemes
            r')'
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return re.match(regex, url) is not None