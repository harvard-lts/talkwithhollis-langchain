# talkwithhollis-langchain
Talk with HOLLIS: Intelligent semantic book search using Generative AI

# Local development environment

## Docker compose local

Build image with no cache and run containers

```
docker compose -f docker-compose-local.yml build --no-cache && docker compose -f docker-compose-local.yml up -d
```

## Installing packages

Exec into the container

```
docker exec -it twhapi bash
```

Run pip install and pip freeze to update the requirements.txt file

```
pip install packagename && pip freeze > requirements.txt
```

## AWS credentials

Create an [AWS credentials file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) and [add a profile](https://docs.aws.amazon.com/cli/latest/reference/configure/#synopsis).

```
aws configure --profile talkwithhollis
```

Install the AWS CLI locally, or run in a docker container.

To run the AWS CLI commands in a (separate from the app) docker container, run the amazon/aws-cli image, mount in the ~/.aws directory into the container, and specify the aws-cli command.

```
docker run --rm -it -v ~/.aws:/root/.aws amazon/aws-cli configure --profile talkwithhollis
```

Enter the access key id, secret access key, and region. A new entry in the `~/.aws/credentials` file will be created. Path to AWS credentials file: `$HOME/.aws/credentials`. Note that the region is required.

Entry in the credentials file:

```
[talkwithhollis]
aws_access_key_id = <access key id>
aws_secret_access_key = <secret key>
region = us-east-1
```

Profile name

The profile name in the credentials file must match the profile name `AWS_BEDROCK_PROFILE_NAME` in the .env.

```
AWS_BEDROCK_PROFILE_NAME=talkwithhollis
```

The `~/.aws/credentials` file is mounted into the app container as a volume in `docker-compose-local.yml`.
