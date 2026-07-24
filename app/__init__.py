import logging
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app(config_override=None):
    app = Flask(__name__)

    from app.config import Settings

    settings = Settings()

    app.config["DEBUG"] = settings.DEBUG
    app.config["HOST"] = settings.HOST
    app.config["PORT"] = settings.PORT
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ADMIN_USERNAME"] = settings.ADMIN_USERNAME
    app.config["ADMIN_PASSWORD"] = settings.ADMIN_PASSWORD
    app.config["FACES_DIR"] = settings.FACES_DIR
    app.config["CONFIDENCE_THRESHOLD"] = settings.CONFIDENCE_THRESHOLD
    app.config["DUPLICATE_WINDOW_MINUTES"] = settings.DUPLICATE_WINDOW_MINUTES
    app.config["LOG_LEVEL"] = settings.LOG_LEVEL

    if config_override:
        app.config.update(config_override)

    from app.extensions import db, login_manager, migrate

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.main import main_bp
    from app.routes.employees import employees_bp
    from app.routes.attendance import attendance_bp
    from app.routes.camera import camera_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(employees_bp, url_prefix="/employees")
    app.register_blueprint(attendance_bp, url_prefix="/attendance")
    app.register_blueprint(camera_bp, url_prefix="/camera")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    with app.app_context():
        db.create_all()
        _create_admin_user(app, db)

    app.logger.info("FaceAttendance iniciado correctamente")
    return app


def _create_admin_user(app, db):
    from app.models.user import User

    if not User.query.filter_by(username=app.config["ADMIN_USERNAME"]).first():
        admin = User(
            username=app.config["ADMIN_USERNAME"],
            is_admin=True,
        )
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        app.logger.info(f"Admin user '{app.config['ADMIN_USERNAME']}' created")
