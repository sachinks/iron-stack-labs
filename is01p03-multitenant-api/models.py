# models.py
"""Data models and simulated stores for the multitenant API.

In a real app this would be a database ORM layer (SQLAlchemy, Tortoise, etc.).
For this project we keep an in-memory dict to demonstrate tenant isolation.
"""

# Simulated per-tenant data store
TENANT_DATA = {
    "sachin": {"plan": "pro", "records": 42},
    "bob": {"plan": "free", "records": 7},
}
