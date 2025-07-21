from enum import Enum

class OrderStatus(str, Enum):
    DRAFT = "Draft"
    INACTIVE = "Inactive"
    WORKING = "Working"
    PENDING = "Pending"
    ENTRY_ORDER_SUBMITTED = "Entry Order Submitted"
    CONTINGENT_ORDER_SUBMITTED = "Contingent Order Submitted"
    CONTINGENT_ORDER_WORKING = "Contingent Order Working"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"

class TradeStatus(str, Enum):
    BLANK = "--"
    PENDING = "Pending"
    LIVE = "Live"
    FILLED = "Filled"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"
