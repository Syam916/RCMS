from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import bcrypt
import mysql.connector
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_mail import Mail, Message
from app_2 import mail 

# Database connection using mysql.connector
def connect_to_database():
    try:
        conn = mysql.connector.connect(
            host="rcms-database.cxyo004saqut.us-east-1.rds.amazonaws.com",
            user="Global_Admin",
            password="Globaladmin1",
            database="rcms"
        )
        cursor = conn.cursor(dictionary=True)  # Returns query results as dictionaries
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None, None


def get_regulations_user():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))  # Redirect to login if not logged in
    
    conn, cur = connect_to_database()
    if conn is None or cur is None:
        return jsonify({"error": "Database connection failed"}), 500

    # Fetch all regulations with their status and due_on dates
    query = """
        SELECT e.activity_id, e.regulation_id, r.regulation_name, a.activity, e.due_on, e.status
        FROM entity_regulation_tasks e
        JOIN regulation_master r ON e.regulation_id = r.regulation_id
        JOIN activity_master a ON e.activity_id = a.activity_id AND e.regulation_id = a.regulation_id
        ORDER BY e.due_on ASC;
    """
    cur.execute(query)
    regulations = cur.fetchall()
    cur.close()
    conn.close()

    # Debug: Output all fetched regulations
    print(f"Fetched Regulations: {regulations}")

    # Categorize the regulations
    due_this_month = []
    delayed = []
    in_progress = []
    completed = []

    current_date = datetime.now().date()

    for regulation in regulations:
        due_on = regulation['due_on'].date()  # Convert to date
        status = regulation['status']

        # Debug: Show details for each regulation before categorization
        print(f"Processing Regulation: {regulation['regulation_name']}, Status: {status}, Due On: {due_on}")

        if status == "Yet to Start":
            if due_on >= current_date:
                due_this_month.append(regulation)  # Yet to Start with future due date -> Due This Month
                print(f"Added to Due This Month: {regulation['regulation_name']} (Yet to Start, Future Due Date)")
            else:
                delayed.append(regulation)  # Yet to Start and past due date -> Delayed
                print(f"Added to Delayed: {regulation['regulation_name']} (Yet to Start, Past Due Date)")
        elif status == "WIP":
            if due_on >= current_date:
                in_progress.append(regulation)  # WIP with future due date -> In Progress
                print(f"Added to In Progress: {regulation['regulation_name']} (WIP, Future Due Date)")
            else:
                regulation['overdue'] = True  # Mark WIP as overdue for red highlight
                in_progress.append(regulation)  # WIP and past due date -> In Progress with red highlight
                print(f"Added to In Progress with Red Highlight: {regulation['regulation_name']} (WIP, Past Due Date)")
        elif status == "Completed":
            completed.append(regulation)  # Completed -> Completed section
            print(f"Added to Completed: {regulation['regulation_name']}")

    # Debug: Show final categorization of regulations
    print(f"Final Categorization: Delayed: {len(delayed)}, In Progress: {len(in_progress)}, Completed: {len(completed)}, Due This Month: {len(due_this_month)}")

    # Render the regulations into separate tables in the HTML
    return render_template('user/entity_user.html',
                        due_this_month=due_this_month,
                        delayed=delayed,
                        in_progress=in_progress,
                        completed=completed)


