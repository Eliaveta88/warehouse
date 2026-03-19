"""Description strings for warehouse endpoints."""

LIST_STOCK_DESC = (
    "Retrieve inventory overview with hot stock balances. "
    "Shows available, reserved, and total quantities per product. "
    "Action: LIST_STOCK"
)

RESERVE_STOCK_DESC = (
    "Reserve stock batch using FEFO (First-Expiry-First-Out) algorithm. "
    "Allocates oldest batches first to minimize waste. "
    "Action: RESERVE_STOCK"
)

RELEASE_STOCK_DESC = (
    "Release previously made reservation. "
    "Returns reserved stock to available inventory. "
    "Action: RELEASE_STOCK"
)

RECEIVE_BATCH_DESC = (
    "Receive new batch with expiry date tracking. "
    "Registers incoming goods and updates stock levels. "
    "Action: RECEIVE_BATCH"
)
