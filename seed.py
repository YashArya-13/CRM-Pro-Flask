from app import create_app, db
from app.models import User, RoleEnum

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        u = User(username="admin", role=RoleEnum.Admin.value)
        u.set_password("admin123")
        db.session.add(u)
        db.session.commit()
        print("Created admin user: admin / admin123")
    else:
        print("Admin exists")
