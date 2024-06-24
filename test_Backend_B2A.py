import pytest
from flask import Flask
from collections import defaultdict
from Backend_B2A import app

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
                "1": {
                    'Date': '2021-01-01',
                    'Description': 'Description 1',
                    'participants': {
                        "1": {'name': 'User1', 'lastname': 'Lastname1'},
                        "2": {'name': 'User2', 'lastname': 'Lastname2'}
                    }
                },
                "2": {
                    'Date': '2021-02-01',
                    'Description': 'Description 2',
                    'participants': {
                        "3": {'name': 'User3', 'lastname': 'Lastname3'}
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
                "3": {
                    'Date': '2021-03-01',
                    'Description': 'Description 3',
                    'participants': {
                        "4": {'name': 'User4', 'lastname': 'Lastname4'}
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
        mock_cursor.execute.return_value = None
        mock_cursor.fetchall.return_value = db_data

        # Mock mysql connection
        mock_connection = mocker.patch('Backend_B2A.MySQL.connection', autospec=True)
        mock_connection.cursor.return_value = mock_cursor

        response = client.get('/appointment/get_all')

        assert response.status_code == 200
        assert response.json == expected_response

@pytest.mark.parametrize(
    "user_id, db_data, expected_response",
    [
        (
            1,
            # db_data represents the result set from the query
            [
                (1, '2021-01-01', 'Description 1', 1, 'User1', 'Lastname1'),
                (1, '2021-01-01', 'Description 1', 2, 'User2', 'Lastname2')
            ],
            # expected_response represents the JSON response structure
            {
                "1": {
                    'Date': '2021-01-01',
                    'Description': 'Description 1',
                    'participants': {
                        "1": {'name': 'User1', 'lastname': 'Lastname1'},
                        "2": {'name': 'User2', 'lastname': 'Lastname2'}
                    }
                }
            }
        ),
        (
            # Empty user_id
            1,
            # Empty result set
            [],
            # Expected response for no data
            []
        ),
        (
            # Single appointment result set
            4,
            [
                (3, '2021-03-01', 'Description 3', 4, 'User4', 'Lastname4')
            ],
            {
                "3": {
                    'Date': '2021-03-01',
                    'Description': 'Description 3',
                    'participants': {
                        "4": {'name': 'User4', 'lastname': 'Lastname4'}
                    }
                }
            }
        )
    ],
    ids=['multiple_appointments', 'no_appointments', 'single_appointment']  
)
def test_get_all_user_appointments(client, mocker, db_data, user_id, expected_response):
    with app.app_context():
        # Mock DB cursor
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.return_value = None
        mock_cursor.fetchall.return_value = db_data

        # Mock mysql connection
        mock_connection = mocker.patch('Backend_B2A.MySQL.connection', autospec=True)
        mock_connection.cursor.return_value = mock_cursor

        response = client.get("/user/" + str(user_id) + "/appointment")

        assert response.status_code == 200
        assert response.json == expected_response

@pytest.mark.parametrize(
    "request_body, db_data_participants, db_data_appointment, status_code, expected_response",
    [
        (
            # Multiple participants
            {
                "date": "10-06-2024",
                "description": "CMAS afspraak",
                "participants": [1, 3]
            },
            [{'Id': 1, 'Name': 'User1'}, {'Id': 3, 'Name': 'User3'}],
            [(123,)],
            200,
            {"message": "Appointment added successfully"}
        ),
        (
            # Empty request body
            {},
            [],  # No participant check needed
            [],  # No appointment data
            400,
            {"error": "Missing required appointment data: date, description, participants"}
        ),
        (
            # Single participant
            {
                "date": "10-06-2024",
                "description": "CMAS afspraak",
                "participants": [1]
            },
            [{'Id': 1, 'Name': 'User1'}],
            [(124,)],
            200,
            {"message": "Appointment added successfully"}
        )
    ],
    ids=['multiple_participants', 'no_appointment_data', 'single_participant']  
)
def test_create_appointment(client, mocker, request_body, db_data_participants, db_data_appointment, status_code, expected_response):
    with app.app_context():
        # Mock DB cursor
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.return_value = None

        # Prepare the side_effect for fetchone based on number of participants
        side_effect = []
        if 'participants' in request_body:
            side_effect.extend(db_data_participants)  # Add participant data
        if db_data_appointment:
            side_effect.extend(db_data_appointment)  # Add appointment ID data

        mock_cursor.fetchone.side_effect = side_effect

        # Mock mysql connection
        mock_connection = mocker.patch('Backend_B2A.MySQL.connection', autospec=True)
        mock_connection.cursor.return_value = mock_cursor

        response = client.post("/appointment/create", json=request_body)

        assert response.status_code == status_code
        assert response.json == expected_response

@pytest.mark.parametrize(
    "appointment_id, request_body, db_data_participants, db_data_appointment, existing_participants, expected_status_code, expected_response",
    [
        (
            123,
            {
                "date": "2024-06-11 00:00:00",
                "description": "CMAS afspraak",
                "participants": [1, 3]
            },
            [{'Id': 1, 'Name': 'User1'}, {'Id': 2, 'Name': 'User2'}],
            [(123,)],
            {1, 2},
            200,
            {"message": "Appointment updated successfully"}
        ),
        (
            456,
            {
                "date": "2024-06-12 00:00:00",
                "description": "Dentist appointment",
                "participants": [2, 4]
            },
            [{'Id': 2, 'Name': 'User2'}, {'Id': 4, 'Name': 'User4'}],
            [(456,)],
            {2, 4},
            200,
            {"message": "Appointment updated successfully"}
        ),
        (
            789,
            {
                "date": "2024-06-13 00:00:00",
                "description": "Meeting",
                "participants": [5, 1]
            },
            [{'Id': 4, 'Name': 'User4'}, {'Id': 5, 'Name': 'User5'}],
            [(789,)],
            {4, 5},
            200,
            {"message": "Appointment updated successfully"}
        ),
        (
            999,
            {
                "date": "2024-06-14 00:00:00",
                "description": "Project discussion",
                "participants": [6, 7]
            },
            [{'Id': 6, 'Name': 'User6'}, {'Id': 7, 'Name': 'User7'}],
            [(0,)],
            {6, 7},
            404,
            {"error": "Appointment not found"}
        ),
    ]
)
def test_update_appointment(client, mocker, appointment_id, request_body, db_data_participants, existing_participants, db_data_appointment, expected_status_code, expected_response):
    with app.app_context():
        # Mock DB cursor
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.return_value = None

        side_effect = []
        if db_data_participants:
            side_effect.extend(db_data_participants)
        if db_data_appointment:
            side_effect.extend(db_data_appointment)

        mock_cursor.fetchone.side_effect = side_effect
        mock_cursor.fetchall.return_value = [(participant_id,) for participant_id in existing_participants]

        # Mock mysql connection
        mock_connection = mocker.patch('Backend_B2A.MySQL.connection', autospec=True)
        mock_connection.cursor.return_value = mock_cursor

        response = client.put(f"/appointment/{appointment_id}/update", json=request_body)

        assert response.status_code == expected_status_code
        assert response.json == expected_response

@pytest.mark.parametrize(
    "appointment_id, db_data, expected_status_code, expected_response",
    [
        (
            123, 
            [(1, '2021-01-01', 'Description 1'),],
            200, 
            {"message": "Appointment deleted successfully"}
        ),
        (
            999,
            None,
            404,
            {"error": "Appointment not found"}
        )
    ],
)
def test_delete_appointment(client, mocker, db_data, appointment_id, expected_status_code, expected_response):
    with app.app_context():
        # Mock DB cursor
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = db_data

        # Mock mysql connection
        mock_connection = mocker.patch('Backend_B2A.MySQL.connection', autospec=True)
        mock_connection.cursor.return_value = mock_cursor

        response = client.delete(f'/appointment/{appointment_id}/delete')

        assert response.status_code == expected_status_code
        assert response.json == expected_response

@pytest.mark.parametrize("user_id, request_body, db_data, user_exists, expected_status_code, expected_response", 
    [
        (1, {}, None, False, 400, {"error": "Missing required appointment data: start_date, end_date"}),  # Missing fields
        (1, {"start_date": "invalid_date", "end_date": "2023-01-01"}, None, True, 400, {"error": "start_date is not in the correct format. Expected format: %Y-%m-%d"}),  # Invalid start_date format
        (1, {"start_date": "2023-01-01", "end_date": "2023-01-01"}, None, False, 400, {"error": "User not found"}),  # User not found
        (1, {"start_date": "2023-01-01", "end_date": "2023-12-31"}, [], True, 200, []),  # No appointments
        (1, {"start_date": "2023-01-01", "end_date": "2023-12-31"}, 
        [(1, "2023-06-15", "Description1", 1, "John", "Doe")], True, 200, {'1': {"Date": "2023-06-15", "Description": "Description1", "participants": {'1': {"name": "John", "lastname": "Doe"}}}})  # Valid response with data
    ]
)
def test_get_user_appointments(client, mocker, user_id, request_body, db_data, user_exists, expected_status_code, expected_response):
    with app.app_context():
        # Mock DB cursor
        mock_cursor = mocker.MagicMock()
        if user_exists:
            mock_cursor.fetchone.return_value = (user_id, "John", "Doe")
        else:
            mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = db_data

        # Mock mysql connection
        mock_connection = mocker.patch('Backend_B2A.MySQL.connection', autospec=True)
        mock_connection.cursor.return_value = mock_cursor

        response = client.get(f"/user/{user_id}/appointment/get", json=request_body)

        assert response.status_code == expected_status_code
        assert response.get_json() == expected_response
        
if __name__ == '__main__':
    pytest.main()
