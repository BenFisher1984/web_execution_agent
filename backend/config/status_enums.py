from enum import Enum

class OrderStatus(str, Enum):
    INACTIVE = "Inactive"
    ACTIVE = "Active"
    WORKING = "Working"
    PENDING = "Pending"
    ENTRY_ORDER_SUBMITTED = "Entry Order Submitted"
    CONTINGENT_ORDER_ACTIVE = "Contingent Order Active"
    CONTINGENT_ORDER_SUBMITTED = "Contingent Order Submitted"
    CONTINGENT_ORDER_WORKING = "Contingent Order Working"

class TradeStatus(str, Enum):
    BLANK = "--"
    PENDING = "Pending"
    LIVE = "Live"
    FILLED = "Filled"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"
