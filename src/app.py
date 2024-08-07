import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet

from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager

app = Flask(__name__)
app.url_map.strict_slashes = False

app.config["JWT_SECRET_KEY"] = "griffith"
jwt = JWTManager(app)

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
    all_people = list(map(lambda x: x.serialize(), people))
    return jsonify(all_people), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = People.query.get(people_id)
    if not person:
        return jsonify({"message": "Person not found"}), 404
    return jsonify(person.serialize()), 200

@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    all_planets = list(map(lambda x: x.serialize(), planets))
    return jsonify(all_planets), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"message": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    all_users = list(map(lambda x: x.serialize(), users))
    return jsonify(all_users), 200

@app.route('/users/favorites', methods=['GET'])
@jwt_required()
def get_user_favorites():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    favorite_planets = list(map(lambda planet: planet.serialize(), user.favorite_planets))
    favorite_people = list(map(lambda person: person.serialize(), user.favorite_people))
    favorites = {
        "favorite_planets": favorite_planets,
        "favorite_people": favorite_people
    }
    return jsonify(favorites), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
@jwt_required()
def add_favorite_planet(planet_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    planet = Planet.query.get(planet_id)
    if user and planet:
        user.favorite_planets.append(planet)
        db.session.commit()
        return jsonify({"message": "Planet added to favorites"}), 200
    return jsonify({"message": "User or Planet not found"}), 404

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
@jwt_required()
def add_favorite_people(people_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    person = People.query.get(people_id)
    if user and person:
        user.favorite_people.append(person)
        db.session.commit()
        return jsonify({"message": "Person added to favorites"}), 200
    return jsonify({"message": "User or Person not found"}), 404

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite_planet(planet_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    planet = Planet.query.get(planet_id)
    if user and planet:
        user.favorite_planets.remove(planet)
        db.session.commit()
        return jsonify({"message": "Planet removed from favorites"}), 200
    return jsonify({"message": "User or Planet not found"}), 404

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite_people(people_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    person = People.query.get(people_id)
    if user and person:
        user.favorite_people.remove(person)
        db.session.commit()
        return jsonify({"message": "Person removed from favorites"}), 200
    return jsonify({"message": "User or Person not found"}), 404

@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    if email is None or password is None:
        return jsonify({"msg": "Bad username or password"}), 401
    user_query = User.query.filter_by(email=email)
    user = user_query.first()
    if user is None:
        return jsonify({"msg": "Bad username or password"}), 401
    if user.email != email or user.password != password:
        return jsonify({"msg": "Bad username or password"}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token)

@app.route("/current-user", methods=["GET"])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    if current_user_id is None:
        return jsonify({"msg": "User not found"}), 401
    user_query = User.query.get(current_user_id)
    if user_query is None:
        return jsonify({"msg": "User not found"}), 401
    user = user_query.serialize()
    return jsonify(current_user=user), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
