"""Authentication endpoints."""
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db, csrf
from ..models import User
from ..schemas import UserSchema

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/login/', methods=['POST'])
@csrf.exempt
def login():
    """Login endpoint - creates session."""
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
    """Logout endpoint - destroys session."""
    logout_user()
    return jsonify({'message': 'Logout successful'})


@bp.route('/me/', methods=['GET'])
@login_required
def current_user_view():
    """Get current authenticated user."""
    return jsonify(UserSchema().dump(current_user))
