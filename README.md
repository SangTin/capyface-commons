# CapyFace Commons

## Overview

CapyFace Commons là một thư viện tiện ích dùng chung cho các microservices trong hệ sinh thái CapyFace. Thư viện cung cấp các công cụ và tiện ích để hỗ trợ việc phát triển và quản lý các dịch vụ trong kiến trúc microservices.

## Features

### Service Registry
- Đăng ký và quản lý các microservices
- Hỗ trợ heartbeat cho các services
- Tích hợp với Redis để quản lý service discovery

## Installation

### Cài đặt từ GitHub
```bash
pip install git+https://github.com/SangTin/capyface-commons.git
```

## Usage

### Service Registration

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

## Configuration

### Yêu cầu
- Python 3.8+
- Redis
- Django (optional)

### Cấu hình Redis
Đảm bảo cấu hình Redis trong settings của bạn:
```python
# settings.py
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
```
