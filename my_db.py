from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class UserTable(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096))
    user_id = db.Column(db.Integer)
    token = db.Column(db.String(4096))
    login = db.Column(db.Integer)
    access_level = db.Column(db.Integer)

    def __init__(self, name, user_id, token, login, access_level):
        self.name = name
        self.user_id = user_id
        self.token = token
        self.login = login
        self.access_level = access_level

def delete_all():
    try:
        db.session.query(UserTable).delete()
        db.session.commit()
    except Exception as e:
        print("Delete failed " + str(e))
        db.session.rollback()


def get_user_row_if_exists(user_id):
    user_row = UserTable.query.filter_by(user_id=user_id).first()
    if user_row is not None:
        return user_row
    else:
        print(f"The user with id {user_id} does not exist")
        return False



def add_user_and_login(name, user_id):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        row.login = 1
        db.session.commit()
    else:
        print(f"Adding {user_id}")
        new_user = UserTable(name, user_id, None, 1, 0)
        db.session.add(new_user)
        db.session.commit()



def user_logout(user_id):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        row.login = 0
        db.session.commit()


def add_token(user_id, token):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        row.token = token
        db.session.commit()


def get_token(user_id):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        return row.token
    else:
        print(f"User {user_id} does not exist")


def view_all():
    row = UserTable.query.all()
    for n in range(0, len(row)):
        print(f"{row[n].id} | {row[n].name} | {row[n].user_id} | {row[n].token} | {row[n].access_level}")


def get_all_logged_in_users():
    row = UserTable.query.filter_by(login=1).all()
    user_records = {"users" : []}
    for n in range(0, len(row)):
        if row[n].access_level == 1:
            read = "checked"
            write = "unchecked"
        elif row[n].access_level == 2:
            read = "checked"
            write = "checked"
        else:
            read = "unchecked"
            write = "unchecked"
        user_records["users"].append([row[n].name, row[n].user_id, read, write])
    return user_records


def add_user_permission(user_id, read, write):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        if read == "true" and write =="true":
            row.access_level = 2
        elif read == "true":
            row.access_level = 1
        else:
            row.access_level = 0
        db.session.commit()
    else:
        add_user_and_login("sensor", user_id)


def get_user_access(user_id):
    row = get_user_row_if_exists(user_id)
    if row is not False:
        user_row = UserTable.query.filter_by(user_id=user_id).first()
        if user_row.acess_level == 0:
            read = False
            write = False
        elif user_row.access_level == 1:
            read = True
            write = False
        elif user_row.access_level == 2:
            read = True
            write = True
        else:
            read = False
            write = False
    return read, write
