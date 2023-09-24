from flask import Blueprint

bp = Blueprint('views', __name__)


@bp.route('/test_views')
def index():
    return "This is an example app"
