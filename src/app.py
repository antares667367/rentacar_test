from datetime import timedelta
from hashlib import sha1
from pprint import pprint as pp

from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from pysondb import PysonDB
from pysondb import errors as pydberr

from src import RoutesBuilder, pass_auth, rentacar_args

# init flask app
app = Flask(__name__)
jwt = JWTManager(app)
# config token access secret key
app.config["SECRET_KEY"] = "004f2af45d3a4e161a7dd2d17fdae47f"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
# init json databases
def databases_setup():
    carsdb = PysonDB("data/rentacar.cars.json")
    usersdb = PysonDB("data/rentacar.users.json")

    # ####SET SEED USER##################
    # init auth user/password for  fake auth (but look for it first)
    if not usersdb.get_by_query(
        lambda x: x["skey"] == sha1("userpassword".encode()).hexdigest(),
    ):
        # created only if a matching record is not found
        pp("Creating user")
        usersdb.add(
            {
                "user": "user",
                "password": "password",
                "skey": sha1("userpassword".encode()).hexdigest(),
            }
        )

    return carsdb, usersdb


carsdb, usersdb = databases_setup()
##### SET ROUTES FOR ROUTES BUILDER#############
RB = RoutesBuilder("/rentacar")
## crud part
RB.add_path("__crud", "crud")
RB.add_path("create", "create", extends="__crud")
RB.add_path(
    "retrieve", "retrieve/<param>", extends="__crud", varia=["all", "id", "query"]
)
RB.add_path("update", "update/<param>", extends="__crud", varia=["id", "query"])
RB.add_path(
    "delete", "delete/<param>", extends="__crud", varia=["id", "query", "purge"]
)
## auth part
RB.add_path("__auth", "auth")
RB.add_path("login", "login", extends="__auth")
# Help part
RB.add_path("help", "help")
###### ROUTES #############################


@app.route(RB.path("help"), methods=["POST"])
def help():
    """test route
    TEST

    Returns:
        routes
    """
    return jsonify({"routes": RB.displayroutes()})


@app.route(RB.path("login"), methods=["POST"])
def login():
    """Login route
    LOGIN

    Returns:
        json:the result of the query
    """
    RQF = request.form
    passed, user = pass_auth(RQF["user"], RQF["password"], usersdb)
    if passed:
        return jsonify(
            {
                "token": create_access_token(identity=user["skey"]),
            }
        )
    return jsonify({"message": "Auth failed, User not recognized. "})


@app.route(RB.path("create"), methods=["POST"])
@jwt_required()
def create():
    """Create a new car in the database
    CREATE

    Returns:
         json:the result of the query
    """
    RQF = request.form
    search = carsdb.get_by_query(lambda x: all(x[k] == v for k, v in RQF.items()))
    if not search:  # if not found, insert
        op = carsdb.add(RQF)
        return jsonify({"msg": carsdb.get_by_id(op)})
    # otherwise , return message
    return jsonify({"msg": "The car already exists", "car": search})


@app.route(RB.path("retrieve"), methods=["POST"])
@jwt_required()
def retrieve(param):
    """Retrieve a specific car/all cars from the database
    RETRIEVE
    Args:
        param str: param to supply to the route
        XX/XX/retrieve/<all|id|query>
    Returns:
        json: The result of the query
    """
    RQF = request.form
    params = {
        "all": lambda: carsdb.get_all(),
        "id": lambda: carsdb.get_by_id(RQF["id"]),
        "query": lambda: carsdb.get_by_query(
            lambda x: all(x[k] == v for k, v in dictify(RQF["query"]).items())
        ),
    }
    if param not in params:
        return jsonify({"msg": f"parameter {param} invalid. Accepts [all/id/query]"})
    try:
        return params[param]()
    except pydberr.IdDoesNotExistError:
        return jsonify({"msg": "The requested id does not exist in the database"})


@app.route(RB.path("update"), methods=["POST"])
@jwt_required()
def update(param):
    """Retrieve a specific car/all cars from the database
    UPDATE
    Args:
        param str: param to supply to the route
        XX/XX/update/<id|query>


    Returns:
        json: The result of the query
    """
    RQF = request.form
    params = {
        "id": lambda: carsdb.update_by_id(RQF["id"], dictify(RQF["new_data"])),
        "query": lambda: carsdb.update_by_query(
            query=lambda x: all(x[k] == v for k, v in dictify(RQF["query"]).items()),
            new_data=dictify(RQF["new_data"]),
        ),
    }
    if param not in params:
        return jsonify({"msg": f"parameter {param} invalid. Accepts [id/query]"})
    try:
        return params[param]()
    except pydberr.IdDoesNotExistError:
        return jsonify({"msg": "The requested id does not exist in the database"})


@app.route(RB.path("delete"), methods=["POST"])
@jwt_required()
def delete(param):
    """Delete a specific car/all cars from the database
    DELETE
    Args:
    param str: param to supply to the route
    XX/XX/delete/<purge|id|query>

    Returns:
        [type]: [description]
    """
    RQF = request.form
    params = {
        "purge": lambda: carsdb.purge(),  ## WARNING , purges the database
        "id": lambda: carsdb.delete_by_id(RQF["id"]),
        "query": lambda: carsdb.delete_by_query(
            lambda x: all(x[k] == v for k, v in dictify(RQF["query"]).items())
        ),
    }
    if param not in params:
        return jsonify({"msg": f"parameter {param} invalid. Accepts [purge/id/query]"})
    try:
        exc = params[param]()
        return jsonify({"msg": exc})
    except pydberr.IdDoesNotExistError:
        return jsonify({"msg": "The requested id does not exist in the database"})


def dictify(qstring: str) -> dict:
    """Transforms a query string into a dict"""
    stor = {}
    Q = qstring.split(",")
    for q in Q:
        s = q.split("=")
        stor[s[0]] = s[1]

    return stor


# main
if __name__ == "__main__":
    __args = rentacar_args()  # set in rentacar_args // tools.arguments
    app.run(debug=__args.debug, port=__args.port, host=__args.host)
