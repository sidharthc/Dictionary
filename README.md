#{{cookiecutter.github_repository_name}}
---------------------------------------------------
{{cookiecutter.description}}. Check out the project's [documentation](https://github.com/{{cookiecutter.github_username}}/{{cookiecutter.github_repository_name}}/).

# Introduction

# Developer Guide

## Getting Started

### Prerequisites
- [virtualenv](https://virtualenv.pypa.io/en/latest/)

### Initialize the project
Create and activate a virtualenv:

```bash
virtualenv env
source env/bin/activate
```
Install dependencies:

```bash
pip install -r requirements.txt
```
Initialize the git repository

```
git init
git remote add origin git@github.com:{{cookiecutter.github_username}}/{{cookiecutter.github_repository_name}}.git
```

Migrate, create a superuser, and run the server:
```bash
python manage.py migrate
python manage.py makemigrations {{cookiecutter.project_name}}
python manage.py createsuperuser
python manage.py runserver
```

## Changing Database

## Static Files

## Running Test Cases

## Setting Up Travis

## Setting Up Circleci


