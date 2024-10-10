from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import mysql.connector
from mysql.connector import errorcode
from datetime import  datetime
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import smtplib

import bcrypt

import re
from mysql.connector import Error
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.relativedelta import relativedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import mysql.connector
from google.oauth2.credentials import Credentials



# from lib import get_users, get_regulations,get_regulation_name,get_category_type,get_activities,get_frequency,get_frequency_description,get_due_on,create_calendar_event, schedule_calendar_events,send_scheduled_emails,add_calendar_events_from_queue,configure_mail
 
from python_functions.lib_functions import *



app = Flask(__name__)
# Configuration for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'vardaan.rcms@gmail.com'
app.config['MAIL_PASSWORD'] = 'aynlltagpthlzqgd'  # Consider using environment variables for security
app.config['MAIL_DEFAULT_SENDER'] = 'vardaan.rcms@gmail.com'
mail = Mail(app)



# Database connection using mysql.connector
def connect_to_database():
    try:
        conn = mysql.connector.connect(
            host="rcms-database.cxyo004saqut.us-east-1.rds.amazonaws.com",
            user="Global_Admin",
            password="Globaladmin1",
            database="rcms"
        )
        cursor = conn.cursor(buffered=True, dictionary=True)
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None, None
    
# Configuration for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'vardaan.rcms@gmail.com'
app.config['MAIL_PASSWORD'] = 'aynlltagpthlzqgd'  # Consider using environment variables for security
app.config['MAIL_DEFAULT_SENDER'] = 'vardaan.rcms@gmail.com'
mail = Mail(app)

def index_main():
    return render_template('entity/login.html')

def login_main():
    print('Entered login')
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        # Connect to the database
        conn, cursor = connect_to_database()

        if conn is None or cursor is None:
            flash('Database connection failed', 'error')
            return redirect(url_for('index'))

        try:
            # Query to get the user details based on user_id
            query = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            # print(user)
            # input(user)

            if user:
                print(f"Fetched user data: {user}")  # Debugging output

                # Verify the password
                if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    # Initialize session variables
                    session['user_id'] = user['user_id']
                    session['entity_id'] = user.get('entity_id')
                    session['user_name'] = user.get('user_name')

                    # Debugging output to ensure session variables are set
                    print(f"Session user_id: {session['user_id']}")
                    print(f"Session entity_id: {session['entity_id']}")
                    print(f"Session user_name: {session['user_name']}")

                    #flash('Login successful!', 'success')

                    # Role-based redirection
                    if user['role'] == 'Global':
                        print("Redirecting to global admin page")
                        return redirect(url_for('global_admin_dashboard'))

                    elif user['role'] == 'Admin':
                        print("Redirecting to admin dashboard")
                        return redirect(url_for('entity_admin_dashboard'))

                    elif user['role'] == 'User':
                        print("Redirecting to user dashboard")
                        return redirect(url_for('entity_dashboard', entity_id=user['entity_id']))
                else:
                    flash('Invalid credentials, please try again.', 'error')
            else:
                flash('User not found.', 'error')

        except Exception as e:
            print(f'An error occurred: {str(e)}', 'error')
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    # If the request method is GET or if authentication fails, render the login page
    return render_template('entity/login.html')

def entity_admin_dashboard_main():
    # Pass entity_id to Dash when rendering the page
      # Call your Dash app with entity_id
      entity_id2=session['entity_id']
      print("The Entity ID 2 is", entity_id2)
      return render_template('entity/entity_admin.html', factory_id=entity_id2)

