from flask import Flask, request, jsonify, session, app
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
import base64
import time
from sqlalchemy.orm import scoped_session, sessionmaker
import geocoder
from ttl_list import TTLList
import requests


active_users = TTLList()
# active_users.add_item('item1', 'value1', 10)
master_url = 'http://127.0.0.1:8000/api/punch'



app = Flask(__name__)
app.secret_key = 'secretkey00'
CORS(app)

PHOTO_FOLDER = 'captured_photos'
app.config['UPLOAD_FOLDER'] = PHOTO_FOLDER

if not os.path.exists(PHOTO_FOLDER):
    os.makedirs(PHOTO_FOLDER)

engine = create_engine("Database URL")
db = scoped_session(sessionmaker(bind=engine))

encodings =[]
register = []
l_name = []
club =[]


# ab= db.execute(text('SELECT * FROM student_info')).fetchall()



# b =  pickle.loads(data[0][13])


# Open the file in write mode
# with open(file_path, "w") as file:
#     # Write each element of the list to a new line in the file
#     for item in b:
#         file.write("%s\n" % item)



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
            club.append(data[i][10])


file_path = "outpu_acb.txt"

# Open the file in write mode
with open(file_path, "w") as file:
    # Write each element of the list to a new line in the file
    for item in encodings:
        file.write("%s\n" % item)

# print(encodings[0])
# print(register)
# encoding = pickle.loads(data.encoding)
# print(type(encoding))




# data= db.execute(text('SELECT encoding FROM student_info')).fetchall()
# for i in data:
#     print(i)
#     en = pickle.loads(i)
#     encodings.append(en)

# register= db.execute(text('SELECT register_number FROM student_info')).fetchall()

# print(encodings)
# print(register)




@app.route('/', methods=['POST'])
def index():
    pass


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
        image_data = request.get_data()
        image = byte_array_to_image(image_data)
        filename = 'login.jpg'
        image.save(filename)


        oi = face_recognition.load_image_file("login.jpg")
        os.remove("login.jpg")
        face_locations = face_recognition.face_locations(oi)
        face_encodings = face_recognition.face_encodings(oi)
        urk = "unknown"
        # print(face_encodings)

        if len(face_locations) == 0:
            return "", 406

        if len(face_locations) >1:
            return "", 405
        
        
        
        for face_encoding in face_encodings:

        # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(encodings, face_encoding)
            

            # # If a match was found in known_face_encodings, just use the first one.
            # if True in matches:
            #     first_match_index = matches.index(True)
            #     name = register[first_match_index]

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index] and face_distances[best_match_index] < 0.4:
                urk = register[best_match_index]
                name = l_name[best_match_index]
                c = club[best_match_index]
                
                print(0)

                if active_users.element_exists(urk):
                    return '', 200
                



                

                sql1 = text("""
                SELECT * FROM student_status WHERE register_number= '""" + urk+"' ORDER BY id DESC" )

                
                
                reply = db.execute(sql1).fetchone()
                # print(reply)
                # id = reply[0]

                flag=False
                if reply is not None:
                    if reply[7] == 'active':
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
                        'register_number': urk,
                        'club': c,
                        'datetime': str(datetime_now),
                        'geolocation': geolocation,
                        'logout_time': datetime_now,  # Assuming you have a default value or handle this appropriately
                        'status': status,
                        'id': reply[0]
                    })
                    db.commit()
                # Construct the SQL query using named placeholders
                    
                else:
                    active_users.add_item(urk, 30)
                    print('hello')
                        
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
                        'register_number': urk,
                        'club': c,
                        'datetime': datetime_now,
                        'geolocation': geolocation,
                        'login_time': datetime_now,
                        'status' : status  # Assuming you have a default value or handle this appropriately
                    })
                    db.commit()
                    # return jsonify(name), 200

            # c = club[best_match_index]
            

            # name = l_name[best_match_index]
            # urk = register[best_match_index] 

            #response = requests.post(master_url, json=json_data)
            # print("Second"+name)
            if name == "Stranger!":
                return jsonify(''), 201
            else:
                return jsonify(name), 200

        return "not found",400



    except Exception as e:
        print(e)
        return f"Error: {str(e)}", 500

@app.route('/save_image', methods=['POST'])   
def save_image():
    try:
        image_data = request.get_data()
        image = byte_array_to_image(image_data)

        filename = 'saved_image.jpg'
        image.save(filename)

        return f"Image saved successfully as {filename}", 200

    except Exception as e:
        print(e)
        return f"Error: {str(e)}", 500

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

        face = face_recognition.load_image_file('C:\Server\Flask Server\saved_image.jpg')
        os.remove('C:\Server\Flask Server\saved_image.jpg')
        face_bounding_boxes = face_recognition.face_locations(face)

        if len(face_bounding_boxes) == 1:
            enc = face_recognition.face_encodings(face)[0]
            file_path = "output1.txt"

# Open the file in write mode
            # with open(file_path, "w") as file:
    # Write each element of the list to a new line in the file
                # for item in b:
                #     file.write("%s\n" % enc)
            # print(2222222222222222222222222)
            # print(enc)
            # print(200000000000000)
            face_enc =enc # enc.tobytes()


            sql = text("""
                INSERT INTO student_info 
                ("name", "register_number", "email", "gender", "branch", "dept", "year_of_joining", "year_of_studying", "year_of_leaving", "club", "encoding") 
                VALUES (:name, :register_number, :email, :gender, :branch, :dept, :year_of_joining, :year_of_studying, :year_of_leaving, :club, :encoding)
            """)

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

            load_encodings()


        else:
            return "Image was skipped and can't be used for training"

        return "", 200
    except Exception as e:
        print(e)
        return "", 401
    



def save_photo(image_data):
    with app.app_context():
        binary_image = base64.b64decode(image_data)
        
        # Generate a unique filename for each photo (you may want to use a timestamp)
        filename = f'captured_photo_{str(time.time())}.jpg'
        
        # Save the photo to the specified folder
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as file:
            file.write(binary_image)

        return filename

@app.route('/capture-photo', methods=['POST'])
def capture_photo():
    try:
        # Get the image data from the request
        image_data = request.get_data(as_text=True)

        # Save the captured photo
        filename = save_photo(image_data)

        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    credential = request.get_data()
    # user_data = request.get_data()
    user_dict = json.loads(credential)
    print()
    # return jsonify("User Verified"), 200
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
        return "",200
    else:
        return "",400

    return "kollada"

@app.route('/temp', methods=['POST'])
def temp():
    data = request.get_data()
    if(data == "b'Christin'"):
        return jsonify("Christin"), 200
    else:
        return jsonify("Hi"), 200

if __name__ == "__main__":

    app.run(debug=True, port=7000)
    load_encodings()