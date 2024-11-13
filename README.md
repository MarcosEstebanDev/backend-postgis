# Weather Station API

This is a **Flask-based RESTful API** for managing weather stations and their meteorological data. It allows users to create, retrieve, update, and delete weather stations, as well as retrieve weather data for the closest station based on geographic coordinates.

## Table of Contents
- [Project Setup](#project-setup)
- [Database Configuration](#database-configuration)
- [API Endpoints](#api-endpoints)
  - [GET /weather_stations/:id](#get-weather_stationsid)
  - [POST /weather_stations/create](#post-weather_stationscreate)
  - [GET /weather_stations/closest](#get-weather_stationsclosest)
  - [PUT /weather_stations/update/:id](#put-weather_stationsupdateid)
  - [DELETE /weather_stations/delete/:id](#delete-weather_stationsdeleteid)
- [Logging](#logging)
- [Error Handling](#error-handling)

---

## Project Setup

### Requirements
To run this project, you'll need to have the following installed:
- Python 3.8+
- PostgreSQL with PostGIS extension
- Flask
- SQLAlchemy
- GeoAlchemy2

### Installation Steps

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/weather-station-api.git
    cd weather-station-api
    ```

2. Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up the PostgreSQL database:
    - Install PostgreSQL and enable the PostGIS extension.
    - Create a database and configure the connection URI in `app.config['SQLALCHEMY_DATABASE_URI']`.

    Example:
    ```python
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/postgres'
    ```

4. Run the Flask application:
    ```bash
    flask run
    ```

## Database Configuration

The application uses **SQLAlchemy** and **GeoAlchemy2** to interact with a PostgreSQL database. The models defined are:
- `WeatherStation`: Stores information about the station, including its name and geographic location.
- `WeatherData`: Stores the meteorological data such as temperature, humidity, and pressure for each station.

### Example Models:
```python
class WeatherStation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(Geometry('POINT', srid=4326))
    weather_data = db.relationship('WeatherData', backref='station', cascade="all, delete", lazy=True)

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('weather_stations.id'), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    pressure = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)
