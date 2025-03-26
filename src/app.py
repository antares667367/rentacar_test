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
    """
    Initializes and sets up the databases for the rental car application.

    This function creates two PysonDB instances, one for storing car information (carsdb)
    and another for storing user information (usersdb). It also checks if a seed user
    exists in the usersdb. If not, it creates a new user with the username "user",
    password "password", and a hashed skey.

    Returns:
    tuple: A tuple containing the carsdb and usersdb instances.
    """
    carsdb = PysonDB("data/rentacar.cars.json")
    usersdb = PysonDB("data/rentacar.users.json")

    # ####SET SEED USER##################
    # init auth user/password for fake auth.
    if not usersdb.get_by_query(
        lambda x: x["skey"] == sha1("user_password".encode()).hexdigest(),
    ):
        # created only if a matching record is not found
        pp("Creating user")
        usersdb.add(
            {
                "user": "user",
                "password": "password",
                "skey": sha1("user_password".encode()).hexdigest(),
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
    """
    Provide information about available routes in the application.
    This function handles the 'help' route and returns a JSON response
    containing information about all the routes defined in the application.
    Returns:
        flask.Response: A JSON response containing a dictionary with a 'routes' key.
            The value is the result of calling RB.displayroutes(), which likely
            returns a list or dictionary of available routes.
    """
    return jsonify({"routes": RB.displayroutes()})


@app.route(RB.path("login"), methods=["POST"])
def login():
    """
    Authenticate a user and generate an access token.

    This function handles the login process. It receives user credentials
    via a POST request, authenticates the user against the database,
    and returns an access token if authentication is successful.

    Parameters:
    -----------
    None (implicitly uses Flask's request object)

    Returns:
    --------
    flask.Response
        A JSON response containing either:
        - An access token if authentication is successful
        - An error message if authentication fails

    Notes:
    ------
    The function expects 'user' and 'password' fields in the request form data.
    It uses the pass_auth function for authentication and create_access_token
    to generate the JWT token.
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
    """
    Create a new car entry in the database.

    This function handles the creation of a new car entry. It first checks if a car
    with the same details already exists in the database. If not, it adds the new car.
    If a matching car is found, it returns a message indicating that the car already exists.

    The function requires JWT authentication to access.

    Parameters:
    -----------
    None (implicitly uses Flask's request object)

    Returns:
    --------
    flask.Response
        A JSON response containing either:
        - The newly created car details if the car was successfully added
        - A message indicating that the car already exists, along with the existing car details

    Notes:
    ------
    The function expects the car details to be sent in the request form data.
    It uses the carsdb database for querying and adding car entries.
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
    """
    Retrieve car information from the database based on the specified parameter.

    This function handles different types of retrieval operations on the car database.
    It supports retrieving all cars, a specific car by ID, or cars matching a query.

    Parameters:
    -----------
    param : str
        The type of retrieval operation to perform. Valid values are:
        - 'all': Retrieve all cars in the database.
        - 'id': Retrieve a specific car by its ID.
        - 'query': Retrieve cars matching a specific query.

    Returns:
    --------
    flask.Response
        A JSON response containing either:
        - The requested car data if the operation is successful.
        - An error message if the parameter is invalid or the requested ID doesn't exist.

    Raises:
    -------
    pydberr.IdDoesNotExistError
        If the requested ID does not exist in the database when using the 'id' parameter.

    Notes:
    ------
    - The function requires JWT authentication to access.
    - For 'id' and 'query' operations, the necessary data should be provided in the request form.
    - The 'query' operation uses a dictionary created from a comma-separated string of key-value pairs.
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
    """
    Update car information in the database based on the specified parameter.

    This function handles different types of update operations on the car database.
    It supports updating a specific car by ID or updating cars matching a query.

    Parameters:
    -----------
    param : str
        The type of update operation to perform. Valid values are:
        - 'id': Update a specific car by its ID.
        - 'query': Update cars matching a specific query.

    Returns:
    --------
    flask.Response
        A JSON response containing either:
        - The result of the update operation if successful.
        - An error message if the parameter is invalid or the requested ID doesn't exist.

    Raises:
    -------
    pydberr.IdDoesNotExistError
        If the requested ID does not exist in the database when using the 'id' parameter.

    Notes:
    ------
    - The function requires JWT authentication to access.
    - The necessary data for the update operation should be provided in the request form.
    - For 'id' updates, 'id' and 'new_data' fields are required in the form.
    - For 'query' updates, 'query' and 'new_data' fields are required in the form.
    - The 'new_data' and 'query' (for query updates) should be provided as comma-separated strings of key-value pairs.
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
    """
    Delete car information from the database based on the specified parameter.

    This function handles different types of delete operations on the car database.
    It supports purging the entire database, deleting a specific car by ID, or
    deleting cars matching a query.

    Parameters:
    -----------
    param : str
        The type of delete operation to perform. Valid values are:
        - 'purge': Delete all entries in the database.
        - 'id': Delete a specific car by its ID.
        - 'query': Delete cars matching a specific query.

    Returns:
    --------
    flask.Response
        A JSON response containing either:
        - The result of the delete operation if successful.
        - An error message if the parameter is invalid or the requested ID doesn't exist.

    Raises:
    -------
    pydberr.IdDoesNotExistError
        If the requested ID does not exist in the database when using the 'id' parameter.

    Notes:
    ------
    - The function requires JWT authentication to access.
    - For 'id' and 'query' operations, the necessary data should be provided in the request form.
    - The 'query' operation uses a dictionary created from a comma-separated string of key-value pairs.
    - Use the 'purge' option with caution as it deletes all entries in the database.
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
    """
    Convert a comma-separated string of key-value pairs into a dictionary.

    This function takes a string containing key-value pairs separated by commas,
    where each pair is separated by an equals sign, and converts it into a dictionary.

    Parameters:
    -----------
    qstring : str
        A string containing key-value pairs in the format "key1=value1,key2=value2,...".

    Returns:
    --------
    dict
        A dictionary where the keys and values are extracted from the input string.

    Example:
    --------
    >>> dictify("name=John,age=30")
    {'name': 'John', 'age': '30'}
    """
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
