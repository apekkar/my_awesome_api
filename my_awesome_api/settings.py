import os

from dotenv import load_dotenv

load_dotenv()

ENV = str(os.getenv("ENV", "local")).rstrip()
USE_PROXY = os.getenv("USE_PROXY", False)
AWS_REGION = str(os.getenv("MY_AWS_REGION", "eu-west-1")).rstrip()
AWS_PROFILE = str(os.getenv("MY_AWS_PROFILE", None)).rstrip()
AWS_SECRET_NAME = str(os.getenv("AWS_SECRET_NAME")).rstrip()
DATABASE_NAME = str(os.getenv("DATABASE_NAME")).rstrip()
DATABASE_ENDPOINT = str(os.getenv("DATABASE_ENDPOINT")).rstrip()
DATABASE_PORT = int(os.getenv("DATABASE_PORT"))
DATABASE_USERNAME = str(os.getenv("DATABASE_USERNAME")).rstrip()
DATABASE_PASSWORD = str(os.getenv("DATABASE_PASSWORD")).rstrip()
RDS_PROXY_ENDPOINT = str(os.getenv("RDS_PROXY_ENDPOINT")).rstrip()
