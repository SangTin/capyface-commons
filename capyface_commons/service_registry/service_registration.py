import requests
import json
import time
import threading
import logging

# Thiết lập logger
logger = logging.getLogger('capyface.service_registry')

class ServiceRegistration:
    def __init__(self, api_gateway_url, service_name, service_url, routes_config, default_auth=True, heartbeat_interval=120):
        """
        Khởi tạo đối tượng đăng ký service
        
        Parameters:
        -----------
        api_gateway_url : str
            URL của API Gateway
        service_name : str
            Tên duy nhất của service
        service_url : str
            URL cơ sở của service (ví dụ: http://user-service:8000)
        routes_config : list or dict
            - List: Danh sách các route đơn giản, sẽ sử dụng default_auth
              Ví dụ: ["api/users", "api/posts"]
            - Dict: Dict với route và yêu cầu xác thực
              Ví dụ: {"api/users": True, "api/public": False}
        default_auth : bool
            Giá trị xác thực mặc định nếu routes_config là list
        heartbeat_interval : int
            Khoảng thời gian giữa các heartbeat (giây)
        """
        self.api_gateway_url = api_gateway_url
        self.service_name = service_name
        self.service_url = service_url
        self.routes_config = routes_config
        self.default_auth = default_auth
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_thread = None
        self.should_stop = False
        logger.info(f"Initialized ServiceRegistration for {service_name} at {service_url}")
    
    def register(self):
        """
        Đăng ký service với API Gateway
        """
        try:
            logger.info(f"Registering service {self.service_name} with API Gateway at {self.api_gateway_url}")
            response = requests.post(
                f"{self.api_gateway_url}/api/register-service",
                json={
                    "service_name": self.service_name,
                    "service_url": self.service_url,
                    "routes": self.routes_config,
                    "default_auth": self.default_auth
                },
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Service {self.service_name} registered successfully")
                return True
            else:
                logger.error(f"Failed to register service: {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error registering service: {str(e)}")
            return False
    
    def send_heartbeat(self):
        """
        Gửi heartbeat đến API Gateway
        """
        try:
            logger.debug(f"Sending heartbeat for service {self.service_name}")
            response = requests.post(
                f"{self.api_gateway_url}/api/service-heartbeat",
                json={"service_name": self.service_name},
                timeout=3
            )
            
            if response.status_code != 200:
                logger.warning(f"Heartbeat failed: {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"Error sending heartbeat: {str(e)}")
    
    def _heartbeat_worker(self):
        """
        Worker thread gửi heartbeat định kỳ
        """
        logger.info(f"Starting heartbeat worker for {self.service_name}")
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
            logger.info(f"Started heartbeat for service {self.service_name}")
    
    def stop_heartbeat(self):
        """
        Dừng thread gửi heartbeat
        """
        logger.info(f"Stopping heartbeat for service {self.service_name}")
        self.should_stop = True
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=1)
            logger.info(f"Stopped heartbeat for service {self.service_name}")