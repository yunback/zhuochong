from common_imports import *
import datetime

class PetTimeDisplay(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        # 创建配置目录（如果不存在）
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.config_file = self.config_dir / "pet_config.ini"


        self.parent = parent
        self.enabled = False  # 默认关闭
        self.is_countdown_active = False
    
        # 初始化定时器
        self.timer = QTimer(parent)
        self.countdown_timer = QTimer(parent)
    
        # 其他属性
        self.time_label = None
        self.countdown_seconds = 0
        self.original_pet_size = None
        self.animation = None
    
        self.setup_time_display()
        self.parent.installEventFilter(self)

    def setup_time_display(self):
        """初始化时间显示标签"""

        self.time_label = QLabel()  # 独立窗口
        self.time_label.setWindowFlags(
            Qt.FramelessWindowHint |   # 无边框
            Qt.Tool |                 # 不在任务栏显示
            Qt.WindowStaysOnTopHint   # 始终置顶
        )
        self.time_label.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示但不获取焦点

        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 150);
                border-radius: 10px;
                padding: 5px 10px;
            }
        """)

        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self.time_label.setFont(font)
        self.time_label.setFixedSize(300, 70)

        # 初始位置
        self.update_label_position()

        # 根据 enabled 状态决定是否显示
        if self.enabled:
            self.time_label.show()
            self.time_label.raise_()  # 显示时强制置顶
            self.update_time()

        # 设置定时器
        self.timer.timeout.connect(self.update_time)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

    def set_visible(self, visible):
        """设置显示状态"""
        self.enabled = visible
        if visible:
            self.update_label_position()
            self.time_label.show()
            self.time_label.raise_()  # 显示时强制置顶
            self.update_time()
        else:
            self.time_label.hide()
        self.save_state()

    def update_time(self):
        """更新时间显示"""
        if self.enabled and not self.is_countdown_active:
            now = datetime.datetime.now()
            time_str = now.strftime("%H:%M:%S")
            date_str = now.strftime("%Y-%m-%d %A")
            self.time_label.setText(f"{date_str}\n{time_str}")

    def start_countdown(self, minutes):
        """开始倒计时"""
        self.is_countdown_active = True
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()
        
        self.countdown_seconds = minutes * 60
        self.update_countdown()
        self.countdown_timer.start(1000)

    def update_countdown(self):
        """更新倒计时显示"""
        if self.countdown_seconds > 0:
            self.countdown_seconds -= 1
            mins, secs = divmod(self.countdown_seconds, 60)
            self.time_label.setText(f"倒计时\n{mins:02d}:{secs:02d}")
        
            if self.countdown_seconds <= 10:
                self.time_label.setStyleSheet("""
                    QLabel { 
                        color: blue; 
                        background-color: rgba(0,0,0,150); 
                        border-radius: 10px; 
                        padding: 5px 10px; 
                    }
                """)
            else:
                self.time_label.setStyleSheet("""
                    QLabel { 
                        color: white; 
                        background-color: rgba(0,0,0,150); 
                        border-radius: 10px; 
                        padding: 5px 10px; 
                    }
                """)
        else:
            self.countdown_timer.stop()
            self.is_countdown_active = False
        
            # 倒计时结束显示效果
            self.time_label.setText("倒计时结束！")
            self.time_label.setStyleSheet("""
                QLabel {
                    color: red;
                    background-color: rgba(0,0,0,200);
                    border-radius: 10px;
                    padding: 5px 10px;
                    font-weight: bold;
                    font-size: 12pt;
                }
            """)
            # 3秒后恢复时间显示
            QTimer.singleShot(3000, self.restore_normal_display)

    def restore_normal_display(self):
        """恢复正常时间显示"""
        self.time_label.setStyleSheet("""
            QLabel { 
                color: white; 
                background-color: rgba(0,0,0,150); 
                border-radius: 10px; 
                padding: 5px 10px; 
            }
        """)
        self.update_time()

    def update_label_position(self):
        """更新标签位置到桌宠正上方"""
        if self.time_label:
            # 获取桌宠的全局位置
            pet_global_pos = self.parent.mapToGlobal(QPoint(0, 0))
        
            # 计算时间框位置（居中于桌宠上方）
            label_x = pet_global_pos.x() + (self.parent.width() - self.time_label.width()) // 2
            label_y = pet_global_pos.y() - self.time_label.height() - 5  # 上方5像素
        
            self.time_label.move(label_x, label_y)
            self.time_label.raise_()  # 确保置顶



    def eventFilter(self, obj, event):
        """事件过滤器，用于监听桌宠移动"""
        if obj == self.parent and event.type() == QEvent.Move:
            if self.enabled:
                self.update_label_position()
        return super().eventFilter(obj, event)

    def load_state(self):
        """从配置文件加载状态"""
        try:
            from configparser import ConfigParser
            config = ConfigParser()
            if self.config_file.exists():
                config.read(str(self.config_file))
                if config.has_section('TimeDisplay'):
                    self.enabled = config.getboolean('TimeDisplay', 'enabled', fallback=False)
        except Exception as e:
            print(f"加载配置出错: {e}")
            self.enabled = False

    def save_state(self):
        """保存状态到配置文件"""
        try:
            from configparser import ConfigParser
            config = ConfigParser()
            config['TimeDisplay'] = {'enabled': str(self.enabled)}
            
            with open(str(self.config_file), 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"保存配置出错: {e}")

    def toggle_time_display(self, checked):
        """切换显示状态"""
        self.set_visible(checked)

    def ensure_visible(self):
        """确保时间框可见（防止切换应用时消失）"""
        if self.enabled and self.time_label:
            self.time_label.show()
            self.time_label.raise_()
            self.update_label_position()
