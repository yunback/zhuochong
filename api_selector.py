from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from common_imports import *

class APISelector:
    def __init__(self, parent=None):
        self.parent = parent
        self.api_handlers = {
            "讯飞星火Lite": "api_handler",
            "OpenRouter": "api_handler2"
        }
        self.last_selected = None  # 记录上次选择

    def show_selection_dialog(self):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("选择API供应商")
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("请选择API供应商:"))
        
        combo = QComboBox()
        for name, module_name in self.api_handlers.items():
            combo.addItem(name, module_name)
        
        # 设置默认选中项
        if self.last_selected:
            index = combo.findData(self.last_selected)
            if index >= 0:
                combo.setCurrentIndex(index)
        
        layout.addWidget(combo)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            self.last_selected = combo.currentData()
            return self.last_selected
        return None

class APIHandlerBase(ABC):
    """API处理器的基类，定义统一接口"""
    def __init__(self, config_file: Optional[str] = None):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        default_config_file = f"config_{self.API_TYPE}.json"
        self.config_file = self.config_dir / (config_file or default_config_file)
        self.conversation_history = [
            {"role": "system", "content": "你是一个可爱的桌面宠物助手，回答要简短有趣。"}
        ]
        self.load_config()
    
    @property
    @abstractmethod
    def API_TYPE(self) -> str:
        """返回API类型标识"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否完整"""
        pass
    
    @abstractmethod
    def get_response(self, user_input: str) -> str:
        """获取AI响应"""
        pass
    
    def load_config(self) -> None:
        """从配置文件加载配置"""
        if not os.path.exists(self.config_file):
            return
            
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                self._update_config(config)
        except Exception as e:
            QMessageBox.warning(None, "配置错误", f"加载配置文件失败: {str(e)}")
    
    @abstractmethod
    def _update_config(self, config: Dict[str, Any]) -> None:
        """更新配置参数"""
        pass
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._get_config_data(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(None, "保存错误", f"保存配置失败: {str(e)}")
    
    @abstractmethod
    def _get_config_data(self) -> Dict[str, Any]:
        """获取需要保存的配置数据"""
        pass
    
    def close(self) -> None:
        """关闭时清理资源"""
        pass