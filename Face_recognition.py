from flask import Flask, jsonify, request, session, render_template
from flask_cors import CORS
from PIL import Image
from io import BytesIO
import json
import face_recognition
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
import numpy as np
import pickle
import os
from time import sleep
import datetime
import geocoder
from ttl_list import TTLList
import requests
import threading



active_users = TTLList()
response = TTLList()
master_url = 'http://127.0.0.1:8000/api/punch'



app = Flask(__name__)
app.secret_key = 'secretkey00'
CORS(app)

engine = create_engine("postgresql://postgres:Christin@localhost:5432/facial_attendance")
db = scoped_session(sessionmaker(bind=engine))

encodings =[]
register = []
l_name = []
club = []

data= db.execute(text('SELECT * FROM student_info')).fetchall()
data_len = len(data)

for i in range(data_len):
    b =  pickle.loads(data[i][13])
    encodings.append(b)
    register.append(data[i][2])
    l_name.append(data[i][1])
    club.append(data[i][10])



def load_encodings():
    with app.app_context():
        encodings=[]
        register=[]
        data= db.execute(text('SELECT * FROM student_info')).fetchall()
        data_len = len(data)

        for i in range(data_len):
            b =  pickle.loads(data[i][13])
            encodings.append(b)
            register.append(data[i][2])
            l_name.append(data[i][1])


def byte_array_to_image(byte_array):
    with app.app_context():
        bytes_io = BytesIO(byte_array)
        image = Image.open(bytes_io)
        return image
    

@app.route('/login', methods=['POST'])   
def login():
    try:
        datetime_now = datetime.datetime.now()
        name = "Stranger!"
        status = "active"
        reg_no = "unknown"
        flag=False
        image_data = request.get_data()
        image = byte_array_to_image(image_data)
        filename = 'login.jpg'
        image.save(filename)


        loaded_image = face_recognition.load_image_file("login.jpg")
        # os.remove("login.jpg")
        face_locations = face_recognition.face_locations(loaded_image)
        face_encodings = face_recognition.face_encodings(loaded_image)

        if len(face_locations) == 0:
            return jsonify("No Face Detected"), 205

        if len(face_locations) >1:
            return jsonify("Multiple Face Detected"), 205
        
        
        
        for face_encoding in face_encodings:

        # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(encodings, face_encoding)
            
            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index] and face_distances[best_match_index] < 0.4:
                reg_no = register[best_match_index]
                name = l_name[best_match_index]
                student_club = club[best_match_index]

                if active_users.element_exists(reg_no):
                    if response.element_exists("Attendence Marked"):
                        return jsonify("Attendence Marked"),204
                    else:
                        response.add_item("Attendence Marked", 6)
                        return jsonify("Attendence Marked"), 203

                sql1 = text("""
                SELECT * FROM student_status WHERE register_number= '""" + reg_no+"' ORDER BY id DESC" )
                
                reply = db.execute(sql1).fetchone()

                
                if reply and reply[7] == 'active':
                    flag = True
                        
                if flag:
                    status = 'exited'
                    sql = text("""
                    UPDATE student_status 
                    SET "register_number" = :register_number,
                        "club" = :club,
                        "geolocation" = :geolocation,
                        "logout_time" = :logout_time,
                        "status" = :status
                    WHERE id = :id
                """)


                    # Retrieve geolocation
                    location = geocoder.ip('me')
                    geolocation = location.latlng if location and location.latlng else [0.0, 0.0]

                    # Execute the query with parameters
                    db.execute(sql, {
                        'register_number': reg_no,
                        'club': student_club,
                        'datetime': str(datetime_now),
                        'geolocation': geolocation,
                        'logout_time': datetime_now,  # Assuming you have a default value or handle this appropriately
                        'status': status,
                        'id': reply[0]
                    })
                    db.commit()
                    active_users.add_item(reg_no, 30)
                    return jsonify(f"Goodbye {name}") ,203
                    

                else:
                    active_users.add_item(reg_no, 60)
                    sql = text("""
                        INSERT INTO student_status 
                        ("register_number", "club", "datetime", "geolocation", "login_time", "status") 
                        VALUES (:register_number, :club, :datetime, :geolocation, :login_time,  :status)
                    """)

                    # Retrieve geolocation
                    location = geocoder.ip('me')
                    geolocation = location.latlng if location and location.latlng else [0.0, 0.0]

                    # Execute the query with parameters
                    db.execute(sql, {
                        'register_number': reg_no,
                        'club': student_club,
                        'datetime': datetime_now,
                        'geolocation': geolocation,
                        'login_time': datetime_now,
                        'status' : status  # Assuming you have a default value or handle this appropriately
                    })
                    db.commit()
            if name == "Stranger!":
                if response.element_exists("Hello Stranger"):
                    return jsonify("Hello Stranger"), 204
                else:
                    response.add_item("Hello Stranger", 6)
                    return jsonify("Hello Stranger"), 202
            else:
                return jsonify(f"Welcome {name}"), 200

        return jsonify("Error Faced"),400
    except Exception as e:
        print(e)
        return jsonify(f"Error: {str(e)}"), 500

