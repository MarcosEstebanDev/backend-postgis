from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from sqlalchemy import func
from sqlalchemy import exc
import logging



app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/postgres'

# Configuración básica del logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

db = SQLAlchemy(app)
 
print(f"Conectando a la base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}")



# Modelo de estaciones meteorológicas
class WeatherStation(db.Model):
    __tablename__ = 'weather_stations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(Geometry('POINT', srid=4326))  # Definir como tipo 'Point'
    weather_data = db.relationship('WeatherData', backref='station', cascade="all, delete", lazy=True)

# Modelo de datos meteorológicos
class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('weather_stations.id'), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    pressure = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)

with app.app_context():
    db.create_all()
    
# Validación de datos de entrada para coordenadas
def validate_coordinates(latitude, longitude):
    try:
        lat = float(latitude)
        lon = float(longitude)
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return False, "Latitude must be between -90 and 90, and longitude between -180 and 180."
        return True, None
    except ValueError:
        return False, "Invalid latitude or longitude format."

# Validación de entrada para el nombre
def validate_name(name):
    if not name or len(name.strip()) == 0:
        return False, "Name is required and cannot be empty."
    if len(name) > 100:
        return False, "Name cannot exceed 100 characters."
    return True, None

# Validación de JSON de entrada
def validate_json(request_data, required_fields):
    for field in required_fields:
        if field not in request_data:
            return False, f"{field} is required."
    return True, None

@app.route('/weather_stations/<int:id>', methods=['GET'])
def get_station(id):
    if id <= 0:
        return jsonify({'error': 'Invalid ID. ID must be a positive integer.'}), 400

    try:
        # obtener la estación de la base de datos
        station = WeatherStation.query.get(id)

        # Verificar si la estación existe
        if not station:
            return jsonify({'error': f'Station with ID {id} not found'}), 404

        # Convertir la ubicación WKB a texto legible (WKT)
        location = db.session.query(func.ST_AsText(station.location)).scalar()

        # Verificar que la ubicación no sea nula
        if not location:
            return jsonify({'error': 'Location data is missing or corrupted for this station'}), 500

        # Respuesta exitosa con los detalles de la estación
        return jsonify({
            'id': station.id,
            'name': station.name,
            'location': location
        }), 200

    except Exception as e:
        # Manejo genérico de excepciones
        logger.error(f"Error retrieving station with ID {id}: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred while retrieving the station'}), 500

@app.route('/weather_stations/create', methods=['POST'])
def create_weather_station():
    data = request.get_json()

    # Validar que los datos requeridos existan
    name = data.get('name')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    # Validar que el nombre no esté vacío
    if not name or not isinstance(name, str):
        return jsonify({"error": "Station name is required and must be a string."}), 400

    # Validar que la latitud y longitud sean valores numéricos
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (ValueError, TypeError):
        return jsonify({"error": "Latitude and longitude must be valid numbers."}), 400

    # Validar el rango de latitud y longitud
    if not (-90 <= latitude <= 90):
        return jsonify({"error": "Latitude must be between -90 and 90 degrees."}), 400
    if not (-180 <= longitude <= 180):
        return jsonify({"error": "Longitude must be between -180 and 180 degrees."}), 400

    # Crear la ubicación como un objeto Geometry usando ST_GeomFromText
    try:
        location = func.ST_GeomFromText(f"POINT({longitude} {latitude})", 4326)
    except Exception as e:
        return jsonify({"error": f"Error processing location data: {str(e)}"}), 500

    try:
        # Crear la nueva estación y agregarla a la base de datos
        new_station = WeatherStation(name=name, location=location)
        db.session.add(new_station)
        db.session.commit()

        # Respuesta exitosa, devolviendo los datos de la nueva estación
        return jsonify({
            "id": new_station.id, 
            "name": new_station.name, 
            "location": f"POINT({longitude} {latitude})"
        }), 201

    except exc.SQLAlchemyError as e:
        # Revertir la transacción si ocurre un error en la base de datos
        db.session.rollback()
        logger.error(f"Error al insertar estación: {str(e)}")  # Registrar el error
        return jsonify({"error": "An error occurred while creating the weather station. Please try again."}), 500
    except Exception as e:
        # Manejar cualquier otro error inesperado
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

    
@app.route('/weather_stations/closest', methods=['GET'])
def get_closest_station():
    # Obtener los parámetros de latitud y longitud
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    
    # Verificar que los parámetros existan
    if not latitude or not longitude:
        logger.warning('Latitude and longitude are required but not provided.')
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    latitude = float(latitude)
    longitude = float(longitude)
    
    # Crear la ubicación de consulta
    location = f"POINT({longitude} {latitude})"
    
    # Encontrar la estación más cercana
    logger.debug(f"Consultando la estación más cercana a la ubicación: {latitude}, {longitude}")
    
    closest_station = db.session.query(WeatherStation).order_by(
        func.ST_Distance(WeatherStation.location, func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326))
    ).first()

    # Verificar si se ha encontrado la estación más cercana
    if not closest_station:
        logger.warning('No stations found near the given location.')
        return jsonify({'error': 'No stations found'}), 404
    
    logger.info(f"Estación más cercana: {closest_station.name} con ID: {closest_station.id}")
    
    # Obtener los datos meteorológicos más recientes
    latest_data = WeatherData.query.filter_by(station_id=closest_station.id).order_by(WeatherData.timestamp.desc()).first()

    # Verificar si se encontraron datos meteorológicos
    if not latest_data:
        logger.warning(f"No weather data available for station ID {closest_station.id}")
        return jsonify({'error': 'No weather data available for this station'}), 404
    
    logger.info(f"Últimos datos meteorológicos para la estación {closest_station.name}: "
                f"Temperatura: {latest_data.temperature}, Humedad: {latest_data.humidity}, "
                f"Presión: {latest_data.pressure}, Timestamp: {latest_data.timestamp}")
    
    return jsonify({
        'station_name': closest_station.name,
        'location': closest_station.location,
        'latest_data': {
            'temperature': latest_data.temperature,
            'humidity': latest_data.humidity,
            'pressure': latest_data.pressure,
            'timestamp': latest_data.timestamp
        }
    })
    
