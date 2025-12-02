"""Health check endpoint."""
from flask import Blueprint, jsonify

bp = Blueprint('health', __name__, url_prefix='/api')


@bp.route('/health/', methods=['GET'])
def health_check():
    """Health check endpoint.
    ---
    tags:
      - Health
    responses:
      200:
        description: Service is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
    """
    return jsonify({'status': 'ok'})
