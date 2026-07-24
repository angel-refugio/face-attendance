class TestAuth:
    def test_login_page_loads(self, client):
        response = client.get("/auth/login")
        assert response.status_code == 200

    def test_login_success(self, client, app):
        from app.models.user import User
        from app.extensions import db

        with app.app_context():
            user = User(username="testuser", is_admin=True)
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "password"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_login_invalid(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "wrong", "password": "wrong"},
            follow_redirects=True,
        )
        assert b"incorrectos" in response.data


class TestDashboard:
    def test_dashboard_requires_login(self, client):
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert b"Iniciar Sesion" in response.data

    def test_dashboard_accessible_when_logged_in(self, auth_client):
        response = auth_client.get("/")
        assert response.status_code == 200
        assert b"Dashboard" in response.data


class TestEmployees:
    def test_employees_page(self, auth_client):
        response = auth_client.get("/employees/")
        assert response.status_code == 200

    def test_add_employee(self, auth_client, app):
        response = auth_client.post(
            "/employees/add",
            data={
                "name": "Juan Perez",
                "department": "Ventas",
                "position": "Ejecutivo",
                "email": "juan@test.com",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Juan Perez" in response.data

    def test_add_employee_duplicate(self, auth_client, app):
        auth_client.post(
            "/employees/add",
            data={"name": "Maria Lopez"},
            follow_redirects=True,
        )
        response = auth_client.post(
            "/employees/add",
            data={"name": "Maria Lopez"},
            follow_redirects=True,
        )
        assert b"Ya existe" in response.data


class TestAttendance:
    def test_attendance_page(self, auth_client):
        response = auth_client.get("/attendance/")
        assert response.status_code == 200

    def test_stats_page(self, auth_client):
        response = auth_client.get("/attendance/stats")
        assert response.status_code == 200
