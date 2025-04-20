from .service_registry import service_registry
import grpc
import importlib
import logging

logger = logging.getLogger('capyface.service_gateway')

class ServiceGateway:
    """
    Gateway tập trung cho các gRPC services
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ServiceGateway, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.registry = service_registry
        self.channels = {}
        self.stubs = {}
        self._initialized = True
        logger.info("ServiceGateway initialized")
    
    def _get_stub(self, service_name):
        """Lấy stub cho service"""
        # Kiểm tra xem đã có stub chưa
        if service_name in self.stubs:
            return self.stubs[service_name]
        
        # Lấy cấu hình từ registry
        service_config = self.registry.get_service_config(service_name)
        if not service_config:
            raise ValueError(f"Service {service_name} not registered")
        
        # Tạo channel
        host = service_config["host"]
        port = service_config["port"]
        target = f"{host}:{port}"
        
        if target not in self.channels:
            if service_config.get("use_tls", False):
                # Tạo secure channel
                credentials = grpc.ssl_channel_credentials()
                self.channels[target] = grpc.secure_channel(target, credentials)
            else:
                # Tạo insecure channel
                self.channels[target] = grpc.insecure_channel(target)
        
        # Import stub class
        stub_module = importlib.import_module(service_config["stub_module"])
        stub_class = getattr(stub_module, service_config["stub_class"])
        
        # Tạo stub
        self.stubs[service_name] = stub_class(self.channels[target])
        return self.stubs[service_name]
    
    def call(self, service_name, method_name, **kwargs):
        """Gọi method từ service"""
        # Lấy stub
        stub = self._get_stub(service_name)
        
        # Lấy thông tin method
        service_config = self.registry.get_service_config(service_name)
        method_config = service_config.get("methods", {}).get(method_name)
        
        if not method_config:
            raise ValueError(f"Method {method_name} not registered for service {service_name}")
        
        # Import request class
        request_module = importlib.import_module(method_config["request_module"])
        request_class = getattr(request_module, method_config["request_class"])
        
        # Tạo request object
        request = request_class(**kwargs)
        
        # Gọi method
        method = getattr(stub, method_name)
        return method(request)

# Singleton instance
service_gateway = ServiceGateway()