# capyface_commons/grpc_service/service_registry.py
import json
import os
import logging

logger = logging.getLogger('capyface.service_registry')

class ServiceRegistry:
    """
    Quản lý đăng ký các gRPC services
    """
    
    def __init__(self, config_file=None):
        """
        Khởi tạo registry
        
        Args:
            config_file: Đường dẫn file cấu hình JSON
        """
        self.config_file = config_file or os.environ.get('GRPC_CONFIG_FILE', '/app/config/grpc_services.json')
        self.services = {}
        
        # Tạo thư mục chứa file nếu chưa tồn tại
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Load cấu hình nếu file tồn tại
        if os.path.exists(self.config_file):
            self._load_config()
    
    def _load_config(self):
        """Load cấu hình từ file JSON"""
        try:
            with open(self.config_file, 'r') as f:
                self.services = json.load(f)
            logger.info(f"Loaded service registry from {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading service registry: {e}")
            self.services = {}
    
    def _save_config(self):
        """Lưu cấu hình vào file JSON"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.services, f, indent=2)
            logger.info(f"Saved service registry to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving service registry: {e}")
    
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
        # Cập nhật thông tin service
        self.services[service_name] = {
            "host": host,
            "port": port,
            "use_tls": use_tls,
            "stub_module": stub_module,
            "stub_class": stub_class,
            "methods": methods or {}
        }
        
        # Lưu cấu hình
        self._save_config()
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
        if service_name not in self.services:
            logger.error(f"Service {service_name} not found in registry")
            return
        
        # Tạo dict methods nếu chưa có
        if "methods" not in self.services[service_name]:
            self.services[service_name]["methods"] = {}
        
        # Thêm method
        self.services[service_name]["methods"][method_name] = {
            "request_module": request_module,
            "request_class": request_class
        }
        
        # Lưu cấu hình
        self._save_config()
        logger.info(f"Registered method: {service_name}.{method_name}")
    
    def get_service_config(self, service_name):
        """Lấy cấu hình của service"""
        return self.services.get(service_name)
    
    def get_all_services(self):
        """Lấy cấu hình của tất cả services"""
        return self.services

# Singleton instance
service_registry = ServiceRegistry()