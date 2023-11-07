# 
FROM python:3.9

# 
#WORKDIR /app

# 
COPY ./requirements.txt /tmp/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

# 
#COPY ./app /app

RUN useradd --create-home twhadm
WORKDIR /home/twhadm
USER twhadm

# 
CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
