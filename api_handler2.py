from typing import List, Dict, Any
from common_imports import *
from api_selector import APIHandlerBase
from datetime import datetime

class APIHandler(APIHandlerBase):
    API_TYPE = "openrouter"
    def __init__(self):
        super().__init__()
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.config_file = self.config_dir / "openrouter.json"
        self.api_key = ""
        self.model = ""
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.load_config()  # 确保初始化时加载配置

    def validate_config(self) -> bool:
        # 检查配置是否有效而不仅仅是存在
        if not all([self.api_key, self.model]):
            return False
            
        # 简单验证API Key格式（至少20字符）
        if len(self.api_key) < 20:
            return False
            
        return True

    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key", "")
                    self.model = config.get("model", "")

            except Exception as e:
                QMessageBox.warning(None, "配置错误", f"加载配置失败: {str(e)}")

    def _update_config(self, config: Dict[str, Any]) -> None:
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "")

    def _get_config_data(self) -> Dict[str, Any]:
        return {
            "api_key": self.api_key,
            "model": self.model
        }

    def validate_config(self) -> bool:
        return all([self.api_key, self.model])

    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
    
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                timeout=10
            )
        
            if response.status_code == 200:
                models = response.json().get("data", [])
                return [
                    model["id"] for model in models 
                    if "chat" in model.get("description", "").lower() or 
                       "gpt" in model["id"].lower() or 
                       "claude" in model["id"].lower()
                ]
            raise Exception(f"获取模型列表失败: {response.status_code} - {response.text}")
        except Exception as e:
            QMessageBox.warning(None, "错误", f"获取模型列表时出错: {str(e)}")
            return []

    def get_response(self, user_input: str) -> str:
        print(f"[API_DEBUG] 请求内容: {user_input}")
        print(f"[API_DEBUG] 当前配置: key={self.api_key}, model={self.model}")
        """获取AI响应"""
        self.conversation_history.append({"role": "user", "content": user_input})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": self.conversation_history,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=15
            )
            response.raise_for_status()
            
            ai_response = response.json()["choices"][0]["message"]["content"]
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
        except Exception as e:
            raise Exception(f"API错误: {str(e)}")