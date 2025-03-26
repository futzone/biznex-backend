import enum
from enum import Enum


class AdminOrderStatusEnum(str, Enum):
    opened = "opened"
    completed = "completed"
    cancelled = "cancelled"


class PaymentMethodEnum(str, Enum):
    cash = "cash"
    card = "card"
    debt = "debt"


class PaymentStatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class OrderStatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"
    canceled = "canceled"


class OrderTypeEnum(str, Enum):
    regular = "regular"
    express = "express"


class UserRolesEnum(str, enum.Enum):
    SUPERUSER = 1
    ADMIN = 2
    SELLER = 3
    MANAGER = 4
    CUSTOMER = 5


class WarehouseApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Methods(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class NotificationStatus(str, enum.Enum):
    SUCCESS = "success"
    INFO = "info"
    DANGER = "danger"
    WARNING = "warning"


class RevisionStatus(str, Enum):
    created = "created"
    completed = "completed"
    cancelled = "cancelled"
