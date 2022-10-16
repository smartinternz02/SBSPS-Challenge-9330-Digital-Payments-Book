FROM python:3.6-slim-buster
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
# define the command to start the container
COPY . /app
CMD ["python","./app.py"]