FROM python:3.9

WORKDIR /fastapi_app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod a+x docker/start.sh

CMD ["docker/start.sh"]