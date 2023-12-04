FROM python:3.9

ENV APP_ID_NAME=twhadm

COPY ./requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

COPY ./app /home/${APP_ID_NAME}/app

RUN useradd --create-home ${APP_ID_NAME}
WORKDIR /home/${APP_ID_NAME}
USER ${APP_ID_NAME}

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