def get_filtered_tasks_user():
    filter_option = request.args.get('filter', 'current')
    user_id = session.get('user_id')
 
    conn, cur = connect_to_database()
    if conn is None or cur is None:
        return jsonify({"error": "Database connection failed"}), 500
 
    # SQL query based on filter selection, with 'criticality' included
    if filter_option == 'current':
        query = """
            SELECT e.activity_id, e.regulation_id, r.regulation_name, a.activity, e.due_on, e.status, e.preparation_responsibility, e.review_responsibility, e.criticality
            FROM entity_regulation_tasks e
            JOIN regulation_master r ON e.regulation_id = r.regulation_id
            JOIN activity_master a ON e.activity_id = a.activity_id AND e.regulation_id = a.regulation_id
            WHERE (e.preparation_responsibility = %s OR e.review_responsibility = %s)
            AND MONTH(e.due_on) = MONTH(CURRENT_DATE)
            AND YEAR(e.due_on) = YEAR(CURRENT_DATE)
            ORDER BY e.regulation_id ASC, e.activity_id ASC, e.due_on ASC;
        """
    elif filter_option == 'last':
        query = """
            SELECT e.activity_id, e.regulation_id, r.regulation_name, a.activity, e.due_on, e.status, e.preparation_responsibility, e.review_responsibility, e.criticality
            FROM entity_regulation_tasks e
            JOIN regulation_master r ON e.regulation_id = r.regulation_id
            JOIN activity_master a ON e.activity_id = a.activity_id AND e.regulation_id = a.regulation_id
            WHERE (e.preparation_responsibility = %s OR e.review_responsibility = %s)
            AND e.due_on BETWEEN
                LAST_DAY(CURRENT_DATE - INTERVAL 1 MONTH) + INTERVAL 1 DAY - INTERVAL 1 MONTH
                AND LAST_DAY(CURRENT_DATE - INTERVAL 1 MONTH)
            ORDER BY e.regulation_id ASC, e.activity_id ASC, e.due_on ASC;
        """
    elif filter_option == 'next':
        query = """
            SELECT e.activity_id, e.regulation_id, r.regulation_name, a.activity, e.due_on, e.status, e.preparation_responsibility, e.review_responsibility, e.criticality
            FROM entity_regulation_tasks e
            JOIN regulation_master r ON e.regulation_id = r.regulation_id
            JOIN activity_master a ON e.activity_id = a.activity_id AND e.regulation_id = a.regulation_id
            WHERE (e.preparation_responsibility = %s OR e.review_responsibility = %s)
            AND e.due_on BETWEEN
                LAST_DAY(CURRENT_DATE) + INTERVAL 1 DAY
                AND LAST_DAY(CURRENT_DATE + INTERVAL 1 MONTH)
            ORDER BY e.regulation_id ASC, e.activity_id ASC, e.due_on ASC;
        """
    else:
        return jsonify({"error": "Invalid filter option"}), 400
 
    # Now that the query is defined, execute it
    cur.execute(query, (user_id, user_id))
    tasks = cur.fetchall()
 
    # Format the `due_on` date as DD/MM/YYYY
    for task in tasks:
        task['due_on'] = task['due_on'].strftime('%d/%m/%Y')
 
    cur.close()
    conn.close()
 
    return jsonify(tasks)
 
 



# Route: View Activity
# Route: View Activity
def view_activity_user(activity_id):
    regulation_id = request.args.get('regulation_id')
    role = request.args.get('role')
    due_on = request.args.get('due_on')
    user_id = session.get('user_id')
 
    # Ensure that regulation_id and due_on are present
    if not regulation_id or not due_on:
        return jsonify({"error": "regulation_id and due_on are required"}), 400
 
    conn, cur = connect_to_database()
    if conn is None or cur is None:
        return jsonify({"error": "Database connection failed"}), 500
 
    try:
        # Fetch the preparation status and remarks (or any other progress fields) from the DB
        prep_status_query = """
            SELECT status, remarks  -- Add any other fields that track progress
            FROM entity_regulation_tasks
            WHERE activity_id = %s AND regulation_id = %s AND preparation_responsibility = %s AND due_on = %s
        """
        cur.execute(prep_status_query, (activity_id, regulation_id, user_id, due_on))
        task_progress = cur.fetchone()
 
        if not task_progress:
            return jsonify({"error": "No task found for the given activity and due date"}), 404
 
        # Log the current progress
        print(f"Task progress: {task_progress}")
 
        # Retrieve status and remarks (or other progress details)
        status = task_progress.get('status')
        remarks = task_progress.get('remarks', '')  # Default to empty if no remarks
 
        # Check if the status is 'Completed' for preparation responsibility, restrict review if not completed
        if role == 'review' and status != 'Completed':
            return jsonify({"error": "Cannot review until preparation is completed."}), 403
 
        # Fetch the activity details along with the regulation_name and mandatory_optional
        activity_query = """
            SELECT a.activity_id, a.activity, a.activity_description, r.regulation_name, a.mandatory_optional
            FROM activity_master a
            JOIN regulation_master r ON a.regulation_id = r.regulation_id
            WHERE a.regulation_id = %s AND a.activity_id = %s
        """
        cur.execute(activity_query, (regulation_id, activity_id))
        activity = cur.fetchone()
 
        if not activity:
            return jsonify({"error": "No activity found with the given details"}), 404
 
        # Check if the 'M' value is part of the mandatory_optional field
        is_mandatory = 'M' in activity['mandatory_optional']
 
        # Capture review_start_date if the user role is review
        if role == 'review':
            review_start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_review_query = """
                UPDATE entity_regulation_tasks
                SET review_start_date = %s
                WHERE activity_id = %s AND regulation_id = %s AND due_on = %s
            """
            cur.execute(update_review_query, (review_start_date, activity_id, regulation_id, due_on))
            conn.commit()
 
        # Render the activity details with current progress (remarks and status)
        current_date = datetime.now().date()
        return render_template(
            'user/activity_details.html',
            activity=activity,
            role=role,
            is_mandatory=is_mandatory,  # Flag to show asterisk if the activity is mandatory
            regulation_id=regulation_id,
            user_id=user_id,
            entity_id=session.get('entity_id'),
            due_on=due_on,
            current_date=current_date,
            status=status,  # Pass the current status from the database (e.g., 'WIP')
            remarks=remarks  # Pass the current remarks from the database
        )
 
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred."}), 500
 
    finally:
        cur.close()
        conn.close()


