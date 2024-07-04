import os

def print_env():
    env_vars = [
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DB",
        "MYSQL_HOST",
        "SECRET_KEY",
        "MAIL_PASSWORD"
    ]
    
    for var in env_vars:
        print(f"{var}={os.getenv(var)}")

if __name__ == "__main__":
    print_env()