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
```

## API Endpoints

### GET `/weather_stations/:id`
Retrieve information about a specific weather station by its ID.

- **Parameters**: `id` (required) - The ID of the weather station to retrieve.
- **Description**: This endpoint returns detailed information about a specific weather station, including its name and location.

### POST `/weather_stations/create`
Create a new weather station by providing its name and geographic coordinates.

- **Body Parameters**: 
  - `name` (required) - The name of the weather station.
  - `latitude` (required) - Latitude of the station location.
  - `longitude` (required) - Longitude of the station location.
- **Description**: This endpoint allows the creation of a new weather station by specifying its name and geographic coordinates.

### GET `/weather_stations/closest`
Retrieve the closest weather station to a given geographic point.

- **Query Parameters**: 
  - `latitude` (required) - Latitude of the point to search from.
  - `longitude` (required) - Longitude of the point to search from.
- **Description**: This endpoint returns the closest weather station to the given latitude and longitude.

### PUT `/weather_stations/update/:id`
Update the details of an existing weather station by its ID.

- **Parameters**: `id` (required) - The ID of the weather station to update.
- **Body Parameters**: 
  - `name` (optional) - Updated name of the station.
  - `latitude` (optional) - Updated latitude.
  - `longitude` (optional) - Updated longitude.
- **Description**: This endpoint allows updating an existing weather station's information.

### DELETE `/weather_stations/delete/:id`
Delete a specific weather station by its ID.

- **Parameters**: `id` (required) - The ID of the weather station to delete.
- **Description**: This endpoint deletes a weather station from the database.

---

## Logging

The API uses Python's built-in `logging` module to record different levels of logs:

- **Info**: Successful requests and operations are logged.
- **Warning**: Invalid input data or attempts to access non-existent resources.
- **Error**: Internal server errors or issues while processing a request.

### MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
