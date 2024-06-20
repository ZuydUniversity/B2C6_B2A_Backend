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
            [{'LAST_INSERT_ID()': 123}],
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
            [{'LAST_INSERT_ID()': 124}],
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
