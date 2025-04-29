import sys
import os

def resource_path(relative_path):
    """ 获取打包后资源的绝对路径 """
    if hasattr(sys, '_MEIPASS'):
        # 打包后的情况
        base_path = sys._MEIPASS
    else:
        # 开发时的情况
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

from pet_animations import PetAnimations
from api_selector import APISelector
from pet_input import PetInput
from pet_notes import PetNotes
from pet_clipboard import PetClipboard
from pet_time_display import PetTimeDisplay
from english_page import PetWebBrowser
from app_open import AppLauncher
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from common_imports import *

from enum import Enum, auto
class PetState(Enum):
    IDLE = auto()      # 空闲状态
    CLICKED = auto()   # 被点击状态
    RESTING = auto()   # 休息提醒状态
    THINKING = auto()  # 思考状态

class RestReminderState(Enum):
    DISABLED = auto()  # 休息提醒关闭
    ENABLED = auto()   # 休息提醒开启

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        # 初始化变量
        self.pet1 = []  # 存储GIF动画路径
        self.condition = 0  # 宠物状态
        self.rest_open = 1 # 休息提醒状态
        self.state = PetState.IDLE
        self.state = PetState.IDLE
        self.rest_reminder = RestReminderState.ENABLED

        self.is_active = True
        self.init_system_tray()

        self.saved_states = {}
    
        # 添加动画绑定字典 (MOVED THIS BEFORE PetAnimations INIT)
        self.animation_bindings = {
            "idle": resource_path(os.path.join("pikaqiu", "idle.gif")),
            "phonewalkright": resource_path(os.path.join("pikaqiu", "phonewalkright.gif")),
            "phonewalkleft": resource_path(os.path.join("pikaqiu", "phonewalkleft.gif")),
            "walkleft": resource_path(os.path.join("pikaqiu", "walkleft.gif")),
            "walkright": resource_path(os.path.join("pikaqiu", "walkright.gif")),
            "jump": resource_path(os.path.join("pikaqiu", "jump.gif")),
            "touch": resource_path(os.path.join("pikaqiu", "touch.gif")),
            "shake": resource_path(os.path.join("pikaqiu", "shake.gif"))
        }
        self.current_animation = "idle"
    
        # 初始化动画系统 
        self.animations = PetAnimations(self)
    
        # 先初始化UI
        self.init_ui()
    
        # 然后初始化时间显示
        self.time_display = PetTimeDisplay(self)

        # 添加动画控制标志
        self.animations_enabled = True  # 默认开启动画
    
        # 初始化功能模块
        self.api_selector = APISelector(self)
        self.api_handler = None
        self.setup_api_handler()
        self.notes = PetNotes(self)
        self.clipboard = PetClipboard(self)
        self.web_browser = None  # 延迟初始化浏览器 
        self.app_launcher = AppLauncher(self)

        self.screen_geometry = QApplication.desktop().availableGeometry()
        self.setMaximumSize(self.screen_geometry.width(), self.screen_geometry.height())

        # 动画定时器
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.random_animation)
        random_interval = random.randint(5000, 15000)
        print(f"随机动画时间：{random_interval}")
        self.animation_timer.start(random_interval)
        self.animations = PetAnimations(self) 

        # 动画保活定时器（每10秒检查一次）
        self.animation_keeper = QTimer(self)
        self.animation_keeper.timeout.connect(self._check_animation_alive)
        self.animation_keeper.start(10000)
    
        # 添加问候定时器初始化
        self.greeting_timer = QTimer(self)
        self.greeting_timer.timeout.connect(self.show_greeting)
        random_greeting = random.randint(500, 1000)+random_interval
        print(f"随机问候语时间：{random_greeting}")
        self.greeting_timer.start(random_greeting)  # 可以注释这行来默认关闭
    
        self._enable_rest_reminder()
        self.show()
        

    def init_ui(self):
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)        
        self.setAutoFillBackground(False)
    
        # 设置宠物图像 - 使用GIF动画或粉色圆球
        gif_path = resource_path(os.path.join("pikaqiu", "idle.gif"))
    
        self.pet_image = QLabel(self)
    
        # 检查GIF文件是否存在
        if os.path.exists(gif_path):
            print(f"GIF路径: {gif_path}")
            self.movie = QMovie(gif_path)
            self.movie.setCacheMode(QMovie.CacheAll)
        
            if self.movie.isValid():
                self.movie.setScaledSize(QSize(200, 200))
                self.pet_image.setMovie(self.movie)
                self.movie.start()
            else:
                print("错误: 无效的GIF文件")
                self._setup_fallback_circle()
        else:
            print(f"GIF文件未找到: {gif_path}")
            self._setup_fallback_circle()
    
        # 确保窗口透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        # 加载动画资源时改为使用动画绑定字典
        self.pet1 = list(self.animation_bindings.values())
    
        # 设置初始动画
        self.play_animation("idle")
    
        # 其余初始化代码保持不变...
        # "休息一下"时间显示
        self.show_time_rest = QLabel(self)
        self.show_time_rest.setStyleSheet("font:15pt '楷体';border-width: 1px;color:blue;")
    
        # 初始化输入框组件
        self.pet_input = PetInput(self)
        self.pet_input.input_box.returnPressed.connect(self.handle_input)
    
        # 布局设置
        layout = QVBoxLayout()
        layout.addWidget(self.pet_image)
        layout.addWidget(self.show_time_rest)
        layout.addLayout(self.pet_input.setup_layout())
        self.setLayout(layout)
    
        # 设置窗口初始大小
        self.resize(300, 300)
        self.randomPosition()


    def save_settings(self):
        """保存设置到配置文件"""
        settings = QSettings("YourCompany", "DesktopPet")
        settings.setValue("rest_reminder", self.rest_reminder == RestReminderState.ENABLED)
        settings.setValue("animations_enabled", self.animations_enabled)

    def load_settings(self):
        """从配置文件加载设置"""
        settings = QSettings("YourCompany", "DesktopPet")
        if settings.value("rest_reminder", False, type=bool):
            self._enable_rest_reminder()
        self.animations_enabled = settings.value("animations_enabled", True, type=bool)

    def _setup_fallback_circle(self):
        """设置粉色圆球作为备用显示"""
        self.pet_image.setStyleSheet("""
            background-color: pink;
            border-radius: 100px;
            border: 2px solid white;
            min-width: 200px;
            min-height: 200px;
            max-width: 200px;
            max-height: 200px;
        """)
        # 禁用动画功能
        self.animations_enabled = False
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()


    def play_animation(self, anim_name):
        """委托给动画子系统"""
        self.animations.play(anim_name)

    def randomPosition(self):
        """完全随机的初始位置"""
        screen_geo = QDesktopWidget().screenGeometry()
        self.move(
            random.randint(0, screen_geo.width() - self.width()),
            random.randint(0, screen_geo.height() - self.height())
        )

    def random_animation(self):
        """随机动画触发"""
        if self.state == PetState.IDLE and self.animations_enabled:
            self.animations.random_animation()

       
    def open_web_browser(self):
        """打开网页浏览器"""
        if not hasattr(self, 'web_browser') or not self.web_browser:
            self.web_browser = PetWebBrowser(self)
        self.web_browser.show()
        self.web_browser.raise_() 
           
    def mousePressEvent(self, event):
        """重写鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 通知动画系统处理点击中断
            if hasattr(self, 'animations'):
                self.animations.handle_click_interrupt()
            
            # 正常处理拖动逻辑
            self.state = PetState.CLICKED
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.is_dragging = True
            event.accept()

    def mouseMoveEvent(self, event):
        """重写鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.is_dragging:
            new_pos = event.globalPos() - self.drag_pos
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """重写鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.state = PetState.IDLE  # 明确重置状态
        
            # 确保动画系统知道拖动结束
            if hasattr(self, 'animations'):
                self.animations._is_animating = False
                self.animations._stop_current_animations()
            
                # 延迟一点再触发随机动画，避免冲突
                QTimer.singleShot(300, self.animations.random_animation)
            
            event.accept()


    def _get_center_position(self):
        """获取屏幕中心位置"""
        screen = QApplication.desktop().availableGeometry()
        return QPoint(
            screen.width()//2 - self.width()//2,
            screen.height()//2 - self.height()//2
        )

    def mouseDoubleClickEvent(self, event):
        """重写鼠标点击事件"""
        if event.pos().y() < self.pet_image.height():
            if self.animations_enabled:  # 如果动画是开启状态，则暂停
                # 停止所有动画
                self.animation_timer.stop()
                if hasattr(self, 'animations'):
                    self.animations._stop_current_animations()
            
                # 播放抖动动画
                self.play_animation("shake")
            
                # 显示输入框
                self.pet_input.toggle_input()
            
                # 禁用动画标志
                self.animations_enabled = False
            else:  # 如果动画是关闭状态，则恢复
                # 恢复动画标志
                self.animations_enabled = True
            
                # 恢复动画系统
                random_interval = random.randint(5000, 15000)
                print(f"随机动画时间：{random_interval}")
                self.animation_timer.start(random_interval)
                self.play_animation("idle")
            
                # 隐藏输入框
                self.pet_input.toggle_input()
    
    def handle_input(self):
        """处理输入框的回车事件"""
        text = self.pet_input.input_box.text()
        if text:
            self.pet_input.add_user_input(text)  # 添加到对话历史
            self._process_chat(text)
            self.pet_input.input_box.clear()  #处理输入框的回车事件

    #处理窗口大小改变时的事件
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'time_display'):
            self.time_display.update_label_position()

    # 添加事件过滤器支持
    def eventFilter(self, obj, event):
        if event.type() == QEvent.WindowActivate:
            if hasattr(self, 'time_display'):
                self.time_display.ensure_visible()
        return super().eventFilter(obj, event)

    def toggle_time_display(self, checked):
        """切换时间显示状态"""
        self.time_display.set_visible(checked)

    def start_countdown(self, minutes):
        """开始倒计时"""
        if hasattr(self, 'time_display'):
            self.time_display.start_countdown(minutes)
            QMessageBox.information(self, "倒计时开始", 
                                 f"已设置{minutes}分钟倒计时",
                                 QMessageBox.Ok)

    def set_custom_countdown(self):
        """设置自定义倒计时时间"""
        minutes, ok = QInputDialog.getInt(
            self, "设置倒计时", 
            "请输入倒计时分钟数:", 
            min=1, max=240, step=1
        )
        if ok and minutes > 0:
            self.start_countdown(minutes)
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        # 添加原有菜单项
        software_menu = menu.addMenu("软件")
        self.app_launcher.create_app_menu(software_menu)

        set_api_action = menu.addAction("设置API配置")
        select_api_action = menu.addAction("选择API供应商")
        set_api_action.triggered.connect(self.check_api_key)
        select_api_action.triggered.connect(self.select_api_provider)

        notes_action = menu.addAction("笔记")
        notes_action.triggered.connect(
            lambda: self.notes.show_notes_menu(event)  # 传递事件对象
        )

        clipboard_action = menu.addAction("剪贴板")
        clipboard_action.triggered.connect(
            lambda: self.clipboard.show_clipboard_menu(event)  # 传递事件对象
        )

        # 时间显示菜单
        time_action = QAction("显示/隐藏时间,倒计时", menu)
        time_action.setCheckable(True)
        time_action.setChecked(self.time_display.enabled)
        time_action.triggered.connect(self.toggle_time_display)
        menu.addAction(time_action)

        # 添加倒计时菜单
        timer_menu = menu.addMenu("倒计时提醒")
        for minutes in [1,5, 10, 15, 20, 30, 45, 60]:
            action = timer_menu.addAction(f"{minutes}分钟")
            action.triggered.connect(
                lambda checked, m=minutes: self.start_countdown(m)
            )
        custom_action = timer_menu.addAction("自定义时间...")
        custom_action.triggered.connect(self.set_custom_countdown)

        # 添加网页浏览菜单项
        browser_action = menu.addAction("浏览器")
        browser_action.triggered.connect(self.open_web_browser)

        # 添加GIF动画控制菜单
        animation_action = QAction("开关动画效果", menu)
        animation_action.setCheckable(True)
        animation_action.setChecked(self.animations_enabled)
        animation_action.triggered.connect(self.toggle_animations)
        menu.addAction(animation_action)

        show_action = QAction("显示/隐藏随机语句", menu)
        show_action.setCheckable(True)
        show_action.setChecked(self.greeting_timer.isActive())
        show_action.triggered.connect(self.toggle_greeting_display)
        menu.addAction(show_action)

        rest_action = menu.addAction("休息提醒")
        rest_action.setCheckable(True)
        rest_action.setChecked(self.rest_reminder == RestReminderState.ENABLED)
        rest_action.triggered.connect(self.toggle_rest_reminder)

        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self.quit_application) 

        menu.exec_(event.globalPos())

    def toggle_rest_reminder(self, checked):
        """切换休息提醒状态"""
        if checked:
            self._enable_rest_reminder()
        else:
            self._disable_rest_reminder()
    
        # 更新菜单项的勾选状态
        sender = self.sender()  # 获取触发信号的菜单项
        if sender:
            sender.setChecked(self.rest_reminder == RestReminderState.ENABLED)

    def _enable_rest_reminder(self):
        self.rest_reminder = RestReminderState.ENABLED
        if not hasattr(self, 'timer_rest'):
            self.timer_rest = QTimer(self)
        self.timer_rest.timeout.connect(self.relax)
        self.timer_rest.start(1800000)  # 30分钟

    def relax(self):
        if self.is_rest_reminder_active:
            return  # 如果提醒已经激活，则不再重复触发
    
        # 暂停定时器
        self.timer_rest.stop()
        self.is_rest_reminder_active = True
    
        # 创建消息框
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("休息提醒")
        msg_box.setText("<h3>您已经工作30分钟了！</h3>")
        msg_box.setInformativeText("建议站起来活动一下，放松眼睛~\n\n点击OK后，30分钟后会再次提醒")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setIcon(QMessageBox.NoIcon)
    
        # 添加图片
        rest_image_path = resource_path(os.path.join("pikaqiu", "relax.png"))
        if os.path.exists(rest_image_path):
            pixmap = QPixmap(rest_image_path)
            pixmap = pixmap.scaled(1000,1000, Qt.KeepAspectRatio)
            msg_box.setIconPixmap(pixmap)
    
        # 确保弹窗置顶
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
    
        # 播放提醒动画
        self.play_animation("shake")
    
        # 显示弹窗并等待用户响应
        msg_box.exec_()
    
        # 用户点击OK后
        self.is_rest_reminder_active = False
        self.timer_rest.start(1800000)  # 重新启动30分钟定时器

    def _disable_rest_reminder(self):
        self.rest_reminder = RestReminderState.DISABLED
        if hasattr(self, 'timer_rest'):
            self.timer_rest.stop()

    def check_api_key(self):
        """通用的API配置对话框，根据类型标识自动适配"""
        if not self.api_handler:
            QMessageBox.warning(self, "错误", "API处理器未初始化")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"{self.api_handler.API_TYPE.upper()} 配置")
        layout = QFormLayout(dialog)

        # 通用字段
        api_key_edit = QLineEdit(getattr(self.api_handler, "api_key", ""))
        layout.addRow("API Key:", api_key_edit)

        # 根据类型标识显示不同字段
        if self.api_handler.API_TYPE == "xunfei":
            api_secret_edit = QLineEdit(getattr(self.api_handler, "api_secret", ""))
            app_id_edit = QLineEdit(getattr(self.api_handler, "app_id", ""))
            layout.addRow("API Secret:", api_secret_edit)
            layout.addRow("App ID:", app_id_edit)
        elif self.api_handler.API_TYPE == "openrouter":
            # 添加模型下拉选择框
            model_combo = QComboBox()
        
            # 如果已有模型配置，设为默认值
            current_model = getattr(self.api_handler, "model", "")
            if current_model:
                model_combo.addItem(current_model, current_model)
        
            # 添加"加载模型"按钮
            load_models_btn = QPushButton("加载可用模型")
            load_models_btn.clicked.connect(lambda: self._load_models(api_key_edit.text(), model_combo))
            layout.addRow("Model:", model_combo)
            layout.addRow(load_models_btn)  # 将按钮单独放一行

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        if dialog.exec_() == QDialog.Accepted:
            # 设置通用字段
            self.api_handler.api_key = api_key_edit.text().strip()
        
            # 设置特定字段
            if self.api_handler.API_TYPE == "xunfei":
                self.api_handler.api_secret = api_secret_edit.text().strip()
                self.api_handler.app_id = app_id_edit.text().strip()
            elif self.api_handler.API_TYPE == "openrouter":
                self.api_handler.model = model_combo.currentData()  # 获取选中的模型
        
            self.api_handler.save_config()
            QMessageBox.information(self, "成功", "配置已保存！")

    def _load_models(self, api_key: str, combo_box: QComboBox):
        """加载可用模型到下拉框"""
        if not api_key:
            QMessageBox.warning(self, "错误", "请先输入API Key")
            return
    
        try:
            # 临时设置API Key以获取模型列表
            self.api_handler.api_key = api_key
            models = self.api_handler.get_available_models()
        
            if not models:
                QMessageBox.warning(self, "警告", "未获取到可用模型")
                return
        
            combo_box.clear()
            for model in models:
                combo_box.addItem(model, model)  # 显示名称和实际值一致
        
            QMessageBox.information(self, "成功", f"已加载 {len(models)} 个模型")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模型失败: {str(e)}")

    def setup_api_handler(self, handler_type="api_handler"):
        """根据类型设置API处理器"""
        try:
            if handler_type == "api_handler":
                from api_handler import APIHandler
                self.api_handler = APIHandler()
            elif handler_type == "api_handler2":
                from api_handler2 import APIHandler
                self.api_handler = APIHandler()
                # 如果配置有效，不自动弹出配置对话框
                if self.api_handler.validate_config():
                    self.show_api_tooltip()
                    return
            else:
                raise ValueError(f"未知的API处理器类型: {handler_type}")
        
            self.show_api_tooltip()
        
            # 只有配置无效时才弹出配置对话框
            if not self.api_handler.validate_config():
                self.check_api_key()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载API处理器: {str(e)}")
            self.api_handler = None

    def select_api_provider(self):
        """选择API供应商"""
        selected_handler = self.api_selector.show_selection_dialog()
        if selected_handler:  # 这里现在直接收到的是"api_handler"或"api_handler2"
            self.setup_api_handler(selected_handler)

    def show_api_tooltip(self) -> None:
        """显示当前使用的API类型提示"""
        if self.api_handler:
            QToolTip.showText(
                self.mapToGlobal(QPoint(self.width()//2, 0)),
                f"当前API: {self.api_handler.API_TYPE}",
                self,
                QRect(0, 0, self.width(), self.height()),
                2000
            )

    def start_chat(self, user_input: Optional[str] = None) -> None:
        """开始聊天对话"""
        if not user_input:
            user_input, ok = QInputDialog.getText(
                self, "和桌宠聊天", "你想说什么:", QLineEdit.Normal
            )
            if not ok or not user_input:
                return
    
        self._process_chat(user_input)  # 调用处理聊天的方法

    def _process_chat(self, user_input):
        """使用线程池处理聊天请求"""
        try:
            print(f"[DEBUG] 开始处理输入: {user_input}")
            self.set_thinking_state(True)
    
            # 对话时暂停动画
            was_animation_enabled = getattr(self, 'animations_enabled', False)  # 安全获取属性
            if was_animation_enabled:
                self.toggle_animations(False)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.api_handler.get_response, user_input)
                try:
                    response = future.result(timeout=15)
                    print(f"[DEBUG] 获取到响应: {response}")
                    if response:
                        self.show_response(response)
                    else:
                        print("[ERROR] 空响应")
                        self.show_error("未能获取响应")
                except TimeoutError:
                    print("[ERROR] 请求超时")
                    self.show_error("请求超时，请重试")
                except Exception as e:
                    print(f"[ERROR] 请求异常: {str(e)}")
                    self.show_error(str(e))
        except Exception as e:
            print(f"[ERROR] 处理聊天异常: {str(e)}")
        finally:
            self.set_thinking_state(False)
            # 恢复动画状态
            if was_animation_enabled:  # 现在这个变量总是有值
                self.toggle_animations(True)

    def start_bounce_animation(self):
        """委托给动画子系统执行弹跳动画"""
        if hasattr(self, 'animations') and self.animations_enabled:
            self.animations.start_bounce_animation()

    def toggle_animations(self, checked):
        """切换动画效果"""
        self.animations_enabled = checked
        if checked:

            self.animation_timer.start(5000)  # 改为2秒触发一次随机动画

            self.play_animation("idle")
            QToolTip.showText(
                self.mapToGlobal(QPoint(self.width()//2, 0)),
                "已开启动画效果",
                self,
                QRect(0, 0, self.width(), self.height()),
                1500
            )
        else:
            self.animation_timer.stop()
            if hasattr(self, 'animations'):
                self.animations._stop_current_animations()
            QToolTip.showText(
                self.mapToGlobal(QPoint(self.width()//2, 0)),
                "已关闭动画效果",
                self,
                QRect(0, 0, self.width(), self.height()),
                1500
            )

    def set_thinking_state(self, is_thinking):
        """统一设置思考状态"""
        if is_thinking:
            self.show_thinking_animation()
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            self.show_normal_animation()
            QApplication.restoreOverrideCursor()  #统一设置思考状态
        
    def show_response(self, response):
        """显示响应在文本框下方"""
        self.pet_input.show_response(response)
        if hasattr(self, 'start_bounce_animation'):
            self.start_bounce_animation()

    def show_greeting(self):
        """显示问候语，气泡固定在桌宠上方"""
        greeting = self.animations.get_random_greeting()  
        bubble_pos = self._calculate_bubble_position()
    
        QToolTip.showText(
            bubble_pos,
            greeting,
            self,
            QRect(0, 0, self.width(), self.height()),
            3000  # 显示3秒
        )

    def toggle_greeting_display(self, checked):
        """切换随机语句的显示状态"""
        if checked:
            # 如果勾选了，启动定时器显示随机语句
            self.start_greeting_timer()
            QToolTip.showText(
                self.mapToGlobal(QPoint(self.width()//2, 0)),
                "已开启随机语句显示",
                self,
                QRect(0, 0, self.width(), self.height()),
                1500
            )
        else:
            # 如果取消勾选，停止定时器
            self.stop_greeting_timer()
            QToolTip.showText(
                self.mapToGlobal(QPoint(self.width()//2, 0)),
                "已关闭随机语句显示",
                self,
                QRect(0, 0, self.width(), self.height()),
                1500
            )

    def start_greeting_timer(self, interval=10000):
        """启动随机语句定时器"""
        if not hasattr(self, 'greeting_timer') or not self.greeting_timer:
            self.greeting_timer = QTimer(self)
            self.greeting_timer.timeout.connect(self.show_greeting)
        self.greeting_timer.start(interval)

    def stop_greeting_timer(self):
        """停止随机语句定时器"""
        if hasattr(self, 'greeting_timer') and self.greeting_timer:
            self.greeting_timer.stop()    
    
    def show_thinking_animation(self):
        """显示思考提示，气泡固定在桌宠上方"""
        bubble_pos = self._calculate_bubble_position()
    
        # 改变外观表示正在思考
        self.pet_image.setStyleSheet("""
            background-color: lightblue; 
            border-radius: 50px;
            border: 10px solid white;
        """)
    
        QToolTip.showText(
            bubble_pos,
            "思考中...",
            self,
            QRect(0, 0, self.width(), self.height()),
            3000
        )

    def _calculate_bubble_position(self):
        """计算气泡位置，确保不会超出屏幕"""
        # 气泡显示在桌宠正上方
        bubble_pos = self.mapToGlobal(QPoint(self.width() // 2, -10))
    
        # 确保气泡不会超出屏幕顶部
        screen_top = QApplication.desktop().availableGeometry().top()
        if bubble_pos.y() < screen_top + 10:  # 保留10px边距
            bubble_pos.setY(screen_top + 10)
    
        return bubble_pos

    def _ensure_in_screen(self, pos):
        """确保位置在屏幕范围内"""
        margin = 20  # 与 pet_animations.py 中保持一致
        x = max(margin, min(pos.x(), self.screen_geometry.width() - self.width() - margin))
        y = max(margin, min(pos.y(), self.screen_geometry.height() - self.height() - margin))
        return QPoint(x, y)

    def _stop_current_animations(self):
        """停止当前所有动画"""
        for anim in self._current_animations:
            anim.stop()
            anim.deleteLater()
        self._current_animations.clear()
        self._is_animating = False
        # 停止当前电影
        if hasattr(self, 'current_movie') and self.current_movie:
            self.current_movie.stop()
        # 强制设置为idle状态
        self.play("idle")

    def show_normal_animation(self):
        if hasattr(self, 'pet_image'):
            if self.pet_image.pixmap() and not self.pet_image.pixmap().isNull():
                self.pet_image.setStyleSheet("")
            else:
                self.pet_image.setStyleSheet("")

    def _smooth_return(self, target_pos):
        """添加视觉提示的返回动画"""
        # 创建提示气泡
        bubble = QLabel(self.pet)
        bubble.setText("带我回来啦~")
        bubble.setStyleSheet("""
            background-color: rgba(255,255,255,150);
            border-radius: 10px;
            padding: 5px;
            color: black;
        """)
        bubble.move(10, -30)
        bubble.show()
    
        # 动画完成后移除气泡
        QTimer.singleShot(1500, bubble.deleteLater)

    def _check_animation_alive(self):
        """确保动画系统持续运行"""
        if not self.pet_image.movie() or self.pet_image.movie().state() != QMovie.Running:
            print("动画中断，正在恢复...")
            self.animations.play(self.animations.current_anim if hasattr(self.animations, 'current_anim') else "idle")

    def _smooth_return(self, target_pos):
        """平滑回到可视区域"""
        self._is_animating = True
    
        # 淡出+移动+淡入动画组合
        group = QParallelAnimationGroup()
    
        # 移动动画
        move_anim = QPropertyAnimation(self, b"pos")
        move_anim.setDuration(1000)
        move_anim.setEasingCurve(QEasingCurve.InOutQuad)
        move_anim.setStartValue(self.pos())
        move_anim.setEndValue(target_pos)
    
        # 透明度动画（闪烁效果）
        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(1000)
        opacity_anim.setKeyValues([(0.0, 0.7), (0.5, 0.3), (1.0, 1.0)])
    
        group.addAnimation(move_anim)
        group.addAnimation(opacity_anim)
        group.finished.connect(lambda: self.play_animation("idle"))
        group.start()

    def reset_animation_system(self):
        """完全重置动画系统"""
        self.animations._is_animating = False
        self.animations._stop_current_animations()
        self.pet_image.setMovie(None)
        # 重新初始化
        self.animations._preload_animations()
        self.animations.play("idle")


    def save_current_states(self):
        """保存当前所有可勾选的状态"""
        self.saved_states = {
            'rest_reminder': self.rest_reminder == RestReminderState.ENABLED,
            'animations_enabled': self.animations_enabled,
            'greeting_timer': self.greeting_timer.isActive() if hasattr(self, 'greeting_timer') else False,
            'time_display': self.time_display.enabled if hasattr(self, 'time_display') else False,
            # 添加其他需要保存的状态...
        }

    def restore_saved_states(self):
        """恢复之前保存的状态"""
        if not self.saved_states:
            return
    
        # 恢复动画状态
        self.animations_enabled = self.saved_states.get('animations_enabled', True)
        self.toggle_animations(self.animations_enabled)
    
        # 恢复休息提醒
        if self.saved_states.get('rest_reminder', False):
            self._enable_rest_reminder()
        else:
            self._disable_rest_reminder()
    
        # 恢复随机语句
        if self.saved_states.get('greeting_timer', False):
            self.start_greeting_timer()
        else:
            self.stop_greeting_timer()
    
        # 恢复时间显示
        if hasattr(self, 'time_display'):
            self.time_display.set_visible(self.saved_states.get('time_display', False))

    def init_system_tray(self):
        """初始化系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
    
        # 设置托盘图标
        icon_path = resource_path(os.path.join("pikaqiu", "tray_icon.png"))
    
        # 确保图标文件存在且有效
        if os.path.exists(icon_path):
            try:
                tray_icon = QIcon(icon_path)
                if not tray_icon.isNull():  # 检查图标是否有效
                    self.tray_icon.setIcon(tray_icon)
                else:
                    raise ValueError("无效的图标文件")
            except Exception as e:
                print(f"加载自定义托盘图标失败: {e}")
                self.tray_icon.setIcon(QApplication.style().standardIcon(QStyle.SP_ComputerIcon))
        else:
            print(f"托盘图标文件未找到: {icon_path}")
            self.tray_icon.setIcon(QApplication.style().standardIcon(QStyle.SP_ComputerIcon))
    
        # 创建托盘菜单
        tray_menu = QMenu()
    
        # 显示/隐藏切换动作
        self.toggle_action = QAction("隐藏桌宠", self)
        self.toggle_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(self.toggle_action)
    
        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.cleanup_and_quit)
        tray_menu.addAction(exit_action)
    
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
        # 双击图标切换显示
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def toggle_visibility(self):
        """切换显示/隐藏状态并保存状态"""
        if self.isVisible():
            # 隐藏前保存当前所有状态
            self.save_current_states()
            self.set_pet_active(False)  # 冻结所有功能
            self.hide()
            self.toggle_action.setText("显示桌宠")
        else:
            self.show()
            # 显示时恢复状态（延迟确保窗口已显示）
            QTimer.singleShot(100, self.restore_saved_states)
            self.toggle_action.setText("隐藏桌宠")
            self.raise_()

    def on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件（如双击）"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_visibility()

    def quit_application(self):
        """完全退出应用程序"""
        # 清理资源
        self.set_pet_active(False)
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()  # 隐藏托盘图标
    
        # 确保所有窗口关闭
        QApplication.closeAllWindows()
        QApplication.quit()



    def set_pet_active(self, active: bool):
        """统一启用/禁用所有功能（核心方法）"""
        self.is_active = active
    
        # 1. 控制动画系统
        if hasattr(self, 'movie') and self.movie:
            if active:
                self.movie.start()  # 恢复GIF播放
                self.animation_timer.start(5000)  # 5秒随机动画
            else:
                self.movie.setPaused(True)  # 暂停GIF（保留当前帧）
                self.animation_timer.stop()
    
        # 2. 控制休息提醒
        if hasattr(self, 'timer_rest'):
            if active and self.rest_reminder == RestReminderState.ENABLED:
                self.timer_rest.start(1800000)  # 30分钟
            else:
                self.timer_rest.stop()
    
        # 3. 控制随机语句
        if hasattr(self, 'greeting_timer'):
            if active and self.greeting_timer.isActive():
                self.greeting_timer.start()
            else:
                self.greeting_timer.stop()
    
        # 4. 强制隐藏所有弹出内容
        QToolTip.hideText()
        if hasattr(self, 'time_display'):
            self.time_display.set_visible(active)



    def closeEvent(self, event):
        """点击关闭按钮时隐藏到托盘"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.set_pet_active(False)
            self.hide()
            event.ignore()
        else:
            self.cleanup_and_quit()

    def showEvent(self, event):
        """窗口显示时确保功能恢复"""
        if not self.is_active:
            QTimer.singleShot(50, lambda: self.set_pet_active(True))  # 延迟50ms避免卡顿
        super().showEvent(event)

    def cleanup_and_quit(self):
        """彻底退出时的清理"""
        self.set_pet_active(False)
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()

