from enum import Enum

class OrderStatus(str, Enum):
    INACTIVE = "Inactive"
    ACTIVE = "Active"
    ENTRY_ORDER_SUBMITTED = "Entry Order Submitted"
    CONTINGENT_ORDER_ACTIVE = "Contingent Order Active"
    CONTINGENT_ORDER_SUBMITTED = "Contingent Order Submitted"

class TradeStatus(str, Enum):
    BLANK = "--"
    PENDING = "Pending"
    LIVE = "Live"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"
