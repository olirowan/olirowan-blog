# Oli Rowan Blog

This repo contains the source code for a blog site built with Flask.
The blog supports Markdown blogpost creation and future edits, tags, comments, dark mode and a management panel.


## Getting Started

Clone this repository, install dependencies, and set environment variables:

```bash
$ git clone https://github.com/olirowan/olirowan-blog.git
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ touch .env
```

Modify the _.env_ to set the following values:

- __SQLALCHEMY_DATABASE_URI__ - Specify a database endpoint (optional, default: SQLite3 file)
- __SERVER_NAME__ - Define which host and port the application is bound to (optional, default: localhost:5000)


Configure the database:

```bash
$ flask db upgrade
```


## Running Locally

Run the application from the command line as follows:

```bash
$ . ./set_env.sh
$ flask run
```


## Running in Production

The application can be run in a container for quick setup.

If you don't wish to use containers then the configuration from _supervisord.conf_ and _nginx-config.conf_ can be used as a reference to stand up the application as you prefer.


## Build in Docker

This will create a container running the frontend application however you will still need celery workers running.

```
docker build -t olirowan/olirowan-blog:v1.0 .

docker run --name olirowan-blog -it \
    -e SQLALCHEMY_DATABASE_URI=mysql://demo:demo@db-host:3306/olirowan-blog \
    -e SERVER_NAME=blog.example.com
    -p 5000:80 -\
    olirowan/olirowan-blog:v1.0
```


## Access Application

You should now be able to access the application at http://localhost:5000/

