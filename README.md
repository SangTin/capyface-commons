Dưới đây là README đã cập nhật, bao gồm phương thức `start_heartbeat` cho Redis Service Registry:

# CapyFace Commons

## Overview

CapyFace Commons là một thư viện tiện ích dùng chung cho các microservices trong hệ sinh thái CapyFace. Thư viện cung cấp các công cụ và tiện ích để hỗ trợ việc phát triển và quản lý các dịch vụ trong kiến trúc microservices.

## Features

### Service Registry
- Đăng ký và quản lý các microservices
- Hỗ trợ heartbeat cho các services
- Tích hợp với Redis để quản lý service discovery

### gRPC Support
- Định nghĩa các interfaces giao tiếp giữa các services thông qua Protocol Buffers
- ServiceGateway tập trung để đơn giản hóa giao tiếp giữa các services
- Tự động discovery services thông qua Redis
- Hỗ trợ retry, circuit breaker và error handling

## Installation

### Cài đặt từ GitHub
```bash
pip install git+https://github.com/SangTin/capyface-commons.git
```

## Usage

### REST API Service Registration

```python
from capyface_commons.service_registry import ServiceRegistration
import os

# Khởi tạo service registration
service_registry = ServiceRegistration(
    api_gateway_url=os.getenv('API_GATEWAY_URL', 'http://api-gateway:8000'),
    service_name="user-service",
    service_url=os.getenv('SERVICE_URL', 'http://user-service:8000'),
    routes_config={
        "api/users": True,
        "api/auth": True,
        "api/public/health": False
    }
)

# Đăng ký service
service_registry.register()

# Bắt đầu gửi heartbeat
service_registry.start_heartbeat()
```

### gRPC Service với Redis

#### Cấu hình Redis
```python
# Thiết lập trong environment variables
# REDIS_HOST=redis-service
# REDIS_PORT=6379
# REDIS_DB=0
# REDIS_PASSWORD=optional-password

# Hoặc khởi tạo thủ công trong code
from capyface_commons.grpc_service import service_registry

# Tùy chỉnh cấu hình Redis (tuỳ chọn)
custom_registry = RedisServiceRegistry(
    host="custom-redis",
    port=6380,
    db=1,
    password="your-password"
)
```

#### Đăng ký gRPC Service (cho các service provider)

```python
from capyface_commons.grpc_service import service_registry
import os

# Đăng ký service
service_registry.register_service(
    service_name="user_service",
    host=os.environ.get('GRPC_HOST', '0.0.0.0'),
    port=int(os.environ.get('GRPC_PORT', 50051)),
    stub_module="capyface_commons.generated.user_service_pb2_grpc",
    stub_class="UserServiceStub"
)

# Đăng ký các methods
service_registry.register_method(
    service_name="user_service",
    method_name="ValidateToken",
    request_module="capyface_commons.generated.user_service_pb2",
    request_class="ValidateTokenRequest"
)

# Bắt đầu gửi heartbeat tự động 
service_registry.start_heartbeat("user_service", interval=60)
```

#### Triển khai gRPC Service

```python
# Định nghĩa servicer
from capyface_commons.generated import user_service_pb2
from capyface_commons.generated import user_service_pb2_grpc

class UserServicer(user_service_pb2_grpc.UserServiceServicer):
    def ValidateToken(self, request, context):
        # Triển khai logic xác thực token
        # ...
        return user_service_pb2.ValidateTokenResponse(
            is_valid=True,
            user=user_service_pb2.User(
                id="123",
                username="example_user",
                email="user@example.com"
                # Thêm các trường khác
            )
        )

# Khởi động gRPC server
import grpc
from concurrent import futures

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
```

#### Sử dụng ServiceGateway (cho các service consumer)

```python
from capyface_commons.grpc_service import service_gateway

# Gọi service khác thông qua gateway
try:
    response = service_gateway.call(
        service_name="user_service",
        method_name="ValidateToken",
        token="your_jwt_token_here"
    )
    
    if response.is_valid:
        user_data = {
            'id': response.user.id,
            'username': response.user.username,
            'email': response.user.email,
            # Các trường khác
        }
        # Xử lý dữ liệu
    else:
        # Xử lý khi token không hợp lệ
except Exception as e:
    # Xử lý lỗi kết nối hoặc gRPC error
```

## Protocol Buffers

### Cấu trúc .proto files

Thư viện chứa các file `.proto` định nghĩa interfaces giữa các services:

```protobuf
// Example: user_service.proto
syntax = "proto3";

package capyface.user;

service UserService {
  rpc ValidateToken (ValidateTokenRequest) returns (ValidateTokenResponse) {}
}

message ValidateTokenRequest {
  string token = 1;
}

message ValidateTokenResponse {
  bool is_valid = 1;
  User user = 2;
}

message User {
  string id = 1;
  string username = 2;
  string email = 3;
  // Các trường khác
}
```

### Cập nhật và Biên dịch Proto

Khi cần thay đổi định nghĩa service:

1. Chỉnh sửa file `.proto` tương ứng
2. Biên dịch lại:
   ```bash
   python -m grpc_tools.protoc -I./protos --python_out=./capyface_commons/generated --grpc_python_out=./capyface_commons/generated ./protos/user_service.proto
   ```
3. Commit cả file `.proto` và mã đã biên dịch
4. Tăng version của thư viện

## Configuration

### Yêu cầu
- Python 3.8+
- Redis
- gRPC và Protocol Buffers
- Django (optional)

### Environment Variables
```
# Redis configuration
REDIS_HOST=redis-service
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional-password

# gRPC configuration
GRPC_HOST=0.0.0.0
GRPC_PORT=50051

# API Gateway (for REST)
API_GATEWAY_URL=http://api-gateway:8000
```

## Cấu trúc Dự án
```
capyface-commons/
├── protos/                       # Protocol Buffer definitions
│   ├── user_service.proto
│   ├── post_service.proto
│   └── ...
├── capyface_commons/
│   ├── service_registry/         # REST API service registry
│   ├── grpc_service/             # gRPC utilities
│   │   ├── __init__.py
│   │   ├── service_registry.py   # Redis-based service registry
│   │   └── service_gateway.py    # Service gateway
│   ├── generated/                # Generated code from Protocol Buffers
│   └── ...
└── README.md
```