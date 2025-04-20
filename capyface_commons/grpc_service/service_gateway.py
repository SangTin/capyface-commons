from .service_registry import service_registry
import grpc
import importlib
import logging
import time

logger = logging.getLogger('capyface.service_gateway')

class ServiceGateway:
    """
    Gateway tập trung cho các gRPC services với hỗ trợ timeout và error handling nâng cao
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ServiceGateway, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, 
                 default_timeout=5,  # Mặc định 5 giây
                 max_retries=3,      # Số lần thử lại
                 retry_delay=1):     # Thời gian chờ giữa các lần thử
        if self._initialized:
            return
            
        self.registry = service_registry
        self.channels = {}
        self.stubs = {}
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._initialized = True
        logger.info("ServiceGateway initialized")
    
    def _create_channel(self, host, port, use_tls=False):
        """Tạo channel với cấu hình kết nối"""
        target = f"{host}:{port}"
        
        # Cấu hình channel options
        channel_options = [
            ('grpc.connect_timeout_ms', 3000),  # Timeout kết nối
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB max message
            ('grpc.max_send_message_length', 100 * 1024 * 1024),    # 100MB max message
        ]
        
        try:
            if use_tls:
                # Tạo secure channel
                credentials = grpc.ssl_channel_credentials()
                channel = grpc.secure_channel(target, credentials, options=channel_options)
            else:
                # Tạo insecure channel
                channel = grpc.insecure_channel(target, options=channel_options)
            
            return channel
        except Exception as e:
            logger.error(f"Error creating gRPC channel to {target}: {e}")
            raise
    
    def _get_stub(self, service_name):
        """Lấy stub cho service với caching"""
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
        use_tls = service_config.get("use_tls", False)
        
        # Tạo hoặc lấy channel đã tồn tại
        target = f"{host}:{port}"
        if target not in self.channels:
            self.channels[target] = self._create_channel(host, port, use_tls)
        
        # Import stub class
        try:
            stub_module = importlib.import_module(service_config["stub_module"])
            stub_class = getattr(stub_module, service_config["stub_class"])
        except (ImportError, AttributeError) as e:
            logger.error(f"Error importing stub for {service_name}: {e}")
            raise
        
        # Tạo stub
        self.stubs[service_name] = stub_class(self.channels[target])
        return self.stubs[service_name]
    
    def call(self, service_name, method_name, timeout=None, **kwargs):
        """
        Gọi method từ service với hỗ trợ retry và timeout
        
        :param service_name: Tên service
        :param method_name: Tên method
        :param timeout: Thời gian timeout (giây)
        :param kwargs: Các tham số cho method
        :return: Kết quả gọi method
        """
        # Sử dụng timeout mặc định nếu không được cung cấp
        if timeout is None:
            timeout = self.default_timeout
        
        # Lấy stub
        stub = self._get_stub(service_name)
        
        # Lấy thông tin method
        service_config = self.registry.get_service_config(service_name)
        method_config = service_config.get("methods", {}).get(method_name)
        
        if not method_config:
            raise ValueError(f"Method {method_name} not registered for service {service_name}")
        
        # Import request class
        try:
            request_module = importlib.import_module(method_config["request_module"])
            request_class = getattr(request_module, method_config["request_class"])
        except (ImportError, AttributeError) as e:
            logger.error(f"Error importing request class: {e}")
            raise
        
        # Tạo request object
        request = request_class(**kwargs)
        
        # Lấy method từ stub
        method = getattr(stub, method_name)
        
        # Thực hiện gọi method với retry
        for attempt in range(self.max_retries):
            try:
                # Gọi method với timeout
                response = method(request, timeout=timeout)
                return response
            
            except grpc.RpcError as e:
                # Xử lý các lỗi gRPC cụ thể
                logger.warning(f"gRPC call failed (attempt {attempt + 1}): {e}")
                
                # Kiểm tra mã lỗi để quyết định retry
                if e.code() in [
                    grpc.StatusCode.UNAVAILABLE,      # Service không khả dụng
                    grpc.StatusCode.DEADLINE_EXCEEDED,# Hết thời gian chờ
                    grpc.StatusCode.INTERNAL,         # Lỗi nội bộ
                ]:
                    # Nếu chưa phải lần thử cuối, chờ và thử lại
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    else:
                        # Lần thử cuối, raise exception
                        logger.error(f"Final attempt failed: {e}")
                        raise
                else:
                    # Các lỗi khác không retry
                    raise
            
            except Exception as e:
                # Bắt các ngoại lệ không mong muốn
                logger.error(f"Unexpected error in service call: {e}")
                raise

# Singleton instance
service_gateway = ServiceGateway()