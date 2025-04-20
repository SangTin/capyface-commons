import os
import importlib
import inspect
import logging
from google.protobuf.descriptor_pb2 import FileDescriptorProto

logger = logging.getLogger('capyface.proto_discovery')

class ProtoDiscovery:
    """
    Tự động phát hiện và đăng ký các gRPC services từ file .proto đã biên dịch
    """
    
    def __init__(self, registry, generated_package="capyface_commons.generated"):
        """
        Khởi tạo discovery
        
        Args:
            registry: ServiceRegistry để đăng ký
            generated_package: Package chứa mã đã biên dịch từ .proto
        """
        self.registry = registry
        self.generated_package = generated_package
    
    def discover_and_register(self):
        """
        Phát hiện và đăng ký tất cả services
        """
        # Import package chứa mã đã biên dịch
        try:
            package = importlib.import_module(self.generated_package)
        except ImportError:
            logger.error(f"Cannot import package: {self.generated_package}")
            return
        
        # Tìm tất cả modules trong package
        for _, module_name, is_package in pkgutil.iter_modules(package.__path__):
            if not is_package and module_name.endswith('_pb2'):
                # Tìm thấy module pb2
                self._process_pb2_module(module_name)
    
    def _process_pb2_module(self, module_name):
        """
        Xử lý module pb2 để tìm và đăng ký services
        
        Args:
            module_name: Tên module pb2
        """
        # Import module
        full_module_name = f"{self.generated_package}.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
        except ImportError:
            logger.error(f"Cannot import module: {full_module_name}")
            return
        
        # Tìm service descriptor
        for name, obj in inspect.getmembers(module):
            if name == 'DESCRIPTOR' and isinstance(obj, FileDescriptorProto):
                self._process_descriptor(module_name, obj, module)
    
    def _process_descriptor(self, module_name, descriptor, module):
        """
        Xử lý file descriptor để đăng ký services
        
        Args:
            module_name: Tên module
            descriptor: File descriptor
            module: Module object
        """
        # Tìm service trong descriptor
        for service in descriptor.service:
            service_name = service.name.lower() 
            grpc_module_name = f"{self.generated_package}.{module_name.replace('_pb2', '_pb2_grpc')}"
            
            # Import module grpc
            try:
                grpc_module = importlib.import_module(grpc_module_name)
                stub_class = getattr(grpc_module, f"{service.name}Stub")
            except (ImportError, AttributeError):
                logger.error(f"Cannot find stub class for service: {service.name}")
                continue
            
            # Đăng ký service
            self.registry.register_service(
                service_name=service_name,
                host=os.environ.get(f"{service_name.upper()}_HOST", "localhost"),
                port=int(os.environ.get(f"{service_name.upper()}_PORT", 50051)),
                stub_module=grpc_module_name,
                stub_class=f"{service.name}Stub",
                methods={}
            )
            
            # Đăng ký các methods
            for method in service.method:
                input_type = method.input_type.name
                self.registry.register_method(
                    service_name=service_name,
                    method_name=method.name,
                    request_module=f"{self.generated_package}.{module_name}",
                    request_class=input_type
                )
            
            logger.info(f"Auto-registered service: {service_name}")