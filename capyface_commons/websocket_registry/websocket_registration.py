import requests
import json
import time
import threading
import logging

logger = logging.getLogger('capyface.websocket_registry')

class WebSocketServiceRegistration:
    def __init__(self, api_gateway_url, service_name, websocket_url, routes_config, heartbeat_interval=120):
        """
        Khởi tạo đối tượng đăng ký WebSocket service
        
        Parameters:
        -----------
        api_gateway_url : str
            URL của API Gateway
        service_name : str
            Tên duy nhất của service
        websocket_url : str
            URL WebSocket của service (ws://service:port)
        routes_config : dict
            Dict với route và yêu cầu xác thực
            Ví dụ: {"ws/chat": True, "ws/notifications": False}
        heartbeat_interval : int
            Khoảng thời gian giữa các heartbeat (giây)
        """
        self.api_gateway_url = api_gateway_url
        self.service_name = service_name
        self.websocket_url = websocket_url
        self.routes_config = routes_config
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_thread = None
        self.should_stop = False
        logger.info(f"Initialized WebSocket ServiceRegistration for {service_name} at {websocket_url}")
    
    def register(self):
        """
        Đăng ký WebSocket service với API Gateway
        """
        try:
            logger.info(f"Registering WebSocket service {self.service_name} with API Gateway at {self.api_gateway_url}")
            response = requests.post(
                f"{self.api_gateway_url}/api/register-websocket-service",
                json={
                    "service_name": self.service_name,
                    "websocket_url": self.websocket_url,
                    "routes": self.routes_config
                },
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"WebSocket service {self.service_name} registered successfully")
                return True
            else:
                logger.error(f"Failed to register WebSocket service: {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error registering WebSocket service: {str(e)}")
            return False
    
    def send_heartbeat(self):
        """
        Gửi heartbeat đến API Gateway
        """
        try:
            logger.debug(f"Sending heartbeat for WebSocket service {self.service_name}")
            response = requests.post(
                f"{self.api_gateway_url}/api/websocket-service-heartbeat",
                json={"service_name": self.service_name},
                timeout=3
            )
            
            if response.status_code != 200:
                logger.warning(f"WebSocket heartbeat failed: {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"Error sending WebSocket heartbeat: {str(e)}")
    
    def _heartbeat_worker(self):
        """
        Worker thread gửi heartbeat định kỳ
        """
        logger.info(f"Starting heartbeat worker for WebSocket service {self.service_name}")
        while not self.should_stop:
            self.send_heartbeat()
            time.sleep(self.heartbeat_interval)
    
    def start_heartbeat(self):
        """
        Bắt đầu thread gửi heartbeat
        """
        if self.heartbeat_thread is None or not self.heartbeat_thread.is_alive():
            self.should_stop = False
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()
            logger.info(f"Started heartbeat for WebSocket service {self.service_name}")
    
    def stop_heartbeat(self):
        """
        Dừng thread gửi heartbeat
        """
        logger.info(f"Stopping heartbeat for WebSocket service {self.service_name}")
        self.should_stop = True
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=1)
            logger.info(f"Stopped heartbeat for WebSocket service {self.service_name}")