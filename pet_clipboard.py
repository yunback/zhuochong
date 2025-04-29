from common_imports import *

class PetClipboard(QObject):
    clip_saved = pyqtSignal(str)  # 剪贴板内容保存信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.clipboard = QApplication.clipboard()
        self.history_file = self.config_dir / "clipboard_history.json"
        self.history = []
        self.max_history = 10
        self.load_history()

        # 使用定时器延迟监听剪贴板变化，避免初始化时的问题
        QTimer.singleShot(1000, self.setup_clipboard_monitoring)

    def setup_clipboard_monitoring(self):
        """设置剪贴板监听"""
        try:
            self.clipboard.dataChanged.connect(self.on_clipboard_change)
        except Exception as e:
            print(f"无法初始化剪贴板监听: {str(e)}")
            # 重试机制
            QTimer.singleShot(2000, self.setup_clipboard_monitoring)

    def load_history(self):
        """加载剪贴板历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                QMessageBox.warning(self.parent, "剪贴板错误", 
                                  f"加载历史记录失败: {str(e)}")

    def save_history(self):
        """保存剪贴板历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self.parent, "剪贴板错误",
                              f"保存历史记录失败: {str(e)}")

    def on_clipboard_change(self):
        """剪贴板内容变化时的处理"""
        try:
            text = self.clipboard.text().strip()
            if text and (not self.history or text != self.history[0]):
                self.add_to_history(text)
        except Exception as e:
            print(f"剪贴板访问错误: {str(e)}")
            # 重试机制
            QTimer.singleShot(1000, self.on_clipboard_change)

    def add_to_history(self, text):
        """添加内容到历史记录"""
        if not text:
            return
            
        try:
            if text in self.history:
                self.history.remove(text)
            
            self.history.insert(0, text)
            
            # 限制历史记录数量
            if len(self.history) > self.max_history:
                self.history = self.history[:self.max_history]
            
            self.save_history()
            self.clip_saved.emit(text)
        except Exception as e:
            QMessageBox.warning(self.parent, "剪贴板错误",
                              f"添加历史记录失败: {str(e)}")

    def show_clipboard_menu(self, event):
        """显示剪贴板菜单"""
        menu = QMenu(self.parent)
    
        # 当前剪贴板内容
        current_action = menu.addAction("当前内容")
        current_action.setEnabled(False)
    
        try:
            current_text = self.clipboard.text() or "(空)"
        except:
            current_text = "(无法访问剪贴板)"
        
        if len(current_text) > 20:
            current_text = current_text[:20] + "..."
    
        current_content = menu.addAction(current_text)
        current_content.setEnabled(False)
        menu.addSeparator()
    
        # 保存当前内容
        save_action = menu.addAction("保存当前内容")
        save_action.triggered.connect(
            lambda: self.add_to_history(self.clipboard.text())
        )
    
        # 历史记录
        if self.history:
            menu.addSeparator()
            history_title = menu.addAction("历史记录")
            history_title.setEnabled(False)
        
            for i, item in enumerate(self.history[:10]):
                display_text = f"{i+1}. {item[:20]}{'...' if len(item)>20 else ''}"
                action = menu.addAction(display_text)
                action.setData(item)
                action.triggered.connect(
                    lambda checked, x=item: self.set_clipboard_content(x)
                )
        
            # 管理历史记录
            menu.addSeparator()
            manage_action = menu.addAction("管理历史记录...")
            manage_action.triggered.connect(self.manage_history)
            clear_action = menu.addAction("清空历史记录")
            clear_action.triggered.connect(self.clear_history)
    
        # 使用 event.globalPos() 获取鼠标位置
        menu.exec_(event.globalPos())

    def set_clipboard_content(self, text):
        """设置剪贴板内容"""
        try:
            self.clipboard.setText(text)
            QMessageBox.information(self.parent, "已粘贴", 
                                  "内容已复制到剪贴板！",
                                  QMessageBox.Ok)
        except Exception as e:
            QMessageBox.warning(self.parent, "错误",
                              f"无法设置剪贴板内容: {str(e)}")

    def manage_history(self):
        """管理历史记录对话框"""
        items = [f"{i+1}. {item[:30]}{'...' if len(item)>30 else ''}" 
                for i, item in enumerate(self.history)]
        
        item, ok = QInputDialog.getItem(
            self.parent, "管理剪贴板历史",
            "选择要删除的记录:", items, 0, False
        )
        
        if ok and item:
            index = items.index(item)
            self.history.pop(index)
            self.save_history()
            QMessageBox.information(self.parent, "成功",
                                  "记录已删除!", QMessageBox.Ok)

    def clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(
            self.parent, '确认清空',
            '确定要清空所有剪贴板历史记录吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history = []
            self.save_history()
            QMessageBox.information(
                self.parent, "成功", "历史记录已清空!"
            )