def send_email_reviewer(to_email, subject, body):
    msg = Message(subject, recipients=[to_email])
    msg.body = body
    try:
        mail.send(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def submit_activity_user():
    # Extract form data
    activity_id = request.form['activity_id']
    regulation_id = request.form['regulation_id']
    role = request.form['role']
    due_on = request.form['due_on']
    remarks = request.form.get('remarks', '')
    status_inital_user = request.form.get('status')  # Default status
    # print(status)
    review_remarks = request.form.get('review_comments', '')
    upload_file = request.files.get('upload_file')
    review_upload_file = request.files.get('review_upload_file')

    # Connect to the database
    conn, cur = connect_to_database()
    if conn is None or cur is None:
        print("Error: Unable to connect to the database.")
        return jsonify({"error": "Database connection failed"}), 500

    # Initialize file_path
    file_path = None
    email_info = None  # We'll use this to store information for the email

    try:


        if status_inital_user=="Completed":


            # print("eneterd")

            # # Fetch the preparation status
            # prep_status_query = """
            #     SELECT status
            #     FROM entity_regulation_tasks
            #     WHERE activity_id = %s AND regulation_id = %s  AND due_on = %s

            # """
            # cur.execute(prep_status_query, (activity_id, regulation_id, due_on))

            # status = cur.fetchone()
            status="Completed"

        elif status_inital_user==None:
            status="Completed"

            

        else:
            status=status_inital_user

        print(status, type(status))
        # For preparation responsibility
        if role == 'preparation' and upload_file:
            # Save the uploaded file
            file_path = f'static/uploads/{upload_file.filename}'
            upload_file.save(file_path)
            print(f"File saved at {file_path}")
            
            # Set start and end dates based on status
            start_date = None
            end_date = None
            if status == 'WIP':
                start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif status == 'Completed':
                end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Fetch email information for review responsibility if task is completed
                email_query = """
                    SELECT u.email_id, u.user_name
                    FROM users u
                    JOIN entity_regulation_tasks e ON u.user_id = e.review_responsibility
                    WHERE e.activity_id = %s AND e.regulation_id = %s AND e.due_on = %s
                """
                cur.execute(email_query, (activity_id, regulation_id, due_on))
                email_info = cur.fetchone()  # Fetch email info for later use

            # Update query for preparation responsibility
            query = """
                UPDATE entity_regulation_tasks
                SET remarks = %s, status = %s, upload = %s, start_date = COALESCE(start_date, %s), end_date = %s
                WHERE activity_id = %s AND regulation_id = %s AND due_on = %s
            """
            cur.execute(query, (remarks, status, file_path, start_date, end_date, activity_id, regulation_id, due_on))

        # For review responsibility
        elif role == 'review':
            review_end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Save the uploaded review file
            if review_upload_file:
                file_path = f'static/uploads/{review_upload_file.filename}'
                review_upload_file.save(file_path)
                print(f"Review file saved at {file_path}")

            # Update query for review responsibility
            query = """
                UPDATE entity_regulation_tasks
                SET review_remarks = %s, review_upload = %s, review_end_date = %s, status = %s
                WHERE activity_id = %s AND regulation_id = %s AND due_on = %s
            """
            cur.execute(query, (review_remarks, file_path, review_end_date, status, activity_id, regulation_id, due_on))

        # Commit the transaction to save changes
        conn.commit()
        print("Data committed successfully")

        # --- AFTER COMMIT, SEND EMAIL (if task is completed by preparation role) ---
        if status == 'Completed' and email_info:
            try:
                to_email = email_info['email_id']
                user_name = email_info['user_name']
                subject = "Task Completed - Ready for Review"

                # Fetch entity_id to include in the email
                entity_id_query = """
                    SELECT entity_id 
                    FROM entity_regulation_tasks 
                    WHERE activity_id = %s AND regulation_id = %s AND due_on = %s
                """
                cur.execute(entity_id_query, (activity_id, regulation_id, due_on))
                factory_info = cur.fetchone()
                entity_id = factory_info['entity_id'] if factory_info else "Unknown"

                # Prepare the email body with regulation_id, entity_id, and due_on
                body = f"""
Dear {user_name},

The task with the following details has been completed and is now ready for your review:

- **Activity ID**: {activity_id}
- **Regulation ID**: {regulation_id}
- **Factory ID**: {entity_id}
- **Due On**: {due_on}
- **Remarks**: {remarks}

Please proceed with the review at your earliest convenience.

Best regards,
The Compliance Team
                """
                send_email_reviewer(to_email, subject, body)
                print(f"Email sent to {to_email}")
            except Exception as email_error:
                print(f"Email sending failed: {email_error}")
                # Continue with the process even if the email fails

    except mysql.connector.Error as db_error:
        print(f"Database error: {db_error}")
        conn.rollback()  # Rollback the transaction on error
        return jsonify({"error": "Database operation failed"}), 500

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()  # Rollback on any other exception

    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()

    return jsonify({"success": True})


# def submit_activity_user():
#     # Extract form data
#     activity_id = request.form['activity_id']
#     regulation_id = request.form['regulation_id']
#     role = request.form['role']
#     due_on = request.form['due_on']
#     remarks = request.form.get('remarks', '')  # Default to an empty string if not provided
#     status = request.form.get('status', 'Yet to Start')  # Default status
#     review_remarks = request.form.get('review_comments', '')  # Default to an empty string if not provided
#     upload_file = request.files.get('upload_file')
#     review_upload_file = request.files.get('review_upload_file')

#     # Connect to the database
#     conn, cur = connect_to_database()
#     if conn is None or cur is None:
#         print("Error: Unable to connect to the database.")
#         return jsonify({"error": "Database connection failed"}), 500
#     else:
#         print("Database connected successfully.")

#     # Initialize file_path to None
#     file_path = None

#     try:
#         # For preparation responsibility
#         if role == 'preparation':
#             # If file is uploaded, save the file and set the file path, else keep it None
#             if upload_file and upload_file.filename != '':
#                 file_path = f'static/uploads/{upload_file.filename}'
#                 upload_file.save(file_path)
#                 print(f"File saved at {file_path}")
#             else:
#                 file_path = None

#             # Set start and end dates based on status
#             start_date = None
#             end_date = None
#             if status == 'WIP':
#                 start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             elif status == 'Completed':
#                 end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#             # Debugging log for query parameters
#             print(f"Preparing query with: activity_id={activity_id}, regulation_id={regulation_id}, due_on={due_on}, remarks={remarks}, status={status}, file_path={file_path}, start_date={start_date}, end_date={end_date}")

#             # Update query for preparation responsibility, using COALESCE to handle empty fields
#             query = """
#                 UPDATE entity_regulation_tasks
#                 SET remarks = COALESCE(%s, remarks), status = %s, upload = COALESCE(%s, upload), 
#                     start_date = COALESCE(start_date, %s), end_date = COALESCE(%s, end_date)
#                 WHERE activity_id = %s AND regulation_id = %s AND due_on = %s
#             """
#             cur.execute(query, (remarks or None, status, file_path, start_date, end_date, activity_id, regulation_id, due_on))

#             # Check affected rows
#             rows_affected = cur.rowcount
#             print(f"Rows affected (preparation): {rows_affected}")
#             if rows_affected == 0:
#                 print(f"Error: No rows were updated for the query: {query} with values {remarks, status, file_path, start_date, end_date, activity_id, regulation_id, due_on}")
#                 raise Exception("No rows updated for preparation responsibility.")

#         # For review responsibility
#         elif role == 'review':
#             review_end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#             # Save the uploaded review file, or set to None if not provided
#             if review_upload_file and review_upload_file.filename != '':
#                 file_path = f'static/uploads/{review_upload_file.filename}'
#                 review_upload_file.save(file_path)
#                 print(f"Review file saved at {file_path}")
#             else:
#                 file_path = None

#             # Debugging log for query parameters
#             print(f"Preparing review query with: review_remarks={review_remarks}, file_path={file_path}, review_end_date={review_end_date}, status={status}, activity_id={activity_id}, regulation_id={regulation_id}, due_on={due_on}")

#             # Update query for review responsibility, using COALESCE to handle empty fields
#             query = """
#                 UPDATE entity_regulation_tasks
#                 SET review_remarks = COALESCE(%s, review_remarks), review_upload = COALESCE(%s, review_upload), 
#                     review_end_date = COALESCE(%s, review_end_date), status = %s
#                 WHERE activity_id = %s AND regulation_id = %s AND due_on = %s
#             """
#             cur.execute(query, (review_remarks or None, file_path, review_end_date, status, activity_id, regulation_id, due_on))

#             # Check affected rows
#             rows_affected = cur.rowcount
#             print(f"Rows affected (review): {rows_affected}")
#             if rows_affected == 0:
#                 print(f"Error: No rows were updated for the query: {query} with values {review_remarks, file_path, review_end_date, status, activity_id, regulation_id, due_on}")
#                 raise Exception("No rows updated for review responsibility.")

#         # Commit the transaction to save changes
#         conn.commit()
#         print("Data committed successfully")

#     except mysql.connector.Error as db_error:
#         print(f"Database error: {db_error}")
#         conn.rollback()  # Rollback the transaction on error
#         return jsonify({"error": "Database operation failed"}), 500

#     except Exception as e:
#         print(f"Error: {e}")
#         conn.rollback()  # Rollback on any other exception

#     finally:
#         # Close the cursor and connection
#         cur.close()
#         conn.close()

#     return jsonify({"success": True})


def entity_user_main():
    user_id = session.get('user_id')
    entity_id = session.get('entity_id')
 
    if not user_id or not entity_id:
        return redirect(url_for('index'))  # Redirect to login page if not logged in
   
    return render_template('user/entity_user.html', user_id=user_id, entity_id=entity_id)

# ----------- Utility Functions -----------
# Function: Swal Alert for Response
def swal_alert(title, text, icon):
    return {
        'title': title,
        'text': text,
        'icon': icon
    }
 
# Function: Swal Redirect for Response
def swal_redirect(title, text, icon, redirect_url):
    return {
        'title': title,
        'text': text,
        'icon': icon,
        'redirect': url_for(redirect_url)
    }


#--------------------------------------------------Entity & Global Admin-----------------------------------------------------------
def entity_admin():
    user_id = session.get('user_id')
    entity_id = session.get('entity_id')
 
    if not user_id or not entity_id:
        return redirect(url_for('index'))
 
    return render_template('user/entity_admin.html', user_id=user_id, entity_id=entity_id)


def global_admin():
    user_id = session.get('user_id')
    entity_id = session.get('entity_id')
 
    if not user_id or not entity_id:
        return redirect(url_for('index'))
 
    return render_template('user/global_admin.html', user_id=user_id, entity_id=entity_id)
 