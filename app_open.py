from common_imports import *

class AppConfigDialog(QDialog):
    def __init__(self, app_launcher, parent=None):
        super().__init__(parent)
        self.app_launcher = app_launcher
        self.setWindowTitle("应用管理")
        self.setWindowIcon(QIcon.fromTheme('preferences-system'))
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 应用列表
        self.app_list = QListWidget()
        self.app_list.setSelectionMode(QListWidget.SingleSelection)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        # 添加应用按钮
        add_app_btn = QPushButton("添加应用")
        add_app_btn.clicked.connect(lambda: self.add_item(is_script=False))
        btn_layout.addWidget(add_app_btn)
        
        # 添加脚本按钮
        add_script_btn = QPushButton("添加脚本")
        add_script_btn.clicked.connect(lambda: self.add_item(is_script=True))
        btn_layout.addWidget(add_script_btn)
        
        # 删除按钮
        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(del_btn)
        
        # 分类管理
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("分类:"))
        
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        category_layout.addWidget(self.category_combo)
        
        # 保存/取消按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        # 添加控件到主布局
        layout.addWidget(QLabel("应用列表:"))
        layout.addWidget(self.app_list)
        layout.addLayout(btn_layout)
        layout.addLayout(category_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.populate_app_list()
        self.update_category_combo()

    def populate_app_list(self):
        self.app_list.clear()
        for app in self.app_launcher.apps:
            item = QListWidgetItem(f"{app['name']} ({app['category']})")
            item.setData(Qt.UserRole, app)
            item.setIcon(app['icon'])
            self.app_list.addItem(item)

    def update_category_combo(self):
        self.category_combo.clear()
        categories = sorted({app['category'] for app in self.app_launcher.apps})
        self.category_combo.addItems(categories)

    def add_item(self, is_script=False):
        """添加应用或脚本"""
        file_dialog = QFileDialog()
        file_types = "Python脚本 (*.py);;所有文件 (*)" if is_script else "应用程序 (*.exe *.lnk);;所有文件 (*)"
        default_dir = os.getcwd() if is_script else QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)
        
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            "选择Python脚本" if is_script else "选择应用程序",
            default_dir,
            file_types
        )
        
        if file_path:
            name, ok = QInputDialog.getText(
                self, "名称", 
                f"输入{'脚本' if is_script else '应用'}显示名称:", 
                text=os.path.splitext(os.path.basename(file_path))[0]
            )
            
            if ok and name:
                category, ok = QInputDialog.getItem(
                    self, "分类", 
                    "选择或输入分类:", 
                    sorted({app['category'] for app in self.app_launcher.apps}), 
                    0, True
                )
                
                if ok and category:
                    app_info = {
                        'name': name,
                        'path': file_path,
                        'icon': self.app_launcher.get_app_icon(file_path),
                        'category': category,
                        'filename': os.path.basename(file_path),
                        'is_script': is_script
                    }
                    
                    self.app_launcher.apps.append(app_info)
                    self.app_launcher.update_category(app_info)
                    self.populate_app_list()
                    self.update_category_combo()

    def delete_selected(self):
        """删除选中项（同时支持应用和脚本）"""
        selected = self.app_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return
    
        app = selected.data(Qt.UserRole)
    
        # 更健壮的删除方式 - 通过路径匹配
        to_remove = None
        for item in self.app_launcher.apps:
            if item['path'] == app['path']:  # 通过路径唯一标识
                to_remove = item
                break
    
        if not to_remove:
            QMessageBox.warning(self, "错误", "选中的项目不存在于列表中")
            return
    
        # 确认对话框
        item_type = "脚本" if app.get('is_script', False) else "应用"
        reply = QMessageBox.question(
            self, '确认删除',
            f"确定要删除{item_type} [{app['name']}] 吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
    
        if reply == QMessageBox.Yes:
            try:
                self.app_launcher.apps.remove(to_remove)
                # 重新加载数据
                self.app_launcher.categories = {}
                for app_item in self.app_launcher.apps:
                    self.app_launcher.update_category(app_item)
            
                self.populate_app_list()
                self.update_category_combo()
                QMessageBox.information(self, "成功", f"{item_type}已删除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

class AppLauncher:
    def __init__(self, pet_widget):
        self.pet_widget = pet_widget
        self.apps = []
        self.categories = {}
        self.config_dir = os.path.join(os.getcwd(), "config")
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "app_config.json")
        self.load_apps()

    def load_apps(self):
        """加载应用配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for app_config in config.get('apps', []):
                        if os.path.exists(app_config['path']):
                            app_info = {
                                'name': app_config.get('name', os.path.splitext(os.path.basename(app_config['path']))[0]),
                                'path': app_config['path'],
                                'icon': self.get_app_icon(app_config['path']),
                                'category': app_config.get('category', "其他"),
                                'filename': os.path.basename(app_config['path']),
                                'is_script': app_config.get('is_script', False)
                            }
                            self.apps.append(app_info)
                            self.update_category(app_info)
        except Exception as e:
            QMessageBox.warning(self.pet_widget, "错误", f"加载配置失败: {str(e)}")

    def save_config(self):
        """保存配置到文件"""
        try:
            config = {
                'apps': [{
                    'name': app['name'],
                    'path': app['path'],
                    'category': app['category'],
                    'is_script': app.get('is_script', False)
                } for app in self.apps]
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            QMessageBox.warning(self.pet_widget, "错误", f"保存失败: {str(e)}")
            return False

    def update_category(self, app_info):
        """更新分类字典（确保线程安全）"""
        with threading.Lock():  # 防止多线程冲突
            category = app_info['category']
            if category not in self.categories:
                self.categories[category] = []
        
            # 防止重复添加
            if not any(app['path'] == app_info['path'] for app in self.categories[category]):
                self.categories[category].append(app_info)

    def get_app_icon(self, app_path):
        """获取应用图标"""
        try:
            if app_path.endswith('.py'):
                return QIcon.fromTheme('text-x-python')
            return QIcon(app_path)
        except:
            return QIcon.fromTheme('application-x-executable')

    def create_app_menu(self, parent_menu):
        """创建新的菜单结构"""
        if not self.apps:
            no_app_action = QAction("无可用应用", parent_menu)
            no_app_action.setEnabled(False)
            parent_menu.addAction(no_app_action)
            
            # 添加管理入口
            manage_action = QAction("管理应用", parent_menu)
            manage_action.triggered.connect(self.show_config_dialog)
            parent_menu.addAction(manage_action)
            return
        
        # 第一级菜单 - 软件
        software_menu = parent_menu.addMenu("软件")
        
        # 第二级菜单 - 应用/脚本/管理
        app_menu = software_menu.addMenu("应用")
        script_menu = software_menu.addMenu("脚本")
        manage_menu = software_menu.addMenu("管理")
        
        # 添加管理选项
        config_action = QAction("添加/删除应用", manage_menu)
        config_action.triggered.connect(self.show_config_dialog)
        manage_menu.addAction(config_action)
        
        # 添加分组应用
        for category, apps in sorted(self.categories.items()):
            # 普通应用
            cat_apps = [app for app in apps if not app.get('is_script', False)]
            if cat_apps:
                cat_menu = app_menu.addMenu(category)
                for app in cat_apps:
                    self.add_app_action(cat_menu, app)
            
            # 脚本
            cat_scripts = [app for app in apps if app.get('is_script', False)]
            if cat_scripts:
                script_cat_menu = script_menu.addMenu(category)
                for script in cat_scripts:
                    self.add_app_action(script_cat_menu, script)

    def show_config_dialog(self):
        """显示配置对话框"""
        dialog = AppConfigDialog(self, self.pet_widget)
        if dialog.exec_() == QDialog.Accepted:
            # 重新组织分类
            self.categories = {}
            for app in self.apps:
                self.update_category(app)
            self.save_config()

    def add_app_action(self, menu, app):
        """添加应用到菜单"""
        action = QAction(app['name'], menu)
        action.setIcon(app['icon'])
        if app.get('is_script', False):
            action.triggered.connect(lambda: self.launch_script(app['path']))
        else:
            action.triggered.connect(lambda: self.launch_app(app['path']))
        menu.addAction(action)

    def launch_app(self, app_path):
        """启动应用程序"""
        try:
            if os.name == 'nt':
                os.startfile(app_path)
            else:
                subprocess.Popen([app_path])
        except Exception as e:
            QMessageBox.warning(self.pet_widget, "错误", f"启动失败: {str(e)}")

    def launch_script(self, script_path):
        """启动Python脚本"""
        try:
            if os.name == 'nt':
                subprocess.Popen(['python', script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(['python3', script_path])
        except Exception as e:
            QMessageBox.warning(self.pet_widget, "错误", f"启动脚本失败: {str(e)}")