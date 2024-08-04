import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/people', methods=['GET'])
def get_people():
    people = People.query.all()
    serialized_people = []
    for person in people:
        serialized_people.append(person.serialize())
    return jsonify(serialized_people), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = People.query.get(people_id)
    if not person:
        return jsonify({"message": "Person not found"}), 404
    return jsonify(person.serialize()), 200

@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    serialized_planet = []
    for person in planets:
        serialized_planet.append(person.serialize())
    return jsonify(serialized_planet), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"message": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    serialized_user = []
    for person in users:
        serialized_user.append(person.serialize()) #Serializar a cada usuario de todos los usuarios
    return jsonify(serialized_user), 200

@app.route('/users/favorites', methods=['GET']) # ?user_id=1 -----> Esto se agrega al final de la ruta para indicar el usuario a realizar la consulta
def get_user_favorites():
    user_id = request.args.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    favorite_planets = []
    favorite_people = []
    for planet in user.favorite_planets:
        favorite_planets.append(planet.serialize())
    for person in user.favorite_people:
        favorite_people.append(person.serialize())
    favorites = {
        "favorite_planets": favorite_planets,
        "favorite_people": favorite_people
    }
    return jsonify(favorites), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user_id = request.json.get('user_id')
    user = User.query.get(user_id)
    planet = Planet.query.get(planet_id)
    if user and planet:
        user.favorite_planets.append(planet)
        db.session.commit()
        return jsonify({"message": "Planet added to favorites"}), 200
    return jsonify({"message": "User or Planet not found"}), 404

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    user_id = request.json.get('user_id')
    user = User.query.get(user_id)
    person = People.query.get(people_id)
    if user and person:
        user.favorite_people.append(person)
        db.session.commit()
        return jsonify({"message": "Person added to favorites"}), 200
    return jsonify({"message": "User or Person not found"}), 404

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def remove_favorite_planet(planet_id):
    user_id = request.json.get('user_id')
    user = User.query.get(user_id)
    planet = Planet.query.get(planet_id)
    if user and planet:
        user.favorite_planets.remove(planet)
        db.session.commit()
        return jsonify({"message": "Planet removed from favorites"}), 200
    return jsonify({"message": "User or Planet not found"}), 404

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def remove_favorite_people(people_id):
    user_id = request.json.get('user_id')
    user = User.query.get(user_id)
    person = People.query.get(people_id)
    if user and person:
        user.favorite_people.remove(person)
        db.session.commit()
        return jsonify({"message": "Person removed from favorites"}), 200
    return jsonify({"message": "User or Person not found"}), 404

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