def add_user_entity():
    if request.method == 'POST':
        user_id = request.form['user_id']
        user_name = request.form['user_name']
        address = request.form['address']
        mobile_no = request.form['mobile_no']
        email_id = request.form['email_id']
        password = request.form['password']
        role = request.form['role']  # Get the role from the form

        # Hash the password before saving it
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn, cursor = connect_to_database()
        if conn is None or cursor is None:
            flash('Database connection failed!', 'error')
            return redirect(url_for('admin_add_user'))

        try:
            # Insert the new user into the database
            cursor.execute("""
                INSERT INTO users (user_id, user_name, address, mobile_no, email_id, password, entity_id, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, user_name, address, mobile_no, email_id, hashed_password.decode('utf-8'), session['entity_id'], role))

            conn.commit()

            # Send email notification to the user
            msg = Message(
                "Welcome to Regulatory Compliance Management System",
                sender="vardaan.rcms@gmail.com",
                recipients=[email_id]
            )
            msg.body = (f"Dear {user_name},\n\n"
                        f"You have been added to the system with the following credentials:\n\n"
                        f"User ID: {user_id}\n"
                        f"Password: {password}\n"
                        f"Factory ID: {session['entity_id']}\n"
                        f"Role: {role}\n\n"
                        f"Please log in and change your password as soon as possible.\n\n"
                        f"Best regards,\n"
                        f"Your Factory ID: {session['entity_id']}")
            mail.send(msg)

            flash('User added successfully! An email has been sent to the user.', 'success')

        except mysql.connector.Error as err:
            flash(f'Failed to add user: {err}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        #return redirect(url_for('entity_admin_dashboard'))
    # Fetching session data
    user_entity_id = session.get('entity_id')
    user_user_id = session.get('user_id')
    return render_template('entity/add_user.html',user_entity_id=user_entity_id, user_user_id=user_user_id)

def load_user_entity(user_id):
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500

    try:
        cursor.execute("SELECT user_id, entity_id, user_name, address, mobile_no, email_id, role FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return jsonify(user)
        else:
            return jsonify({'error': 'User not found'}), 404
    finally:
        cursor.close()
        conn.close()

def update_user_entity():
    user_id = request.form['user_id']
    user_name = request.form['user_name']
    address = request.form['address']
    mobile_no = request.form['mobile_no']
    email_id = request.form['email_id']

    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500

    try:
        cursor.execute("""
            UPDATE users
            SET user_name = %s, address = %s, mobile_no = %s, email_id = %s
            WHERE user_id = %s
        """, (user_name, address, mobile_no, email_id, user_id))
        conn.commit()
        return jsonify({'message': 'User updated successfully!'}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

def update_user_page_entity():
    # Fetching session data
    user_entity_id = session.get('entity_id')
    user_user_id = session.get('user_id')
    return render_template('entity/update_user.html',user_entity_id=user_entity_id, user_user_id=user_user_id)

def fetch_user_entity(user_id):
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500

    try:
        cursor.execute("SELECT user_id, entity_id, user_name, address, mobile_no, email_id, role FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return jsonify(user)
        else:
            return jsonify({'error': 'User not found'}), 404
    finally:
        cursor.close()
        conn.close()

def delete_user_entity():
    user_id = request.form['user_id']
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500

    try:
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        return jsonify({'message': 'User deleted successfully!'}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

def delete_user_page_entity():
    # Fetching session data
    user_entity_id = session.get('entity_id')
    user_user_id = session.get('user_id')
    return render_template('entity/delete_user.html',user_entity_id=user_entity_id, user_user_id=user_user_id)

def add_category_entity():
    # Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')
    
    # Pass the session data to the template
    return render_template('entity/add_category_entity.html', entity_id=entity_id, user_id=user_id)

def submit_category_entity():
    conn, cursor = connect_to_database()
    error_message = None
    success_message = None
 
    if conn is not None:
        cursor = conn.cursor()
        try:
            category_type = request.form.get('categoryType')
            remarks = request.form.get('remarks')
 
            # Check if the category type already exists in the database
            cursor.execute("SELECT COUNT(*) FROM category WHERE category_type = %s", (category_type,))
            if cursor.fetchone()[0] > 0:
                error_message = "Category already exists! Please use a different category type."
            else:
                # Insert the category data into the database
                cursor.execute("""
                    INSERT INTO category (category_type, remarks)
                    VALUES (%s, %s)
                """, (category_type, remarks))
                conn.commit()
 
                success_message = f"Category successfully added with ID {cursor.lastrowid}."
 
        except mysql.connector.IntegrityError as e:
            error_message = "Failed to submit category data due to integrity error."
        except Exception as e:
            print(f"Failed to submit form data: {e}")
            error_message = "Error processing your request."
        finally:
            cursor.close()
            conn.close()
    else:
        error_message = "Failed to connect to the database."

    # Fetching session data again
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')
 
    return render_template('entity/add_category_entity.html', error_message=error_message, success_message=success_message, entity_id=entity_id, user_id=user_id)

def display_categories_entity():
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return "Error connecting to the database."

    try:
        # Fetch specific columns, including remarks
        cursor.execute("SELECT category_id, category_type, Remarks FROM category")
        categories = cursor.fetchall()
        
        # Print the categories to check if remarks are fetched
        print(categories)  # Debugging: check the data structure and whether remarks are fetched
        # Fetching session data
        entity_id = session.get('entity_id')
        user_id = session.get('user_id')

        return render_template('entity/delete_category.html', categories=categories,entity_id=entity_id, user_id=user_id)
    finally:
        cursor.close()
        conn.close()

def delete_category_entity():
    category_ids = request.form.getlist('category_ids')
    if category_ids:
        conn, cursor = connect_to_database()
        if conn is None or cursor is None:
            return "Error connecting to the database."
        
        try:
            format_strings = ','.join(['%s'] * len(category_ids))
            cursor.execute(f"DELETE FROM category WHERE category_id IN ({format_strings})", category_ids)
            conn.commit()
            return redirect('/display_entity_categories?deleted=true')  # Redirect with query parameter after successful deletion
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            flash("An error occurred while deleting the categories.")
        finally:
            cursor.close()
            conn.close()
    else:
        flash("No category selected for deletion.")
    
    return redirect('/display_entity_categories')

def get_categories():
    print("get_categories() function is called", flush=True)
    conn, cursor = connect_to_database()
    categories = []
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT category_id, category_type FROM category ORDER BY category_type ASC")
            categories = cursor.fetchall()
            print("Categories fetched and sorted:", categories, flush=True)  # Immediate output
        except Error as e:
            print(f"Failed to query categories: {e}", flush=True)
        finally:
            cursor.close()
            conn.close()
    return categories

def add_regulation_entity():
    categories = get_categories()  # This should trigger the print statements

    # Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')
    
    return render_template('entity/add_regulation_entity.html', categories=categories,entity_id=entity_id, user_id=user_id)

def submit_regulation_entity():
    regulation_name = request.form['regulationName']
    category_id = request.form['categoryID']
    regulatory_body = request.form['regulatoryBody']
    internal_external = request.form['internalExternal']
    national_international = request.form['nationalInternational']
    mandatory_optional = request.form['mandatoryOptional']
    effective_from = request.form['effectiveFrom']
    obsolete_current = request.form['obsoleteCurrent']

    # Fetch entity_id from the session
    entity_id = session.get('entity_id')
 
    conn, cursor = connect_to_database()
    error_message = None
    success_message = None
 
    if conn is not None:
        cursor = conn.cursor()
        try:
            # Check if the regulation name already exists
            cursor.execute("SELECT COUNT(*) FROM regulation_master WHERE regulation_name = %s", (regulation_name,))
            exists = cursor.fetchone()[0]
 
            if exists:
                error_message = f"Regulation with name '{regulation_name}' already exists."
            else:
                # Generate regulation_id based on the first 4 letters of the regulation name
                prefix = regulation_name[:4].upper()
 
                # Check if there are existing regulation IDs with the same prefix
                cursor.execute("""
                    SELECT regulation_id FROM regulation_master WHERE regulation_id LIKE %s ORDER BY regulation_id DESC LIMIT 1
                """, (prefix + '%',))
                last_id = cursor.fetchone()
 
                if last_id:
                    last_num = re.search(r'\d+$', last_id[0])
                    new_num = int(last_num.group()) + 1 if last_num else 1
                else:
                    new_num = 1
 
                regulation_id = f"{prefix}{new_num:03}"  # Format the digit part with leading zeros
 
                # Insert the regulation data into the database
                query = """
                    INSERT INTO regulation_master
                    (regulation_id, regulation_name, category_id, regulatory_body, internal_external,
                    national_international, mandatory_optional, effective_from, obsolete_current)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    regulation_id, regulation_name, category_id, regulatory_body,
                    internal_external, national_international, mandatory_optional,
                    effective_from, obsolete_current
                ))
                # Insert the regulation_id and entity_id into the entity_regulation table
                query_entity_regulation = """
                    INSERT INTO entity_regulation (entity_id, regulation_id)
                    VALUES (%s, %s)
                """
                cursor.execute(query_entity_regulation, (entity_id, regulation_id))
                conn.commit()
                success_message = f"Regulation successfully added with ID {regulation_id}."
        except Error as e:
            print(f"Failed to insert regulation: {e}", flush=True)
            error_message = "Failed to add regulation."
        finally:
            cursor.close()
            conn.close()
    else:
        error_message = "Failed to connect to the database."
 
    categories = get_categories()
    user_id = session.get('user_id')
    return render_template('entity/add_regulation_entity.html', error_message=error_message, success_message=success_message, categories=categories,entity_id=entity_id, user_id=user_id)

