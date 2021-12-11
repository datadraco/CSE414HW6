import sys
from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # check password strength
    lower, upper, digit, special = 0, 0, 0, 0
    if len(password) >= 8:
        for i in password:
            if i.islower():
                lower += 1
            if i.isupper():
                upper += 1
            if i.isdigit():
                digit += 1
            if i == '!' or i == '@' or i == '#' or i == '?':
                special += 1
    if lower >= 1 and upper >= 1 and digit >= 1 and special >= 1 and \
            lower + upper + digit + special == len(password):
        print("Password Accepted")
    else:
        print("Please Choose a Stronger Password")

    # create the patient
    try:
        patient = Patient(username, salt=salt, hash=hash)
        # save patient information to our database
        patient.save_to_db()
        print(" *** Account created successfully *** ")

    except pymssql.Error:
        print("Create failed")
        return


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # check password strength
    lower, upper, digit, special = 0, 0, 0, 0
    if len(password) >= 8:
        for i in password:
            if i.islower():
                lower += 1
            if i.isupper():
                upper += 1
            if i.isdigit():
                digit += 1
            if i == '!' or i == '@' or i == '#' or i == '?':
                special += 1
    if lower >= 1 and upper >= 1 and digit >= 1 and special >= 1 and \
            lower + upper + digit + special == len(password):
        print("Password Accepted")
    else:
        print("Please Choose a Stronger Password")

    # create the caregiver
    try:
        caregiver = Caregiver(username, salt=salt, hash=hash)
        # save to caregiver information to our database
        caregiver.save_to_db()
        print(" *** Account created successfully *** ")
    except pymssql.Error:
        print("Create failed")
        return


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM caregivers WHERE username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['username'] is None
    except pymssql.Error:
        print("Error occurred when checking username")
        cm.close_connection()
    cm.close_connection()
    return False


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM patients WHERE username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['username'] is None
    except pymssql.Error:
        print("Error occurred when checking username")
        cm.close_connection()
    cm.close_connection()
    return False


