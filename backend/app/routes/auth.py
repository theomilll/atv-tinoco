"""Authentication endpoints."""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import csrf
from ..models import User
from ..schemas import UserSchema

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/login/', methods=['GET', 'POST'])
@csrf.exempt
def login():
    """Login endpoint - creates session.
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      400:
        description: Missing credentials
      401:
        description: Invalid credentials
    """
    if request.method == 'GET':
        # Return empty response for CSRF token fetch
        return jsonify({'status': 'ready'})

    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user)
        return jsonify({
            'user': UserSchema().dump(user),
            'message': 'Login successful'
        })

    return jsonify({'error': 'Invalid credentials'}), 401


@bp.route('/logout/', methods=['POST'])
@login_required
@csrf.exempt
def logout():
    """Logout endpoint - destroys session.
    ---
    tags:
      - Auth
    security:
      - cookieAuth: []
    responses:
      200:
        description: Logout successful
      401:
        description: Not authenticated
    """
    logout_user()
    return jsonify({'message': 'Logout successful'})


@bp.route('/me/', methods=['GET'])
@login_required
def current_user_view():
    """Get current authenticated user.
    ---
    tags:
      - Auth
    security:
      - cookieAuth: []
    responses:
      200:
        description: Current user info
        schema:
          type: object
          properties:
            id:
              type: integer
            username:
              type: string
            email:
              type: string
      401:
        description: Not authenticated
    """
    return jsonify(UserSchema().dump(current_user))
