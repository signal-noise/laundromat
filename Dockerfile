FROM python:3.8

COPY ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
RUN pip install gunicorn
RUN pip install -r /code/requirements.txt

ARG SECRET_KEY=supersecretstring
ARG GITHUB_CLIENT_ID
ARG GITHUB_CLIENT_SECRET
ARG BASE_URL
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080
ENV SECRET_KEY ${SECRET_KEY}
ENV GITHUB_CLIENT_ID ${GITHUB_CLIENT_ID}
ENV GITHUB_CLIENT_SECRET ${GITHUB_CLIENT_SECRET}
ENV GOOGLE_APPLICATION_CREDENTIALS /config/service_account.json
ENV FLASK_APP app
ENV FLASK_RUN_PORT $PORT
ENV FLASK_ENV production
ENV BASE_URL ${BASE_URL}}

RUN mkdir -p /config
COPY ./config /config/

COPY . /code/
WORKDIR /code

EXPOSE $PORT
CMD gunicorn --bind 0.0.0.0:$PORT manage:app --workers 3