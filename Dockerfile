FROM python:3.9

ENV APP_ID_NUMBER=55028
ENV APP_ID_NAME=twhadm
ENV GROUP_ID_NUMBER=1636
ENV GROUP_ID_NAME=appcommon

COPY ./requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt && \
  useradd --create-home -u ${APP_ID_NUMBER} ${APP_ID_NAME}

COPY --chown=${APP_ID_NAME} ./ /home/${APP_ID_NAME}

WORKDIR /home/${APP_ID_NAME}

USER ${APP_ID_NAME}

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
