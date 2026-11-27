# Inventory service

Run `pip install -r requirements.txt` and `python app.py` locally.

Stock is tracked per item. Receipts increase stock; issues decrease stock. Quantities must be positive integers. References must be unique. An issue must never exceed available stock, including concurrent requests. Stock and movement history must be updated atomically. The report returns current stock and total units received and issued.

Synthetic local demonstration only. No production data.
