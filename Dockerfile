FROM python:3.9

ENV APP_ID_NUMBER=9999
ENV APP_ID_NAME=twhadm
ENV GROUP_ID_NUMBER=1636
ENV GROUP_ID_NAME=appcommon

RUN useradd --create-home ${APP_ID_NAME} --uid ${APP_ID_NUMBER} && \
    groupadd --gid ${GROUP_ID_NUMBER} ${GROUP_ID_NAME} && \
    usermod -a -G ${GROUP_ID_NAME} ${APP_ID_NAME}

WORKDIR /home/${APP_ID_NAME}

COPY ./requirements.txt ./requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --upgrade -r /home/${APP_ID_NAME}/requirements.txt

USER ${APP_ID_NAME}

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
