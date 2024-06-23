import pytest
from Backend_B2A import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.mark.parametrize(
    "login_data, expected_status",
    [
        (
            # Valid email 
            {"email": "jijoce5531@egela.com"},
            # Expected status code
            200

        ),
        (
            # Invalid email
            {"email": "invalid@a"},
            # Expected status code
            400
        )
    ],
    ids=['valid_login', 'invalid_login']
)

def test_send_password_reset_email(client, login_data, expected_status):
    with app.app_context():



        response = client.post('/send_password_reset_email', json=login_data)

        assert response.status_code == expected_status
