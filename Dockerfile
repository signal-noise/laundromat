FROM python:3.8

COPY ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
RUN pip install gunicorn
RUN pip install -r /code/requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080
ENV GOOGLE_APPLICATION_CREDENTIALS /config/service_account.json
ENV FLASK_APP app
ENV FLASK_RUN_PORT $PORT
ENV FLASK_ENV production
ENV BASE_URL https://laundromat.signalnoise.tools

COPY . /code/
WORKDIR /code

EXPOSE $PORT
CMD gunicorn --bind 0.0.0.0:$PORT manage:app --workers 3