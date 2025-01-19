# Use an official Python runtime as the base image
FROM python:3.9

WORKDIR /app

COPY . /app

RUN pip install feedparser
RUN pip install requests
RUN pip install atproto

CMD ["python", "bluesky.py"]
