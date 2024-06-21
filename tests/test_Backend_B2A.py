# python -m unittest test_Backend_B2A.py

# 1. Import necessary modules and classes: unittest for testing, mock_open and patch for mocking.
# 2. Define a test class inheriting from unittest.TestCase.
# 3. Inside the test class, define two test methods:
#    a. test_default_dev_environment_configuration:
#       - Create a mock configuration for the 'dev' environment.
#       - Mock the open function to return this mock configuration when called.
#       - Use patch to mock the os.getenv function to return "dev".
#       - Reload the Backend_B2A module to apply the mocked configuration.
#       - Assert that the app's configuration matches the mocked 'dev' environment configuration.
#    b. test_production_environment_configuration (incomplete in the provided code).
# 4. Use patch and mock_open to simulate different configurations based on the environment.
# 5. Reload the module under test to apply the mocked configurations.
# 6. Assert that the application's configuration matches the expected values for each environment.

import unittest
from unittest.mock import mock_open, patch
from Backend_B2A import app  # Assuming the provided code is in Backend_B2A.py
import json
import importlib

class TestAppConfig(unittest.TestCase):
    def test_default_dev_environment_configuration(self):
        # Mock configuration for the 'dev' environment
        mock_config = {
            "dev": {
                "MYSQL_HOST": "localhost",
                "MYSQL_USER": "user_dev",
                "MYSQL_PASSWORD": "password_dev",
                "MYSQL_DB": "db_dev"
            }
        }
        # Use patch to mock open function within the context of this test
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_config))):
            # Reload the module to apply the mocked configuration
            with patch("os.getenv", return_value="dev"):
                import Backend_B2A
                importlib.reload(Backend_B2A)
                from Backend_B2A import app
                # Assert the configuration is as expected
                self.assertEqual(app.config['MYSQL_HOST'], "localhost")
                self.assertEqual(app.config['MYSQL_USER'], "user_dev")
                self.assertEqual(app.config['MYSQL_PASSWORD'], "password_dev")
                self.assertEqual(app.config['MYSQL_DB'], "db_dev")

    def test_production_environment_configuration(self):
        # Mock configuration for the 'production' environment
        mock_config = {
            "production": {
                "MYSQL_HOST": "prod_host",
                "MYSQL_USER": "user_prod",
                "MYSQL_PASSWORD": "password_prod",
                "MYSQL_DB": "db_prod"
            }
        }
        # Use patch to mock open function within the context of this test
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_config))):
            # Reload the module to apply the mocked configuration
            with patch("os.getenv", return_value="production"):
                import Backend_B2A
                importlib.reload(Backend_B2A)
                from Backend_B2A import app
                # Assert the configuration is as expected
                self.assertEqual(app.config['MYSQL_HOST'], "prod_host")
                self.assertEqual(app.config['MYSQL_USER'], "user_prod")
                self.assertEqual(app.config['MYSQL_PASSWORD'], "password_prod")
                self.assertEqual(app.config['MYSQL_DB'], "db_prod")

if __name__ == '__main__':
    unittest.main()