import resources as resources
import settings as settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routes import router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# When run locally we do not use aws secrets manager to fetch database secrets
if settings.ENV == "local":
    aws_secret_cache = None
else:
    aws_secret_cache = resources.get_secret_cache(region=settings.AWS_REGION)


# Establish database connection outside lambda handler.
# After initialization this singleton database instance
# will be reused as fastapi dependency
my_awesome_database = resources.get_database(
    use_proxy=settings.USE_PROXY, use_secret_cache=aws_secret_cache
)

handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    # to be used in local environment
    import uvicorn

    headers = []
    uvicorn.run(
        app,
        headers=[],
    )
