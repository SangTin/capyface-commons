# capyface_commons/grpc_service/service_registry.py
import json
import redis
import logging
import os
import time
import threading

logger = logging.getLogger('capyface.service_registry')

class RedisServiceRegistry:
    """Quản lý đăng ký các gRPC services sử dụng Redis"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RedisServiceRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, host=None, port=None, db=0, password=None):
        if self._initialized:
            return
            
        # Đọc cấu hình từ biến môi trường nếu không được cung cấp
        self.redis_host = host or os.environ.get('REDIS_HOST', 'localhost')
        self.redis_port = port or int(os.environ.get('REDIS_PORT', 6379))
        self.redis_db = db or int(os.environ.get('REDIS_DB', 0))
        self.redis_password = password or os.environ.get('REDIS_PASSWORD', None)
        
        # Khởi tạo Redis client
        self.redis = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=self.redis_password,
            decode_responses=True  # Tự động decode response thành string
        )
        
        # Key prefix cho các services
        self.service_key_prefix = "capyface:service:"
        
        self._initialized = True
        logger.info(f"RedisServiceRegistry initialized with Redis at {self.redis_host}:{self.redis_port}")
    
    def register_service(self, service_name, host, port, use_tls=False,
                       stub_module=None, stub_class=None, methods=None):
        """
        Đăng ký service với registry
        
        Args:
            service_name: Tên của service
            host: Host của service
            port: Port của service
            use_tls: Có sử dụng TLS không
            stub_module: Module chứa gRPC stub
            stub_class: Tên class của stub
            methods: Dict chứa thông tin các methods
        """
        # Tạo thông tin service
        service_info = {
            "host": host,
            "port": port,
            "use_tls": use_tls,
            "stub_module": stub_module,
            "stub_class": stub_class,
            "methods": methods or {}
        }
        
        # Lưu vào Redis với TTL (ví dụ: 5 phút)
        self.redis.setex(
            f"{self.service_key_prefix}{service_name}",
            300,  # 5 phút (300 giây)
            json.dumps(service_info)
        )
        
        logger.info(f"Registered service: {service_name} at {host}:{port}")
    
    def register_method(self, service_name, method_name, request_module, request_class):
        """
        Đăng ký method cho service
        
        Args:
            service_name: Tên service
            method_name: Tên method
            request_module: Module chứa request class
            request_class: Tên class của request
        """
        # Kiểm tra xem service có tồn tại không
        service_key = f"{self.service_key_prefix}{service_name}"
        service_info_json = self.redis.get(service_key)
        
        if not service_info_json:
            logger.error(f"Service {service_name} not found in registry")
            return False
        
        # Parse thông tin service
        service_info = json.loads(service_info_json)
        
        # Khởi tạo dict methods nếu chưa có
        if "methods" not in service_info:
            service_info["methods"] = {}
        
        # Thêm method
        service_info["methods"][method_name] = {
            "request_module": request_module,
            "request_class": request_class
        }
        
        # Cập nhật lại vào Redis
        self.redis.setex(
            service_key,
            300,  # 5 phút TTL
            json.dumps(service_info)
        )
        
        logger.info(f"Registered method: {service_name}.{method_name}")
        return True
    
    def get_service_config(self, service_name):
        """Lấy cấu hình của service"""
        service_key = f"{self.service_key_prefix}{service_name}"
        service_info_json = self.redis.get(service_key)
        
        if not service_info_json:
            logger.warning(f"Service {service_name} not found in registry")
            return None
        
        return json.loads(service_info_json)
    
    def get_all_services(self):
        """Lấy cấu hình của tất cả services"""
        # Lấy tất cả keys có prefix là service_key_prefix
        service_keys = self.redis.keys(f"{self.service_key_prefix}*")
        
        services = {}
        for key in service_keys:
            service_name = key.replace(self.service_key_prefix, '')
            service_info = self.get_service_config(service_name)
            if service_info:
                services[service_name] = service_info
        
        return services
    
    def heartbeat(self, service_name):
        """
        Cập nhật thời gian sống của service (heartbeat)
        """
        service_key = f"{self.service_key_prefix}{service_name}"
        service_info_json = self.redis.get(service_key)
        
        if not service_info_json:
            logger.warning(f"Cannot send heartbeat - Service {service_name} not found in registry")
            return False
        
        # Cập nhật TTL
        self.redis.expire(service_key, 300)  # 5 phút
        logger.debug(f"Heartbeat sent for service {service_name}")
        return True
    
    def start_heartbeat(self, service_name, interval=60):
        """
        Bắt đầu gửi heartbeat định kỳ cho service
        
        Args:
            service_name: Tên service cần gửi heartbeat
            interval: Khoảng thời gian giữa các lần gửi heartbeat (giây)
        """
        def heartbeat_worker():
            while True:
                try:
                    self.heartbeat(service_name)
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in heartbeat for {service_name}: {e}")
                    time.sleep(5)  # Ngủ một chút khi có lỗi
        
        # Khởi động thread
        thread = threading.Thread(target=heartbeat_worker, daemon=True)
        thread.start()
        logger.info(f"Started heartbeat for {service_name} with interval {interval}s")
        return thread

# Singleton instance
service_registry = RedisServiceRegistry()