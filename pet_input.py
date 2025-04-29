from common_imports import *
import datetime

class PetInput:
    def __init__(self, pet_widget):
        self.pet_widget = pet_widget
        self.input_box = None
        self.response_box = None
        self.setup_input()
        self.conversation_history = []
        self.current_conversation_id = None

    def setup_input(self):
        # 创建输入框
        self.input_box = QLineEdit(self.pet_widget)
        self.input_box.setPlaceholderText("要问我什么呢...")
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 5px;
                min-width: 250px;  # 增加最小宽度
            }
        """)
    
        # 创建响应框
        self.response_box = QTextEdit(self.pet_widget)
        self.response_box.setReadOnly(True)
        self.response_box.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 5px;
                min-width: 250px;  # 增加最小宽度
                max-height: 150px;
            }
        """)
        self.response_box.setLineWrapMode(QTextEdit.WidgetWidth)  # 自动换行
        self.response_box.hide()
    
        self.input_box.hide()

    def adjust_window_size(self):
        base_width = max(250, self.pet_widget.pet_image.width())  # 确保足够宽度
        height = self.pet_widget.pet_image.height()
    
        if not self.input_box.isHidden():
            height += self.input_box.height() + 10
        if not self.response_box.isHidden():
            height += self.response_box.height() + 10
    
        self.pet_widget.resize(base_width, height)

    def toggle_input(self):
        if self.input_box.isHidden():
            self.show_input()
        else:
            self.hide_input()

    def show_input(self):
        self.input_box.show()
        self.input_box.setFocus()
        self.adjust_window_size()

    def hide_input(self):
        self.input_box.hide()
        self.response_box.hide()
        self.adjust_window_size()

    def show_response(self, text):
        """显示响应文本"""
        if not self.current_conversation_id:
            self.current_conversation_id = int(time.time())
        
        self.response_box.setPlainText(text)
        self.response_box.show()
        self.adjust_window_size()
        
        # 添加到当前对话历史
        self.conversation_history.append(("assistant", text))
        self.save_conversation()

    def add_user_input(self, text):
        """添加用户输入到对话历史"""
        if not self.current_conversation_id:
            self.current_conversation_id = int(time.time())
        
        self.conversation_history.append(("user", text))
        
    def save_conversation(self):
        """保存对话历史到文件"""
        if not self.conversation_history:
            return
            
        # 确保history目录存在
        history_dir = "history"
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{history_dir}/conversation_{timestamp}.txt"
        
        # 写入文件
        with open(filename, "w", encoding="utf-8") as f:
            for role, text in self.conversation_history:
                f.write(f"{role}: {text}\n\n")

    def adjust_window_size(self):
        height = self.pet_widget.pet_image.height()
        if not self.input_box.isHidden():
            height += self.input_box.height() + 10
        if not self.response_box.isHidden():
            height += self.response_box.height() + 10
        self.pet_widget.resize(max(200, self.pet_widget.width()), height)

    def setup_layout(self):
        layout = QVBoxLayout(self.pet_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.pet_widget.pet_image, 0, Qt.AlignCenter)
        layout.addWidget(self.input_box, 0, Qt.AlignCenter)
        layout.addWidget(self.response_box, 0, Qt.AlignCenter)
        return layout