@app.route('/save_image', methods=['POST'])   
def save_image():
    try:
        image_data = request.get_data()
        image = byte_array_to_image(image_data)

        filename = 'saved_image.jpg'
        image.save(filename)

        return jsonify("Image Saved"),200

    except Exception as e:
        print(e)
        return jsonify(f"Error: {str(e)}"), 500

@app.route('/register-user', methods=['POST'])
def register_user():
    try:
        user_data = request.get_data()
        user_dict = json.loads(user_data)
        sleep(2)

        name = user_dict["name"]
        register_number = user_dict["regNo"]
        email = user_dict["email"]
        dept = user_dict["dept"]
        yoj = user_dict['yoj']
        year_of_studying = user_dict['year']
        club = user_dict['club']
        gender = user_dict['gender']
        branch = "aaia"
        year_of_leaving = "2025"

        face = face_recognition.load_image_file('saved_image.jpg')
        os.remove('saved_image.jpg')
        face_bounding_boxes = face_recognition.face_locations(face)

        if len(face_bounding_boxes) == 2:
            enc = face_recognition.face_encodings(face)[0]
            face_enc =enc
            sql = text("""
                INSERT INTO student_info 
                ("name", "register_number", "email", "gender", "branch", "dept", "year_of_joining", "year_of_studying", "year_of_leaving", "club", "encoding") 
                VALUES (:name, :register_number, :email, :gender, :branch, :dept, :year_of_joining, :year_of_studying, :year_of_leaving, :club, :encoding)
            """)
            try:
                db.execute(sql, {
                'name': name,
                'register_number': register_number,
                'email': email,
                'gender': gender,
                'branch': branch,
                'dept': dept,
                'year_of_joining': yoj,
                'year_of_studying': year_of_studying,
                'year_of_leaving': year_of_leaving,
                'club': club,
                'encoding': pickle.dumps(face_enc)
                })

                db.commit()
                loading = threading.Thread(target=load_encodings)
                loading.start()
                return jsonify("User Created"), 201
            except Exception as e:
                print(e)
                return jsonify(e), 400
        else:
            return jsonify("Registration Failed"), 400

    except Exception as e:
        print(e)
        return jsonify(e), 401



@app.route('/admin/login', methods=['POST'])
def admin_login():
    credential = request.get_data()
    user_dict = json.loads(credential)
    username = user_dict["username"]
    password = user_dict["password"]

    users = db.execute(text("SELECT username FROM admin_users")).fetchone()
    print(users)
    if username in users:
        query = "SELECT password FROM admin_users WHERE username = '"+username+"'"
        password = db.execute(text(query)).fetchone()
    else:
        return "",400
    
    print(password)

    if username  == password[0]:
        # User is valid, set up the session
        session['username'] = username
        return jsonify("Authenticated"),200
    else:
        return jsonify("Invalid Entry"),400

if __name__ == "__main__":

    app.run(debug=True, port=7000)
    load_encodings()