def login_patient(tokens):
    # login_patient <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error:
        print("Error occurred when logging in")

    # check if the login was successful
    if patient is None:
        print("Please try again!")
    else:
        print("Patient logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error:
        print("Error occurred when logging in")

    # check if the login was successful
    if caregiver is None:
        print("Please try again!")
    else:
        print("Caregiver logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    # search_caregiver_schedule <date>
    # check 1: make sure someone is logged in
    global current_caregiver
    if current_caregiver is None or current_patient is None:
        print("Please log in!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    select_available_caregivers = "SELECT username FROM availabilities WHERE time = %s"
    select_available_vaccines = "SELECT DISTINCT(v.name) FROM vaccines AS v"

    try:
        d = datetime.datetime(year, month, day)
        try:
            cursor.execute(select_available_caregivers, d)
            for row in cursor:
                print(row)
            try:
                cursor.execute(select_available_vaccines)
                for row in cursor:
                    print(row)
            except:
                print("Failed to get available vaccines")
        except:
            print("Error occurred when uploading availability")
            cm.close_connection()
    except ValueError:
        print("Please select a valid date")
    except pymssql.Error:
        print("Error occured when searching schedule")
        cm.close_connection()
    cm.close_connection()


def reserve(tokens):
    # reserve <date> <vaccine>
    # check 1: make sure a patient is logged in
    global current_patient
    if current_patient is None:
        print("Please log in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine = str(tokens[2])

    # check 3: check that there available doses of the vaccine
    if vaccine.available_doses() == 0:
        print("No available doses for selected vaccine")
        return

    # check 4: check that the date has available caregivers
    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    select_caregiver = "SELECT TOP 1 username FROM availabilities WHERE time = %s ORDER BY RAND()"
    make_appointment = "INSERT INTO appointments VALUES (%s, %s, %s, %s)"
    check_caregiver_avail = "SELECT * FROM appointments WHERE time = %s and caregiver = %s"
    check_patient_avail =  "SELECT * FROM appointments WHERE time = %s and patient = %s"
    check_doses = "SELECT * FROM vaccines WHERE name = %s"
    app_details = "SELECT * FROM appointments WHERE vaccine = %s AND caregiver = %s AND patient = %s AND time = %s"

    try:
        d = datetime.datetime(year, month, day)
        try:
            rand_caregiver = cursor.execute(select_caregiver, d)
            for row in rand_caregiver:
                caregiver = row['username']
            try:
                cursor.execute(check_caregiver_avail, (d, caregiver))
                if caregiver == row['username']:
                    print("Caregiver has no availability on this day")
                    return
                try:
                    cursor.execute(check_patient_avail, (d, current_patient.get_username()))
                    if current_patient.get_username() == row['patient']:
                        print("Patient has no availability on this day")
                        return
                    try:
                        cursor.execute(check_doses, vaccine)
                        if row['doses'] == 0:
                            print("No available doses of selected vaccine")
                            return
                        try:
                            cursor.execute(make_appointment, (vaccine, current_patient, caregiver, d))
                            conn.commit()
                            vaccine.decrease_available_doses(1)
                            try:
                                cursor.execute(app_details, (vaccine, caregiver, current_patient.get_username(), d))
                                print("Appointment ID:", row['id'], "\nCaregiver:", row['caregiver'])
                            except:
                                print("Failed to find appointment details")
                                cm.close_connection()
                        except pymssql.Error:
                            print("Error when creating appointment")
                            cm.close_connection()
                    except:
                        print("Failed to check available doses")
                        cm.close_connection()
                except:
                    print("Failed to check patient availability")
                    cm.close_connection()
            except:
                print("Failed to check caregiver availability")
                cm.close_connection()
        except pymssql.Error:
            print("No available caregivers on this date")
            cm.close_connection()
    except pymssql.Error as db_err:
        print("Error occurred when inserting caregivers")
        sqlrc = str(db_err.args[0])
        print("Exception code: " + str(sqlrc))
        cm.close_connection()
    except ValueError:
        print("Please enter a valid date")
        cm.close_connection()
    cm.close_connection()


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        try:
            current_caregiver.upload_availability(d)
            print("Availability uploaded!")
        except ValueError:
            print("Please enter a valid date!")
    except pymssql.Error as db_err:
        print("Error occurred when uploading availability")


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    pass


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = str(tokens[1])
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error:
        print("Error occurred when adding doses")

    # check 3: if getter returns null, it means that we need to create the vaccine and insert it into the Vaccines
    #          table

    if vaccine is None:
        try:
            vaccine = Vaccine(vaccine_name, doses)
            vaccine.save_to_db()
        except pymssql.Error:
            print("Error occurred when adding doses")
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error:
            print("Error occurred when adding doses")

    print("Doses updated!")


def show_appointments(tokens):
    # show_appointments <username>
    # check 1: make sure that someone is logged in
    global current_caregiver
    if current_caregiver is None and current_patient is None:
        print("Please log in!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    # check 3: return results depending on role
    username = tokens[1]
    select_caregiver_schedule = "SELECT id, vaccine, date, patient FROM appointments WHERE caregiver = %s"
    select_patient_schedule = "SELECT id, vaccine, date, caregiver FROM appointments WHERE patient = %s"

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    if current_caregiver is not None:
        try:
            cursor.execute(select_caregiver_schedule, username)
            for row in cursor:
                print(row)
            return
        except pymssql.Error:
            print("Error when searching for scheduled appointments")

    if current_patient is not None:
        try:
            cursor.execute(select_patient_schedule, username)
            for row in cursor:
                print(row)
            return
        except pymssql.Error:
            print("Error when searching for scheduled appointments")


def logout(tokens):
    # logout as a patient or caregiver
    global current_caregiver
    global current_patient
    # check 1: make sure someone is logged in
    if current_caregiver is None and current_patient is None:
        print("Already logged out!")
        return

    # check 2: correct amount of tokens? but what are the tokens in this case?
    if len(tokens) != 1:
        print("Please try again!")
        return

    # check 3: if someone is logged in, set both to none
    if current_caregiver is None or current_patient is None:
        current_patient = None
        current_caregiver = None
        print("Logged Out")


def start():
    stop = False
    while not stop:
        print()
        print(" *** Please enter one of the following commands *** ")
        print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
        print("> create_caregiver <username> <password>")
        print("> login_patient <username> <password>")  #// TODO: implement login_patient (Part 1)
        print("> login_caregiver <username> <password>")
        print("> search_caregiver_schedule <date>")  #// TODO: implement search_caregiver_schedule (Part 2)
        print("> reserve <date> <vaccine>") #// TODO: implement reserve (Part 2)
        print("> upload_availability <date>")
        print("> cancel <appointment_id>") #// TODO: implement cancel (extra credit)
        print("> add_doses <vaccine> <number>")
        print("> show_appointments")  #// TODO: implement show_appointments (Part 2)
        print("> logout") #// TODO: implement logout (Part 2)
        print("> Quit")
        print()
        response = ""
        print("> Enter: ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Type in a valid argument")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Try Again")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == cancel:
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Thank you for using the scheduler, Goodbye!")
            stop = True
        else:
            print("Invalid Argument")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
