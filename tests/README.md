# Running Tests

The test suite tests the functionalities of the MVG client library. Some of these test cases involves a network call to the API, the `vibium-cloud` service.

## Test against a local instance of the API
Assuming that the API runs on the host `http://localhost:8000`, use the host argument of `pytest` to run the tests against the local API instance.

```bash
python -m pytest tests --host "http://localhost:8000"
```

## Test against a local instance of the AWS infrastructure
The `vibium-cloud` service is hosted on a AWS infrastructure and it is possible to clone the entire infrastructure locally. This way we run the test suite against a specific or the production version of the `vibium-cloud` service.

Prerequisites:
- Docker
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)


Create an environment file named `services.env` in the `tests` folder with the following content
```env
AWS_DEFAULT_REGION=<AWS_DEFAULT_REGION>
AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>
AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY>
AWS_ECR=<AWS_ECR>
VIBIUM_VERSION=prod
```
_The text within <> should be replaced with valid values_

Login to AWS
```bash
aws ecr auth
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
```

Run docker compose to setup the AWS infrastructure
```bash
docker compose --env-file=services.env up -d
```

Monitor the logs of the docker container `tests-vibium-api-1` to know if the service has started. If the service has started, the logs for the container would contain the below text
```text
tests-vibium-api-1     | 2022-10-11 10:29:30,890 - INFO - vibium_app.main - Creating manager FastApi application...
tests-vibium-api-1     | INFO:     Started server process [9]
tests-vibium-api-1     | 2022-10-11 10:29:31,049 - INFO - uvicorn.error - Started server process [9]
tests-vibium-api-1     | INFO:     Waiting for application startup.
tests-vibium-api-1     | 2022-10-11 10:29:31,049 - INFO - uvicorn.error - Waiting for application startup.
tests-vibium-api-1     | INFO:     Application startup complete.
tests-vibium-api-1     | 2022-10-11 10:29:31,050 - INFO - uvicorn.error - Application startup complete.
tests-vibium-api-1     | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
tests-vibium-api-1     | 2022-10-11 10:29:31,050 - INFO - uvicorn.error - Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

If all has been well so far, then the `vibium-cloud` service should be running on `http://localhost:8000`. The test suite can be run against this host as follows:

```bash
python -m pytest tests --host "http://localhost:8000"
```
