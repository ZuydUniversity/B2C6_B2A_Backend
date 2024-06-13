import pytest
from flask import Flask
from collections import defaultdict
from Backend_B2A import app  # Assuming `app` is the Flask application instance

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.mark.parametrize(
    "db_data, expected_response",
    [
        (
            # db_data represents the result set from the query
            [
                (1, '2021-01-01', 'Description 1', 1, 'User1', 'Lastname1'),
                (1, '2021-01-01', 'Description 1', 2, 'User2', 'Lastname2'),
                (2, '2021-02-01', 'Description 2', 3, 'User3', 'Lastname3')
            ],
            # expected_response represents the JSON response structure
            {
                1: {
                    'Date': '2021-01-01',
                    'Description': 'Description 1',
                    'participants': {
                        1: {'name': 'User1', 'lastname': 'Lastname1'},
                        2: {'name': 'User2', 'lastname': 'Lastname2'}
                    }
                },
                2: {
                    'Date': '2021-02-01',
                    'Description': 'Description 2',
                    'participants': {
                        3: {'name': 'User3', 'lastname': 'Lastname3'}
                    }
                }
            }
        ),
        (
            # Empty result set
            [],
            # Expected response for no data
            []
        ),
        (
            # Single appointment result set
            [
                (3, '2021-03-01', 'Description 3', 4, 'User4', 'Lastname4')
            ],
            {
                3: {
                    'Date': '2021-03-01',
                    'Description': 'Description 3',
                    'participants': {
                        4: {'name': 'User4', 'lastname': 'Lastname4'}
                    }
                }
            }
        )
    ],
    ids=['multiple_appointments', 'no_appointments', 'single_appointment']
)
def test_get_all_appointments(client, mocker, db_data, expected_response):
    with app.app_context():
        # Mock DB cursor
        mock_cursor = mocker.MagicMock()
        mock_cursor.fetchall.return_value = db_data
        mock_connection = mocker.MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        # Patch mysql connection
        mocker.patch('Backend_B2A.mysql', return_value=mock_connection)

        response = client.get('/appointment/get_all')

        assert response.status_code == 200
        assert response.json == expected_response
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_cursor.close.assert_called_once()

# @pytest.mark.parametrize()
# def test_get_all_user_appointmets(user_id):
#     True

# @pytest.mark.parametrize()
# def test_create_appointment():
#     True

# @pytest.mark.parametrize()
# def test_update_appointment(appointment_id):
#     True

# @pytest.mark.parametrize()
# def test_delete_appointment(appointment_id):
#     True

# @pytest.mark.parametrize()
# def test_get_user_appointment(user_id):
#     True

if __name__ == '__main__':
    pytest.main()
