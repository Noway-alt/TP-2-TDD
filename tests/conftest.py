import pytest
from fastapi.testclient import TestClient

from app.main import ORDERS, app


@pytest.fixture(autouse=True)
def reset_orders():
    ORDERS.clear()
    yield
    ORDERS.clear()


@pytest.fixture
def client():
    return TestClient(app)
