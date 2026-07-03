# LandSeaLot Metadata Form

A Streamlit web application developed for the LandSeaLot project to validate, process, enrich, and upload sensor datasets to Zenodo.

## Features
- Interactive web interface built with Streamlit.
- Metadata generation compliant with the LandSeaLot metadata model.
- Automatic generation of metadata files.
- Dataset validation and preprocessing.
- Zenodo upload (Sandbox or Production).
- Docker support for simplified deployment.

## Project Structure
.
├── config.py
├── docker-compose.yml
├── Dockerfile
├── log_config.yaml
├── main.py
├── metadata/
├── modules/
├── parsers/
├── resources/
├── static/
├── requirements.txt
└── README.md

## Requirements
Python 3.10
A Zenodo API token
Docker and Docker Compose (optional)
Environment Variables
Uploads to Zenodo require a .env file located in the root directory of the project.
Create a file named .env with the following content:

`ZENODO_TOKEN=<your zenodo api token>`

Replace <your zenodo api token> with your personal Zenodo (or Zenodo Sandbox) API token.
Without this file, uploads to Zenodo will not work.
It is recommended to include .env in .gitignore so that the token is never committed to the repository.

## Running Locally
Create a virtual environment:

`python -m venv .venv`

Activate it.
Linux/macOS:
`source .venv/bin/activate`

Windows:
`.venv\Scripts\activate`

Install the dependencies:
`pip install -r requirements.txt`

Start the application:
`streamlit run main.py`

The application will be available at:

http://localhost:8501

## Running with Docker
Update the values of the volumes binds in the docker-compose.yml file.
Build and start the application using Docker Compose:

`docker compose up --build`

Or, if using an older Docker Compose installation:

`docker-compose up --build`

The application will be available at:

http://localhost:8501

## Configuration
Most application settings are defined in:

config.py
resources/
log_config.yaml
License

*Developed as part of the LandSeaLot project.*