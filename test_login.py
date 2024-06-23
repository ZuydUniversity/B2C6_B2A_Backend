import pytest
from Backend_B2A import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.mark.parametrize(
    "login_data, db_data, expected_status, expected_response",
    [
        (
            # Valid login credentials
            {"email": "doctor@example.com", "password": "doctor"},
            # Mock DB result for valid user
            (1, 1),
            # Expected status code
            200,
            # Expected response
            {"role": 1, "user_id": 1}
        ),
        (
            # Invalid login credentials
            {"email": "invalid@a", "password": "abc123"},
            # Mock DB result for invalid user
            None,
            # Expected status code
            400,
            # Expected response
            None
        )
    ],
    ids=['valid_login', 'invalid_login']
)

def test_login(client, mocker, login_data, db_data, expected_status, expected_response):
    with app.app_context():
        # Mock DB cursor
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = db_data

        # Mock mysql connection
        mock_connection = mocker.patch('Backend_B2A.MySQL.connection', autospec=True)
        mock_connection.cursor.return_value = mock_cursor


        response = client.post('/login', json=login_data)

        assert response.status_code == expected_status
        assert response.json == expected_response