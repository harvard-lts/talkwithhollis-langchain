# talkwithhollis-langchain
Talk with HOLLIS: Intelligent semantic book search using Generative AI

# Quick start

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