def edit_regulation_page_entity():
    # Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')

    # Establish connection to database
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        flash('Database connection error', 'error')
        return redirect(url_for('edit_entity_regulation_page'))

    try:
        # Query to fetch all regulations for the given entity_id from the entity_regulation and regulation_master tables
        query = """
            SELECT rm.regulation_id, rm.regulation_name
            FROM regulation_master rm
            INNER JOIN entity_regulation er ON rm.regulation_id = er.regulation_id
            WHERE er.entity_id = %s
        """
        cursor.execute(query, (entity_id,))
        regulations = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f'Error fetching regulations: {str(err)}', 'error')
        regulations = []
    finally:
        cursor.close()
        conn.close()

    # Render the template with the list of regulations for the given entity
    return render_template('entity/update_regulations.html', regulations=regulations, entity_id=entity_id, user_id=user_id)

def fetch_regulation_entity():
    regulation_name = request.form.get('regulation_name')

    # Fetching session data
    entity_id = session.get('entity_id')

    # Convert the input to lowercase for case-insensitive search
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        flash('Database connection error', 'error')
        return redirect(url_for('edit_entity_regulation_page'))

    try:
        # Query to fetch regulation details based on regulation_name and entity_id
        query = """
            SELECT rm.*
            FROM regulation_master rm
            INNER JOIN entity_regulation er ON rm.regulation_id = er.regulation_id
            WHERE LOWER(rm.regulation_name) = LOWER(%s) AND er.entity_id = %s
        """
        cursor.execute(query, (regulation_name, entity_id))
        regulation = cursor.fetchone()
    except mysql.connector.Error as err:
        flash(f'Error fetching regulation: {str(err)}', 'error')
        regulation = None
    finally:
        cursor.close()
        conn.close()

    if not regulation:
        flash('No regulation found for the current entity', 'error')
        return redirect(url_for('edit_entity_regulation_page'))

    # Fetching session data for rendering
    user_id = session.get('user_id')

    return render_template('entity/update_regulations.html', regulation=regulation, entity_id=entity_id, user_id=user_id)

def update_regulation_entity():
    # Get data from the form using `request.form`
    regulation_id = request.form.get('regulation_id')
    regulatory_body = request.form.get('regulatory_body')
    internal_external = request.form.get('internal_external')
    national_international = request.form.get('national_international')
    mandatory_optional = request.form.get('mandatory_optional')
    obsolete_current = request.form.get('obsolete_current')

    if not regulation_id:
        flash('Missing regulation ID', 'error')
        return redirect(url_for('edit_entity_regulation_page'))

    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        flash('Database connection error', 'error')
        return redirect(url_for('edit_entity_regulation_page'))

    try:
        query = """
            UPDATE regulation_master
            SET regulatory_body = %s,
                internal_external = %s,
                national_international = %s,
                mandatory_optional = %s,
                obsolete_current = %s
            WHERE regulation_id = %s
        """
        cursor.execute(query, (regulatory_body, internal_external, national_international, mandatory_optional, obsolete_current, regulation_id))
        conn.commit()

        flash('Regulation updated successfully!', 'success')
        return redirect(url_for('edit_entity_regulation_page'))
    except mysql.connector.Error as err:
        flash(f'Error updating regulation: {str(err)}', 'error')
        return redirect(url_for('edit_entity_regulation_page'))
    finally:
        cursor.close()
        conn.close()

def delete_regulations_page_entity():
    # Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')
    
    return render_template('entity/delete_regulations.html', entity_id=entity_id, user_id=user_id)

def fetch_categories_entity():
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor.execute("SELECT category_id, category_type FROM category")
        categories = cursor.fetchall()
        return jsonify(categories)
    finally:
        cursor.close()
        conn.close()

def load_regulations_entity(category_id):
    # Fetch entity_id from the session
    entity_id = session.get('entity_id')
    
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500

    try:
        # Modify the query to join with entity_regulation and filter by entity_id
        query = """
            SELECT rm.regulation_id, rm.regulation_name, rm.regulatory_body
            FROM regulation_master rm
            INNER JOIN entity_regulation er ON rm.regulation_id = er.regulation_id
            WHERE rm.category_id = %s AND er.entity_id = %s
        """
        cursor.execute(query, (category_id, entity_id))
        regulations = cursor.fetchall()
        return jsonify(regulations)
    finally:
        cursor.close()
        conn.close()

def delete_regulations_entity():
    regulation_ids = request.form.getlist('regulation_ids')
    if not regulation_ids:
        return jsonify({'error': 'No regulations selected'}), 400

    # Fetch entity_id from the session
    entity_id = session.get('entity_id')

    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500

    try:
        # Ensure that only regulations associated with the entity_id can be deleted
        format_strings = ','.join(['%s'] * len(regulation_ids))
        query = f"""
            DELETE rm FROM regulation_master rm
            INNER JOIN entity_regulation er ON rm.regulation_id = er.regulation_id
            WHERE rm.regulation_id IN ({format_strings}) AND er.entity_id = %s
        """
        cursor.execute(query, (*regulation_ids, entity_id))
        conn.commit()
        return jsonify({'message': 'Selected regulations deleted successfully!'})
    finally:
        cursor.close()
        conn.close()

def add_activity_entity():
    conn, cursor = connect_to_database()
    regulations = []
    if conn is not None:
        cursor = conn.cursor()
        try:
            # Fetch both regulation ID and name
            cursor.execute("SELECT regulation_id, regulation_name FROM regulation_master")
            regulations = cursor.fetchall()
        except Error as e:
            print(f"Failed to query regulations: {e}")
        finally:
            cursor.close()
            conn.close()
    
    #Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')
    
    return render_template('entity/add_activity_entity.html', regulations=regulations,entity_id=entity_id, user_id=user_id)

def get_regulation_id_entity(regulation_name):
    conn, cursor = connect_to_database()
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT regulation_id FROM regulation_master WHERE regulation_name = %s", (regulation_name,))
            result = cursor.fetchone()
            return jsonify({'regulation_id': result[0] if result else ''})
        except Error as e:
            print(f"Failed to query regulation ID: {e}")
            return jsonify({'regulation_id': ''})
        finally:
            cursor.close()
            conn.close()
    return jsonify({'regulation_id': ''})

def send_regulations():
    conn, cursor = connect_to_database()
    regulations = []
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT regulation_id, regulation_name FROM regulation_master")
            regulations = cursor.fetchall()
        except Error as e:
            print(f"Failed to query regulations: {e}")
        finally:
            cursor.close()
            conn.close()
    return regulations

