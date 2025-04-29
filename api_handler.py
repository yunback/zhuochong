import _thread as thread
import base64
import hashlib
import hmac
from datetime import datetime
from urllib.parse import urlparse, urlencode
from time import mktime
from wsgiref.handlers import format_date_time
import ssl
from typing import Dict, Any
from common_imports import *
class APIHandler:
    API_TYPE = "xunfei"
    
    def __init__(self):
        # 配置目录
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.config_file = self.config_dir / "xunfei.json"
        self.api_key = ""
        self.api_secret = ""
        self.app_id = ""
        self.domain = "lite"
        self.spark_url = "wss://spark-api.xf-yun.com/v1.1/chat"
        self.max_history_length = 3
        self.system_prompt = "你是一个可爱的桌面宠物助手，回答要简短有趣。"
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        self.answer = ""
        self.load_config()

    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key", "")
                    self.api_secret = config.get("api_secret", "")
                    self.app_id = config.get("app_id", "")
            except Exception as e:
                QMessageBox.warning(None, "配置错误", f"加载配置失败: {str(e)}")

    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({
                    "api_key": self.api_key,
                    "api_secret": self.api_secret,
                    "app_id": self.app_id
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(None, "保存错误", f"保存配置失败: {str(e)}")

    def _update_config(self, config: Dict[str, Any]) -> None:
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.app_id = config.get("app_id", "")

    def _get_config_data(self) -> Dict[str, Any]:
        return {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "app_id": self.app_id
        }

    def validate_config(self) -> bool:
        return all([self.api_key, self.api_secret, self.app_id])

    def create_url(self) -> str:
        """生成WebSocket URL"""
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
    
        signature_origin = f"host: {urlparse(self.spark_url).netloc}\ndate: {date}\nGET {urlparse(self.spark_url).path} HTTP/1.1"
    
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
    
        signature = base64.b64encode(signature_sha).decode('utf-8')
        authorization = base64.b64encode(
            f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
            .encode('utf-8')).decode('utf-8')
    
        return f"{self.spark_url}?{urlencode({'authorization': authorization, 'date': date, 'host': urlparse(self.spark_url).netloc})}"

    def on_error(self, ws, error) -> None:
        self.answer = f"错误: {str(error)}"

    def on_close(self, ws, *args) -> None:
        pass

    def on_open(self, ws) -> None:
        def run(*args):
            ws.send(json.dumps({
                "header": {"app_id": self.app_id, "uid": "123"},
                "parameter": {"chat": {"domain": self.domain, "max_tokens": 512}},
                "payload": {"message": {"text": self.conversation_history}}
            }))
        thread.start_new_thread(run, ())

    def on_message(self, ws, message) -> None:
        data = json.loads(message)
        if data['header']['code'] != 0:
            self.answer = f"API错误: {data['header']['message']}"
            ws.close()
        else:
            self.answer += data["payload"]["choices"]["text"][0]["content"]
            if data["payload"]["choices"]["status"] == 2:
                ws.close()

    def get_response(self, user_input: str) -> str:
        print(f"[API_DEBUG] 请求内容: {user_input}")
        print(f"[API_DEBUG] 当前配置: key={self.api_key}, secret={self.api_secret}, app_id={self.app_id}")
        if not self.validate_config():
            raise Exception("请先设置完整的API配置")
        
        self.conversation_history.append({"role": "user", "content": user_input})
        if len(self.conversation_history) > 5:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-4:]
        
        self.answer = ""
        ws = websocket.WebSocketApp(
            self.create_url(),
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        if self.answer:
            self.conversation_history.append({"role": "assistant", "content": self.answer})
            return self.answer
        raise Exception("未能获取响应")