@app.route('/weather_stations/update/<int:id>', methods=['PUT'])
def update_station(id):
    # Obtener la estación existente
    try:
        station = WeatherStation.query.get_or_404(id)
    except Exception as e:
        logger.error(f"Error fetching station with ID {id}: {str(e)}")
        return jsonify({"error": f"Station with ID {id} not found"}), 404

    # Obtener los datos del request
    data = request.get_json()

    # Validar y actualizar el nombre si se proporciona
    if 'name' in data:
        name = data['name']
        if not isinstance(name, str) or not name.strip():
            return jsonify({"error": "Station name is required and must be a valid non-empty string."}), 400
        station.name = name

    # Validar y actualizar la ubicación si se proporcionan 'latitude' y 'longitude'
    if 'latitude' in data and 'longitude' in data:
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])

            # Validar que la latitud y longitud estén dentro de los rangos correctos
            if not (-90 <= latitude <= 90):
                return jsonify({"error": "Latitude must be between -90 and 90 degrees."}), 400
            if not (-180 <= longitude <= 180):
                return jsonify({"error": "Longitude must be between -180 and 180 degrees."}), 400

            # Crear la nueva ubicación como un objeto Geometry
            station.location = func.ST_GeomFromText(f"POINT({longitude} {latitude})", 4326)

        except (ValueError, TypeError):
            return jsonify({"error": "Latitude and longitude must be valid numbers."}), 400
        except Exception as e:
            logger.error(f"Error processing location data: {str(e)}")
            return jsonify({"error": "Error processing location data."}), 500

    try:
        # Confirmar los cambios en la base de datos
        db.session.commit()

        # Convertir la ubicación a un formato serializable (WKT)
        location = func.ST_AsText(station.location)
        location_text = db.session.execute(location).scalar()

        # Respuesta exitosa con los datos actualizados
        return jsonify({
            'id': station.id,
            'name': station.name,
            'location': location_text
        }), 200

    except exc.SQLAlchemyError as e:
        # Revertir la transacción si ocurre un error en la base de datos
        db.session.rollback()
        logger.error(f"Error updating station: {str(e)}")
        return jsonify({"error": "An error occurred while updating the weather station. Please try again."}), 500
    except Exception as e:
        # Manejar cualquier otro error inesperado
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

@app.route('/weather_stations/delete/<int:id>', methods=['DELETE'])
def delete_station(id):
    try:
        # Intentar obtener la estación por ID
        station = WeatherStation.query.get_or_404(id)
    except Exception as e:
        logger.error(f"Error fetching station with ID {id}: {str(e)}")
        return jsonify({"error": f"Station with ID {id} not found."}), 404

    try:
        # Eliminar la estación si se encuentra
        db.session.delete(station)
        db.session.commit()
        logger.info(f"Station with ID {id} deleted successfully.")

        return jsonify({'message': 'Station deleted successfully'}), 200

    except exc.SQLAlchemyError as e:
        # Revertir la transacción si ocurre un error al eliminar
        db.session.rollback()
        logger.error(f"Error deleting station with ID {id}: {str(e)}")
        return jsonify({"error": "An error occurred while deleting the station. Please try again."}), 500
    except Exception as e:
        # Manejar cualquier otro error inesperado
        logger.error(f"Unexpected error during station deletion: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

if __name__ == '__main__':
    app.run(debug=True)