def submit_checklist_entity():
    regulation_id = request.form['regulationID']
    activity = request.form['activity']
    mandatory_optional = request.form['mandatoryOptional']
    document_upload_yes_no = request.form['documentupload_yes_no']
    frequency = request.form['frequency']
    frequency_timeline = request.form['frequencyTimeline']
    criticality = request.form['criticalNonCritical']
    ews = request.form['ews']
    activity_description = request.form['activityDescription']
 
    conn, cursor = connect_to_database()
    error_message = None
    success_message = None
 
    if conn is not None:
        cursor = conn.cursor()
        try:
            # Check if the activity already exists for the given regulation
            cursor.execute("""
                SELECT COUNT(*) FROM activity_master
                WHERE activity = %s AND regulation_id = %s
            """, (activity, regulation_id))
            if cursor.fetchone()[0] > 0:
                error_message = "Activity already exists for this regulation."
            else:
                # If it doesn't exist, insert the new activity
                cursor.execute("SELECT COALESCE(MAX(activity_id) + 1, 1) FROM activity_master WHERE regulation_id = %s", (regulation_id,))
                activity_id = cursor.fetchone()[0]
 
                query = """
                    INSERT INTO activity_master
                    (regulation_id, activity_id, activity, mandatory_optional, documentupload_yes_no,
                    frequency, frequency_timeline, criticality, ews, activity_description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    regulation_id, activity_id, activity, mandatory_optional, document_upload_yes_no,
                    frequency, frequency_timeline, criticality, ews, activity_description
                ))
                conn.commit()
                success_message = "Activity successfully added."
 
        except Error as e:
            print(f"Failed to insert activity: {e}")
            error_message = "Failed to add checklist item due to a database error."
        finally:
            cursor.close()
            conn.close()
    else:
        error_message = "Failed to connect to the database."
 
    regulations = send_regulations()
    #Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')
    return render_template('entity/add_activity_entity.html', error_message=error_message, success_message=success_message, regulations=regulations,entity_id=entity_id, user_id=user_id)
 
def update_activities_page_entity():
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return "Database connection failed", 500
    
    # Fetch all regulation_id
    cursor.execute("SELECT DISTINCT regulation_id FROM rcms.activity_master")
    regulations = cursor.fetchall()
    
    cursor.close()
    conn.close()

    #Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')
    return render_template('entity/update_activities.html', regulations=regulations,entity_id=entity_id,user_id=user_id)

def populate_activities_entity(regulation_id):
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return "Database connection failed", 500
    
    # Fetch all activities based on regulation_id
    cursor.execute(f"SELECT activity_id, activity FROM rcms.activity_master WHERE regulation_id='{regulation_id}'")
    activities = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {'activities': activities}

def get_activity_details_entity(regulation_id, activity_id):
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return "Database connection failed", 500

    try:
        # Fetch the details of the selected activity based on both regulation_id and activity_id
        cursor.execute("""
            SELECT * FROM rcms.activity_master
            WHERE regulation_id = %s AND activity_id = %s
        """, (regulation_id, activity_id))
        
        # Use fetchone() to retrieve the result
        activity_details = cursor.fetchone()
        print(f"Activity Details: {activity_details}")

        if activity_details:
            return {
                'activity_description': activity_details['activity_description'],
                'criticality': activity_details['criticality'],
                'documentupload_yes_no': activity_details['documentupload_yes_no'],
                'frequency': activity_details['frequency'],
                'frequency_timeline': activity_details['frequency_timeline'].strftime('%Y-%m-%d') if activity_details['frequency_timeline'] else None,  # Format the date properly
                'mandatory_optional': activity_details['mandatory_optional'],
                'ews': activity_details['ews']
            }
        else:
            return "No activity found", 404
    except mysql.connector.Error as err:
        return f"Error fetching activity details: {err}", 500
    finally:
        cursor.close()
        conn.close()

def update_activity_entity():
    data = request.form
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return "Database connection failed", 500
    
    try:
        # Debugging: print the form data to check what is being passed
        print("Form Data:", data)
        
        # Check if all required fields are present
        required_fields = ['activity_description', 'criticality', 'documentupload_yes_no',
                           'frequency', 'frequency_timeline', 'mandatory_optional', 'ews',
                           'regulation_id', 'activity_id_hidden']
        
        for field in required_fields:
            if field not in data:
                return f"Missing field: {field}", 400
        
        # Debugging: print the parameters to be passed in the SQL query
        print("Updating activity with parameters: ",
              data['activity_description'], data['criticality'], data['documentupload_yes_no'],
              data['frequency'], data['frequency_timeline'], data['mandatory_optional'],
              data['ews'], data['regulation_id'], data['activity_id_hidden'])
        
        # Update the activity based on both regulation_id and activity_id to prevent incorrect updates
        cursor.execute("""
            UPDATE rcms.activity_master SET
                activity_description = %s,
                criticality = %s,
                documentupload_yes_no = %s,
                frequency = %s,
                frequency_timeline = %s,
                mandatory_optional = %s,
                ews = %s
            WHERE regulation_id = %s AND activity_id = %s
        """, (data['activity_description'], data['criticality'], data['documentupload_yes_no'],
              data['frequency'], data['frequency_timeline'], data['mandatory_optional'],
              data['ews'], data['regulation_id'], data['activity_id_hidden']))
    
        conn.commit()

        # Fetch updated data to pass to the template
        cursor.execute("SELECT DISTINCT regulation_id FROM rcms.activity_master")
        regulations = cursor.fetchall()

        cursor.execute("SELECT activity_id, activity FROM rcms.activity_master WHERE regulation_id = %s", (data['regulation_id'],))
        activities = cursor.fetchall()

        # Stay on the same page and display a success message
        return render_template('entity/update_activities.html', 
                               regulations=regulations, 
                               activities=activities)
    
    except mysql.connector.Error as err:
        return f"Error updating activity: {err}", 500
    finally:
        cursor.close()
        conn.close()

def delete_activities_page_entity():
    #Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')

    return render_template('entity/delete_activities.html',entity_id=entity_id, user_id=user_id)  # This renders the delete activities HTML page

def populate_regulations_entity():
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor.execute("SELECT regulation_id, regulation_name FROM regulation_master")
        regulations = cursor.fetchall()
        return jsonify(regulations)
    finally:
        cursor.close()
        conn.close()

def load_activities_entity(regulation_id):
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor.execute("SELECT activity_id, activity FROM activity_master WHERE regulation_id = %s", (regulation_id,))
        activities = cursor.fetchall()
        return jsonify(activities)
    finally:
        cursor.close()
        conn.close()

def delete_activities_entity():
    regulation_id = request.form.get('regulation_id')
    activity_ids = request.form.getlist('activity_ids')
    
    if not regulation_id or not activity_ids:
        return jsonify({'error': 'No activities or regulation selected'}), 400

    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500

    try:
        # Delete only the activities with the specific regulation_id and activity_ids
        format_strings = ','.join(['%s'] * len(activity_ids))
        query = f"DELETE FROM activity_master WHERE regulation_id = %s AND activity_id IN ({format_strings})"
        cursor.execute(query, (regulation_id, *activity_ids))
        conn.commit()
        return jsonify({'message': 'Selected activities deleted successfully!'})
    finally:
        cursor.close()
        conn.close()

def add_holiday_entity():
    if request.method == 'POST':
        submit_type = request.form.get('submit_type')
 
        conn, cursor = connect_to_database()
        if conn is None or cursor is None:
            flash('Database connection failed!', 'error')
            return redirect(url_for('add_holiday'))
 
        if submit_type == 'multiple':
            holidays = []
 
            # Loop through potential holiday forms in the table
            for i in range(12):
                holiday_date = request.form.get(f'holiday_date_{i}')
                description = request.form.get(f'description_{i}')
                if holiday_date and description:
                    holidays.append((holiday_date, description))
 
            if not holidays:
                flash('At least one holiday must be provided!', 'error')
                return redirect(url_for('add_holiday'))
 
            try:
                if holidays:
                    cursor.executemany("""
                        INSERT INTO holiday_master (Holiday_Date, Description)
                        VALUES (%s, %s)
                    """, holidays)
                    conn.commit()
                    flash('Holidays added successfully!', 'success')
                else:
                    flash('No holidays to add.', 'error')
            except Exception as e:
                conn.rollback()
                flash(f'Failed to add holidays: {str(e)}', 'error')
 
        elif submit_type == 'single':
            holiday_date = request.form.get('holiday_date_single')
            description = request.form.get('description_single')
 
            if not holiday_date or not description:
                flash('All fields are required!', 'error')
                return redirect(url_for('add_holiday'))
 
            try:
                cursor.execute("""
                    INSERT INTO holiday_master (Holiday_Date, Description)
                    VALUES (%s, %s)
                """, (holiday_date, description))
                conn.commit()
                flash(f'Holiday added successfully! Date: {holiday_date}, Description: {description}', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Failed to add holiday: {str(e)}', 'error')
 
        cursor.close()
        conn.close()
 
        return redirect(url_for('add_holiday'))
    #Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')

    return render_template('entity/add_holiday.html',entity_id=entity_id, user_id=user_id)

def delete_holidays_page_entity():
    #Fetching session data
    entity_id = session.get('entity_id')
    user_id = session.get('user_id')
    return render_template('entity/delete_holidays.html',entity_id=entity_id, user_id=user_id)

def fetch_holidays_entity():
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor.execute("SELECT `Holiday_Date`, `Description` FROM holiday_master")
        holidays = cursor.fetchall()
        # Format the date to exclude time
        for holiday in holidays:
            holiday['Holiday_Date'] = holiday['Holiday_Date'].strftime("%Y-%m-%d")  # Correct format for MySQL
        return jsonify(holidays)
    finally:
        cursor.close()
        conn.close()

def delete_holidays_entity():
    holiday_dates = request.form.getlist('holiday_dates')
    if not holiday_dates:
        return jsonify({'error': 'No holidays selected'}), 400

    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return jsonify({'error': 'Database connection error'}), 500

    try:
        # Convert dates to MySQL acceptable format
        formatted_dates = [datetime.strptime(date, "%Y-%m-%d").date() for date in holiday_dates]
        format_strings = ','.join(['%s'] * len(formatted_dates))
        cursor.execute(f"DELETE FROM holiday_master WHERE `Holiday_Date` IN ({format_strings})", tuple(formatted_dates))
        conn.commit()
        return jsonify({'message': 'Selected holidays deleted successfully!'})
    finally:
        cursor.close()
        conn.close()

def send_email(subject, to_email, content):
    sender_email = "vdatasciences@gmail.com"  # Replace with your sender email
    password = "ywouzetbuxuiaelg"  # Replace with your app-specific password
 
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(content, 'plain'))
 
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    text = message.as_string()
    server.sendmail(sender_email, to_email, text)
    server.quit()
 
# Function to create a Google Calendar event
from google.oauth2.credentials import Credentials  # Ensure this import
 
def ccreate_calendar_event(subject, due_on, to_email):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
 
    # Check if token file exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
 
    # If there are no valid credentials, request authorization
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
 
    # Create the calendar service
    service = build('calendar', 'v3', credentials=creds)
 
    event = {
        'summary': subject,
        'description': f'Task due on {due_on}',
        'start': {
            'dateTime': f'{due_on}T08:00:00',
            'timeZone': 'Europe/London',
        },
        'end': {
            'dateTime': f'{due_on}T09:00:00',
            'timeZone': 'Europe/London',
        },
        'attendees': [
            {'email': to_email},
        ],
    }
 
    # Insert the event into the Google Calendar
    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f'Event created: {event.get("htmlLink")}')

def reassign_entity():
    conn, cursor = connect_to_database()
    cursor = conn.cursor()

    # Fetching task_entity_id from session instead of the form
    task_entity_id = session.get('entity_id')
    task_user_id = session.get('user_id')

    if not task_entity_id:
        return "Entity ID not found in session", 400

    # Fetching unique Factory IDs based on task_entity_id
    cursor.execute("SELECT DISTINCT entity_id FROM entity_regulation WHERE entity_id = %s", (task_entity_id,))
    factories = cursor.fetchall()

    # Default empty values for dropdowns that depend on other selections
    regulation_ids = []
    activities = []
    due_dates = []
    users = []

    # Capture values from the form
    assignTo = request.args.get('assignTo', '')
    reviewer = request.args.get('reviewer', '')
    regulation_id = request.args.get('regulationID', '')
    due_on = request.args.get('dueTo', '')  # Capture the selected due date
    user_id = request.args.get('userID', '')  # Capture the selected user ID
    activity_description = request.args.get('activity', '')  # Capture selected activity description

    print(f"Selected Due Date: {due_on}")  # Debugging

    # Fetch users based on the task_entity_id from the session
    if task_entity_id:
        cursor.execute("""
            SELECT user_id, email_id
            FROM users
            WHERE entity_id = %s
        """, (task_entity_id,))
        users = cursor.fetchall()

    # Fetch Reassign To and Review Reassign To User IDs based on task_entity_id
    reassignto = []
    review_reassignto = []
    if task_entity_id:
        cursor.execute("""
            SELECT user_id, email_id
            FROM users
            WHERE entity_id = %s
        """, (task_entity_id,))
        reassignto = cursor.fetchall()

        cursor.execute("""
            SELECT user_id, email_id
            FROM users
            WHERE entity_id = %s
        """, (task_entity_id,))
        review_reassignto = cursor.fetchall()

    # Fetch Regulation IDs based on user_id and preparation_responsibility
    if user_id:
        cursor.execute("""
            SELECT DISTINCT regulation_id
            FROM entity_regulation_tasks
            WHERE preparation_responsibility = %s
        """, (user_id,))
        regulation_ids = cursor.fetchall()

    # Fetch activity descriptions based on selected user_id and regulation_id
    if user_id and regulation_id:
        cursor.execute("""
            SELECT DISTINCT rc.activity_description
            FROM activity_master rc
            INNER JOIN entity_regulation_tasks fram
                ON rc.regulation_id = fram.regulation_id
                AND rc.activity_id = fram.activity_id
            WHERE fram.preparation_responsibility = %s
            AND fram.regulation_id = %s
        """, (user_id, regulation_id))
        activities = cursor.fetchall()

    # Fetch due_on values based on user_id, regulation_id, and activity_description
    if user_id and regulation_id and activity_description:
        cursor.execute("""
            SELECT DISTINCT due_on
            FROM entity_regulation_tasks fram
            INNER JOIN activity_master rc
                ON fram.regulation_id = rc.regulation_id
                AND fram.activity_id = rc.activity_id
            WHERE fram.preparation_responsibility = %s
            AND fram.regulation_id = %s
            AND rc.activity_description = %s
            AND fram.status IN ('Yet to Start', 'WIP')
        """, (user_id, regulation_id, activity_description))
        due_dates = cursor.fetchall()

    # If both assignTo, reviewer, and due_on are provided, perform the update and send emails
    if assignTo and reviewer and due_on:
        try:
            # Update the responsibility in the database
            cursor.execute("""
                UPDATE entity_regulation_tasks
                SET preparation_responsibility = %s, review_responsibility = %s
                WHERE regulation_id = %s AND due_on = %s
            """, (assignTo, reviewer, regulation_id, due_on))
            conn.commit()

            # Get email IDs for assignTo and reviewer
            cursor.execute("SELECT email_id FROM users WHERE user_id = %s", (assignTo,))
            assign_to_email = cursor.fetchone()[0]
            cursor.execute("SELECT email_id FROM users WHERE user_id = %s", (reviewer,))
            reviewer_email = cursor.fetchone()[0]

            # Send email to Reassign To and Review Reassign To
            send_email(
                activity_description,
                assign_to_email,
                f"""
                Hello,

                A new task has been reassigned to you.

                Task Name: {activity_description}
                Factory ID: {task_entity_id}
                Regulation ID: {regulation_id}
                Assigned To: {assignTo}
                Reviewer: {reviewer}
                Due On: {due_on}

                Please take the necessary action.

                Regards,
                Your Team
                """
            )

            send_email(
                activity_description,
                reviewer_email,
                f"""
                Hello,

                A task review has been reassigned to you.

                Task Name: {activity_description}
                Factory ID: {task_entity_id}
                Regulation ID: {regulation_id}
                Assigned To: {assignTo}
                Reviewer: {reviewer}
                Due On: {due_on}

                Please take the necessary action.

                Regards,
                Your Team
                """
            )

            # Schedule Google Calendar event
            ccreate_calendar_event("Task Reassigned", due_on, assign_to_email)
            ccreate_calendar_event("Task Review Reassigned", due_on, reviewer_email)

            # Flash a success message
            flash('Task successfully reassigned!', 'success')
        except Exception as e:
            flash(f'Error in reassigning task: {str(e)}', 'error')

    cursor.close()
    conn.close()

    return render_template(
        'entity/reassign_task.html',
        factories=factories,
        users=users,
        regulations=regulation_ids,
        activities=activities,
        due_dates=due_dates,
        reassignto=reassignto,
        review_reassignto=review_reassignto,
        selected_due_on=due_on,  # Ensure due date is passed back to the template
        task_entity_id=task_entity_id,
        task_user_id=task_user_id
    )

def logout_entity():
    # Clear the user session
    session.pop('user_id', None)
    session.pop('entity_id', None)
    session.pop('user_name', None)

    # Optionally, flash a message to inform the user
    #flash('You have been logged out successfully.', 'success')

    # Redirect to the login page
    return redirect(url_for('index'))

def assign_task_entity():
    # Fetching session data
    task_entity_id = session.get('entity_id')
    user_id = session.get('user_id')
    
    # Directly pass task_entity_id and user_id from session
    return render_template('entity/assign_task.html', task_entity_id=task_entity_id, user_id=user_id)

def users_entity(entity_id):
    if not entity_id:
        return jsonify([])  # No entity_id provided, return empty list
    
    print(f"Fetching users for entity_id: {entity_id}")  # Debugging message

    try:
        users = get_users(entity_id)  # Make sure this function is properly defined and fetching the data
        if users:
            print(f"Fetched {len(users)} users")  # Debugging message
            return jsonify([{'user_id': user[0], 'user_name': user[1]} for user in users])
        else:
            print("No users found")  # Debugging message
            return jsonify([])
    except Exception as e:
        print(f"Error fetching users: {e}")  # Log the error
        return jsonify([])  # Return an empty list on error

def fetch_regulations_entity():
    task_entity_id = session.get('entity_id')
    if not task_entity_id:
        return jsonify([])  # Return an empty list if entity_id is not in the session

    print(f"Received entity_id from session: {task_entity_id}")  # Debugging statement
    regulations = get_regulations(task_entity_id)
    return jsonify(regulations)

def regulations_entity(entity_id):
    regulations = get_regulations(entity_id)  # Call the function from lib.py
    return jsonify(regulations)

def regulation_name_entity(regulation_id):
    regulation = get_regulation_name(regulation_id)  # Call the function from lib.py
    return jsonify(regulation)

def category_type_entity(regulation_id):
    category = get_category_type(regulation_id)  # Call the function from lib.py
    return jsonify(category)

def activities_entity(regulation_id):
    activities = get_activities(regulation_id)  # Call the function from lib.py
    return jsonify(activities)

def frequency_entity(regulation_id, activity_id):
    frequency = get_frequency(regulation_id, activity_id)  # Call the function from lib.py
    return jsonify(frequency)

def due_on_entity(regulation_id, activity_id):
    due_on = get_due_on(regulation_id, activity_id)  # Call the function from lib.py
    return jsonify(due_on)
 


 
def adjust_due_dates_with_holidays(cursor, due_dates):
    """Adjusts each due date individually by checking for holidays."""
    adjusted_due_dates = []
    
    for due_date in due_dates:
        print(f"Checking due date: {due_date}")  # Log current due date being checked
        
        while True:
            try:
                # Check if the due_date is a holiday
                cursor.execute("SELECT COUNT(*) as holiday_count FROM holiday_master WHERE Holiday_Date = %s", (due_date,))
                result = cursor.fetchone()
                print(f"SQL Query Result for {due_date}: {result}")  # Debug: print the raw result

                if result is None:
                    raise ValueError(f"No result returned for due_date {due_date}")
                
                # Access the result using the dictionary key
                is_holiday = result['holiday_count']
                print(f"Is {due_date} a holiday? {'Yes' if is_holiday else 'No'}")  # Log result of holiday check

                if is_holiday:
                    # If it's a holiday, adjust the due date by moving it to the next day
                    due_date = due_date + relativedelta(days=1)
                    print(f"Adjusted due date to {due_date} because of holiday")
                else:
                    # If it's not a holiday, add the due date to the adjusted list
                    adjusted_due_dates.append(due_date)
                    break

            except mysql.connector.Error as err:
                print(f"MySQL Error: {err}")
                raise  # Re-raise the error after logging it for deeper inspection
            
            except Exception as e:
                print(f"Error adjusting due dates: {e}")
                raise  # Re-raise the error to get full stack trace

    print(f"Final adjusted due dates: {adjusted_due_dates}")  # Log final adjusted due dates
    return adjusted_due_dates



def submit_form_entity():
    conn, cursor = connect_to_database()
    error_message = None
    success_message = None
    task_already_assigned = False
 
    # Fetch the task_entity_id from session
    entity_id = session.get('entity_id')
    if not entity_id:
        error_message = "Entity ID not found in session"
        return render_template('Entity/assign_task.html', error_message=error_message)
 
    

    if conn is not None:
        cursor = conn.cursor(dictionary=True)
        try:
            # Step 1: Fetch form data
            factory_id = entity_id
            regulation_id = request.form.get('regulationID')
            activity_id = request.form.get('taskName')
            due_on_str = request.form.get('Due_on')
            assign_to = request.form.get('Assign_to')
            reviewer = request.form.get('Reviewer')

            # Fetch the regulations for the session entity_id to repopulate after form submission
            regulations = get_regulations(factory_id)


            print(f"Form Data: factory_id={factory_id}, regulation_id={regulation_id}, activity_id={activity_id}, due_on={due_on_str}, assign_to={assign_to}, reviewer={reviewer}")

            # Step 2: Parse due_on date
            try:
                due_on = datetime.strptime(due_on_str, '%Y-%m-%d').date()
                print(f"Parsed due_on: {due_on}")
            except ValueError as e:
                error_message = f"Invalid date format for 'Due_on': {due_on_str}. Error: {str(e)}"
                print(error_message)
                return render_template('Entity/assign_task.html', error_message=error_message, regulations=regulations)

            # Step 3: Fetch activity details
            cursor.execute("""
                SELECT activity, frequency, ews, criticality, mandatory_optional
                FROM activity_master
                WHERE activity_id = %s AND regulation_id = %s
            """, (activity_id, regulation_id))
            activity_result = cursor.fetchone()

            if not activity_result:
                error_message = "Failed to fetch activity details."
                print(error_message)
                return render_template('Entity/assign_task.html', error_message=error_message)

            activity_name = activity_result['activity']
            frequency = activity_result['frequency']
            ews = activity_result['ews']
            criticality = activity_result['criticality']
            mandatory_optional = activity_result['mandatory_optional']
            print(f"Activity details: {activity_name}, Frequency: {frequency}, ews: {ews}, Criticality: {criticality}, Mandatory/Optional: {mandatory_optional}")

        # Fetch `internal_external` from `regulation_master` based on `regulation_id`
            cursor.execute("""
                SELECT internal_external FROM regulation_master
                WHERE regulation_id = %s
            """, (regulation_id,))
            regulation_result = cursor.fetchone()

            if not regulation_result:
                error_message = f"Failed to fetch internal/external for regulation_id {regulation_id}."
                return render_template('Entity/assign_task.html', error_message=error_message, regulations=regulations)

            internal_external = regulation_result['internal_external']
            print(f"Regulation details: Internal/External = {internal_external}")





            # Step 4: Fetch assignee and reviewer details
            cursor.execute("SELECT email_id, user_name FROM users WHERE user_id = %s", (assign_to,))
            assignee_info = cursor.fetchone()
            cursor.fetchall()  # Consume any unread results
            cursor.execute("SELECT email_id, user_name FROM users WHERE user_id = %s", (reviewer,))
            reviewer_info = cursor.fetchone()
            cursor.fetchall()  # Consume any unread results

            if not assignee_info or not reviewer_info:
                error_message = "Failed to fetch email or name for assignee or reviewer."
                print(error_message)
                return render_template('Entity/assign_task.html', error_message=error_message)

            print(f"Assignee: {assignee_info['user_name']}, Reviewer: {reviewer_info['user_name']}")

            # Step 5: Calculate due dates until the end of the next year
            end_of_next_year = due_on.replace(month=12, day=31) + relativedelta(years=1)
            current_due_on = due_on
            due_dates = []
            status="Yet to Start"

            # Step 6: Generate all due dates based on the frequency
            while current_due_on <= end_of_next_year:
                due_dates.append(current_due_on)

                # Step 7: Update current_due_on based on the frequency
                if frequency == 52:  # Weekly
                    current_due_on += relativedelta(weeks=1)
                elif frequency == 12:  # Monthly
                    current_due_on += relativedelta(months=1)
                elif frequency == 4:  # Quarterly
                    current_due_on += relativedelta(months=3)
                elif frequency == 2:  # Half-yearly
                    current_due_on += relativedelta(months=6)
                elif frequency == 1:  # Annually
                    current_due_on += relativedelta(years=1)
                elif frequency == 3:  # Every 4 months
                    current_due_on += relativedelta(months=4)
                elif frequency == 26:  # Fortnightly
                    current_due_on += relativedelta(weeks=2)
                elif frequency == 365:  # Daily
                    current_due_on += relativedelta(days=1)
                elif frequency == 0:  # One-time task
                    break

   
            due_dates = adjust_due_dates_with_holidays(cursor, due_dates)


            print(due_dates)
            print(f"Adjusted due dates: {due_dates}")

            # Step 9: Process each adjusted due date and insert into the database
            for adjusted_due_on in due_dates:
                # Step 10: Check if the task already exists for the current due date
                cursor.execute("""
                    SELECT COUNT(*) as task_count FROM entity_regulation_tasks
                    WHERE entity_id = %s AND regulation_id = %s AND activity_id = %s AND due_on = %s
                """, (factory_id, regulation_id, activity_id, adjusted_due_on.strftime('%Y-%m-%d')))
                task_exists = cursor.fetchone()['task_count']
                cursor.fetchall()  # Ensure any remaining results are consumed





                if task_exists > 0:
                    print(f"Task already assigned for due date {adjusted_due_on}. Skipping.")
                else:

                    # Insert the task including criticality, internal_external, and mandatory_optional
                    cursor.execute("""
                        INSERT INTO entity_regulation_tasks
                        (entity_id, regulation_id, activity_id, due_on,
                         preparation_responsibility, review_responsibility, status, 
                        ews, criticality, internal_external, mandatory_optional)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (factory_id, regulation_id, activity_id, 
                          adjusted_due_on.strftime('%Y-%m-%d'),
                           assign_to, reviewer, status, ews, criticality, internal_external, mandatory_optional))
                    conn.commit()



                    # # Step 11: Insert task
                    # cursor.execute("""
                    #     INSERT INTO entity_regulation_tasks
                    #     (entity_id, regulation_id, activity_id, due_on,
                    #      preparation_responsibility, review_responsibility, status, 
                    #     ews)
                    #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    # """, (factory_id, regulation_id, activity_id, adjusted_due_on.strftime('%Y-%m-%d'), assign_to, reviewer, "Yet to Start", ews))
                    # conn.commit()

                    # print(f"Task inserted for due date {adjusted_due_on}")

                    # Schedule email reminders for both assignee and reviewer
                    reminder_date = adjusted_due_on - relativedelta(days=ews) if ews is not None else adjusted_due_on
                    print('adjusted date',adjusted_due_on)
                    print('ews is ',ews)
                    print('remainder date',reminder_date)
                    # input(reminder_date)
                                        

                    # Insert reminder for Assignee
                    cursor.execute("""
                        INSERT INTO message_queue (message_des, date, time, email_id, status)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        f"Reminder: The task '{activity_name}' for regulation '{regulation_id}' is due on {adjusted_due_on.strftime('%Y-%m-%d')}.",
                        reminder_date.strftime('%Y-%m-%d'),
                        "09:00:00",
                        assignee_info['email_id'],
                        "Scheduled"
                    ))


                    # # Insert reminder for Assignee on the due date
                    # cursor.execute("""
                    #     INSERT INTO message_queue (message_des, date, time, email_id, status)
                    #     VALUES (%s, %s, %s, %s, %s)
                    # """, (
                    #     f"Reminder: The task '{activity_name}' for regulation '{regulation_id}' is due today ({current_due_on.strftime('%Y-%m-%d')}).",
                    #     current_due_on.strftime('%Y-%m-%d'),
                    #     "09:00:00",  # Time for due day reminder
                    #     assignee_info['email_id'],
                    #     "Scheduled"
                    # ))
 
                    # # Insert reminder for Reviewer on the due date
                    # cursor.execute("""
                    #     INSERT INTO message_queue (message_des, date, time, email_id, status)
                    #     VALUES (%s, %s, %s, %s, %s)
                    # """, (
                    #     f"Reminder: The task '{activity_name}' for regulation '{regulation_id}' is due today ({current_due_on.strftime('%Y-%m-%d')}).",
                    #     current_due_on.strftime('%Y-%m-%d'),
                    #     "09:00:00",  # Time for due day reminder
                    #     reviewer_info['email_id'],
                    #     "Scheduled"
                    # ))
                    # conn.commit()


                    # Insert reminder for Reviewer
                    cursor.execute("""
                        INSERT INTO message_queue (message_des, date, time, email_id, status)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        f"Reminder: The task '{activity_name}' for regulation '{regulation_id}' is due on {adjusted_due_on.strftime('%Y-%m-%d')}.",
                        reminder_date.strftime('%Y-%m-%d'),
                        "09:00:00",
                        reviewer_info['email_id'],
                        "Scheduled"
                    ))
                    conn.commit()

                    # Send the assignment email only once for the first occurrence
                    if adjusted_due_on == due_on:
                        text_assigned = f"""
                        Hello,

                        A new task has been assigned to you.

                        Task Name: {activity_name}
                        Factory ID: {factory_id}
                        Regulation ID: {regulation_id}
                        Assigned To: {assignee_info['user_name']}
                        Reviewer: {reviewer_info['user_name']}
                        Due On: {adjusted_due_on.strftime('%Y-%m-%d')}
                        {get_frequency_description(frequency)}

                        Please take the necessary action.

                        Regards,
                        Your Team
                        """

                        recipients = [assignee_info['email_id'], reviewer_info['email_id']]
                        msg = Message("New Task Assigned", recipients=recipients, body=text_assigned)

                        try:
                            mail.send(msg)
                            print(f"Assignment email sent to {recipients} for task due on {adjusted_due_on.strftime('%Y-%m-%d')}")
                            success_message = f"Task assigned successfully and the email is sent to Assigned To: {assignee_info['user_name']}, Reviewer: {reviewer_info['user_name']}."
                        except Exception as e:
                            print(f"Failed to send assignment email: {e}")
                            error_message = "Task assigned, but failed to send email notification."
                            success_message = None

                    # Schedule the calendar events for assignee and reviewer
                    try:
                        schedule_calendar_events(
                            activity_name=activity_name,
                            due_on=adjusted_due_on,
                            assignee_email=assignee_info['email_id'],
                            reviewer_email=reviewer_info['email_id']
                        )
                        print(f"Calendar events scheduled for Assignee and Reviewer for task: {activity_name}.")
                    except Exception as e:
                        print(f"Failed to schedule calendar events: {e}")

            success_message = "Tasks were created successfully for all upcoming due dates."
            print(success_message)

        except mysql.connector.IntegrityError as e:
            print(f"Integrity Error: {str(e)}")
            error_message = "Failed to submit form data: " + str(e)

        except mysql.connector.errors.InternalError as e:
            print(f"Internal Error: {str(e)}")
            error_message = "Internal error occurred: " + str(e)

        except Exception as e:
            print(f"Failed to submit form data: {e}")
            error_message = "Error processing your request."

        finally:
            print("Closing cursor and connection.")
            cursor.close()  # Ensure cursor is closed properly
            conn.close()    # Ensure the connection is closed properly
    else:
        error_message = "Failed to connect to the database."

    return render_template('Entity/assign_task.html', error_message=error_message, success_message=success_message)



# Setting up the scheduler to run `send_scheduled_emails` every minute
scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: send_scheduled_emails(app, mail, connect_to_database), trigger="interval", seconds=60)
scheduler.add_job(func=lambda: add_calendar_events_from_queue(connect_to_database, create_calendar_event), trigger="interval", seconds=60)
scheduler.start()


 