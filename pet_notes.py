from common_imports import *


class PetNotes:
    def __init__(self, parent):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.parent = parent
        self.notes_file =self.config_dir / "pet_notes.json"
        self.notes = {}
        self.load_notes()

    def load_notes(self):
        """加载保存的笔记"""
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
            except Exception as e:
                QMessageBox.warning(self.parent, "笔记错误", f"加载笔记失败: {str(e)}")
                self.notes = {}

    def save_notes(self):
        """保存笔记到文件"""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self.parent, "笔记错误", f"保存笔记失败: {str(e)}")

    def show_note_dialog(self, note_key=None):
        """显示笔记编辑对话框"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("宠物笔记" if not note_key else f"编辑笔记: {note_key}")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        # 笔记内容编辑框
        text_edit = QTextEdit()
        if note_key and note_key in self.notes:
            text_edit.setText(self.notes[note_key])
        
        # 按钮框
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(text_edit)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            note_content = text_edit.toPlainText().strip()
            if note_content:
                if not note_key:
                    note_key, ok = QInputDialog.getText(
                        self.parent, "笔记标题", "请输入笔记标题:"
                    )
                    if not ok or not note_key:
                        return
                
                self.notes[note_key] = note_content
                self.save_notes()
                QMessageBox.information(
                    self.parent, "成功", "笔记已保存!"
                )

    def show_notes_menu(self, event):
        """显示笔记菜单"""
        menu = QMenu(self.parent)
    
        # 添加新笔记
        new_note_action = menu.addAction("新建笔记")
        new_note_action.triggered.connect(
            lambda: self.show_note_dialog()
        )
    
        # 已有笔记列表
        if self.notes:
            menu.addSeparator()
            for note_title in self.notes.keys():
                note_action = menu.addAction(f"编辑: {note_title}")
                note_action.triggered.connect(
                    lambda checked, title=note_title: self.show_note_dialog(title)
                )
        
            # 删除所有笔记
            menu.addSeparator()
            clear_action = menu.addAction("删除所有笔记")
            clear_action.triggered.connect(self.clear_all_notes)
    
        # 使用 event.globalPos() 获取鼠标位置
        menu.exec_(event.globalPos())

    def clear_all_notes(self):
        """删除所有笔记"""
        reply = QMessageBox.question(
            self.parent, '确认删除',
            '确定要删除所有笔记吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.notes = {}
            try:
                os.remove(self.notes_file)
                QMessageBox.information(
                    self.parent, "成功", "所有笔记已删除!"
                )
            except Exception as e:
                QMessageBox.warning(
                    self.parent, "错误", f"删除笔记失败: {str(e)}"
                )