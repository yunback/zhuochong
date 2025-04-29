from common_imports import *


class PetWebBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("桌宠浏览器")
        self.setMinimumSize(1000, 800)
        
        # 初始化配置路径和默认URL
        self.config_path = self.config_dir / "browser_config.json"
        self.default_url = "https://babie.cc/"  # 默认值
        
        self.init_ui()
        self.load_default_page()  # 改为加载配置的URL

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 地址栏和按钮
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("输入网址 (例如: https://www.baidu.com)")
        self.url_bar.returnPressed.connect(self.load_url)
        
        nav_layout = QHBoxLayout()
        self.back_btn = QPushButton("←")
        self.forward_btn = QPushButton("→")
        self.refresh_btn = QPushButton("刷新")
        self.external_btn = QPushButton("外部浏览器打开")
        self.set_default_btn = QPushButton("设为默认")
        
        self.back_btn.clicked.connect(self.go_back)
        self.forward_btn.clicked.connect(self.go_forward)
        self.refresh_btn.clicked.connect(self.refresh_page)
        self.external_btn.clicked.connect(self.open_external)
        self.set_default_btn.clicked.connect(self.set_default_url)
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.refresh_btn)
        nav_layout.addWidget(self.url_bar)
        nav_layout.addWidget(self.external_btn)
        nav_layout.addWidget(self.set_default_btn)
        
        # 网页视图
        self.web_view = QWebEngineView()
        
        layout.addLayout(nav_layout)
        layout.addWidget(self.web_view)
        self.setLayout(layout)

    def load_default_page(self):
        """加载默认页面（从配置文件读取）"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # 如果配置文件存在，读取配置
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    self.default_url = config.get("default_url", self.default_url)
        except Exception as e:
            print(f"[WARN] 加载配置失败: {e}, 使用默认URL")
        
        # 加载URL
        self.web_view.setUrl(QUrl(self.default_url))
        self.url_bar.setText(self.default_url)

    def load_url(self):
        """加载URL"""
        url = self.url_bar.text()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.web_view.setUrl(QUrl(url))
        self.url_bar.setText(url)

    def set_default_url(self):
        """将当前URL保存为默认"""
        current_url = self.url_bar.text()
        if current_url:
            try:
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, "w") as f:
                    json.dump({"default_url": current_url}, f)
                QMessageBox.information(self, "成功", f"已设置默认主页为: {current_url}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存配置失败: {e}")

    def go_back(self):
        """后退"""
        self.web_view.back()

    def go_forward(self):
        """前进"""
        self.web_view.forward()

    def refresh_page(self):
        """刷新页面"""
        self.web_view.reload()

    def open_external(self):
        """在系统默认浏览器中打开"""
        url = self.url_bar.text().strip()
        if url:
            try:
                webbrowser.open(url)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开外部浏览器:\n{str(e)}")

    def closeEvent(self, event):
        """关闭时清理资源"""
        self.web_view.deleteLater()
        super().closeEvent(event)