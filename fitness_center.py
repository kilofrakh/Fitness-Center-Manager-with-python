import cv2
import os
import datetime
import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import qrcode
import smtplib
from email.message import EmailMessage
from tkinter import ttk

# frame scrollable 
def create_scrollable_frame(parent):
    canvas = tk.Canvas(parent)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return canvas, scrollable_frame

# admin login function
def admin_login():
    #check
    def check_admin():
        #inpts
        username = username_entry.get()
        password = password_entry.get()
        # check inputs 
        if username == "admin" and password == "password": 
            messagebox.showinfo("Login Successful", "Welcome, Admin!")
            login_window.destroy()
        #error    
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
    #gui admin login
    login_window = tk.Toplevel()
    login_window.title("Admin Login")
    login_window.geometry("300x200")

    tk.Label(login_window, text="Username:").pack(pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Password:").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    tk.Button(login_window, text="Login", command=check_admin).pack(pady=10)
    login_window.transient(root)
    login_window.grab_set()
    root.wait_window(login_window)



# editing member details
def edit_member():
    member_name = name_entry.get()
    member = None
    for m in fitness_center["members"]:
        if m["name"].lower() == member_name.lower():
            member = m
            break

    if not member:
        messagebox.showerror("Error", "Member not found.")
        return

    new_contact_info = contact_entry.get()
    new_email = email_entry.get()
    expiry_date_str = expiry_entry.get()

    try:
        expiration_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    except ValueError:
        messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD.")
        return

    # Update the details
    if len(str(new_contact_info)) == 11: 
        member["contact_info"] = new_contact_info
    else:
        messagebox.showerror("Error", "Invalid contact info! Please enter a valid 11-digit phone number.")
        return
    if not str(new_email) == "":
        member["email"] = new_email
    
    member["expiration_date"] = str(expiration_date)


    save_data()
    messagebox.showinfo("Success", f"Member {member_name}'s details updated successfully!")
    clear_inputs()


# delete member
def delete_member():
    member_name = name_entry.get()
    global fitness_center
    updated_members = []

    #check if the member name is empty
    if not member_name:
        messagebox.showerror("Error", "Please enter a member name.")
        return
    
    for m in fitness_center["members"]:
        if m["name"].lower() != member_name.lower():
            updated_members.append(m)
    
    # Updateing members
    fitness_center["members"] = updated_members
    save_data()
    messagebox.showinfo("Success", f"Member {member_name} deleted successfully!")
    clear_inputs()



# send email with qr code
def send_email_with_qr(member_email, member_name, qr_image_path):
    try:
        # Set up email details
        sender_email = "sutfitnesscenter@gmail.com"  
        sender_password = "xtulxefebyihfebf"  
        subject = f"QR Code for {member_name} - Fitness Center"
        body = f"Dear {member_name},\n\nPlease find attached your QR code for signing in to the fitness center.\n\nBest regards,\nElsewedy Fitness Center Team"
        
        # Create email message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = member_email
        msg.set_content(body)
        
        # Attach QR code image
        with open(qr_image_path, 'rb') as file:
            qr_image_data = file.read()
            msg.add_attachment(qr_image_data, maintype='image', subtype='png', filename=f"{member_name}_qr.png")
        
        # Send the email via SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

       
        
    except Exception as e:
        pass


# generate QR code for member
def generate_qr_code(member_name, contact_info):
    qr_data = f"Name: {member_name}\nContact: {contact_info}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Save QR code file
    qr_image_path = os.path.join(FACE_IMAGES_DIR, f"{member_name}_qr.png")
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_image.save(qr_image_path)
    
    # Send the QR code email
    send_email_with_qr(contact_info, member_name, qr_image_path)  
    
    return qr_image_path



# activity log
def view_activity_log():
    # delteing the activity log
    for widget in log_frame.winfo_children():
        widget.destroy()

    # checking if there is an activity log
    if "activity_log" not in fitness_center or not fitness_center["activity_log"]:
        tk.Label(log_frame, text="No activity log available.", font=("Arial", 12)).pack()
        return

    # disolay acitvty log
    for log in fitness_center["activity_log"]:
        log_entry = f"Name: {log['name']}, Time: {log['time']}"
        tk.Label(log_frame, text=log_entry, font=("Arial", 10)).pack(anchor="w")



# Scan QR code for sign in for member
def sign_in_with_qr():
    video_capture = cv2.VideoCapture(0)
    messagebox.showinfo("QR Sign-In", "Position the QR code in front of the camera.")

    qr_code_detector = cv2.QRCodeDetector()

    while True:
        ret, frame = video_capture.read()
        if not ret:
            messagebox.showerror("Error", "Failed to access the camera.")
            return

        # Decode QR code with opencv
        data, bbox, _ = qr_code_detector.detectAndDecode(frame)
        if data:
            # decodeing the qr code
            qr_data_lines = data.split("\n")
            member_name = qr_data_lines[0].split(": ")[1]
            contact_info = qr_data_lines[1].split(": ")[1]

            # searching for the member
            member = None
            for m in fitness_center["members"]:
                if m["name"] == member_name and m["contact_info"] == contact_info:
                    member = m
                    break

            if member:
                # put the member in the activity log
                expiry = member.get("expiration_date")
            
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                fitness_center["activity_log"].append({
                    "name": member_name,
                    "time": timestamp,
                
                })
                save_data()
                # check if the membership has expired
                if datetime.datetime.strptime(expiry, "%Y-%m-%d").date() < datetime.datetime.now().date():
                   messagebox.showerror("Sign-In Failed", f"Membership for {member_name} has expired!")
                   return

                messagebox.showinfo("Sign-In Successful", f"Welcome, {member_name}!\nSigned in at {timestamp}.\nMembership Expiry: {expiry}")
                video_capture.release()
                cv2.destroyAllWindows()
                return
            else:
                messagebox.showerror("Sign-In Failed", "Member not found.")
                video_capture.release()
                cv2.destroyAllWindows()
                return

        # Display the live feed
        cv2.imshow("QR Sign-In (Press 'q' to exit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


# face images fils
FACE_IMAGES_DIR = "face_images"
if not os.path.exists(FACE_IMAGES_DIR):
    os.makedirs(FACE_IMAGES_DIR)

# Initialize fitness center data
fitness_center = {
    "members": [],
    "activities": {
        "gym": [],
        "yoga": [],
        "swimming": []
    },
    "activity_log": []
}

# Save and load data functions
def save_data():
    with open("fitness_center.json", "w") as file:
        json.dump(fitness_center, file, indent=4)

def load_data():
    global fitness_center
    if os.path.exists("fitness_center.json"):
        with open("fitness_center.json", "r") as file:
            fitness_center = json.load(file)
    if "activity_log" not in fitness_center:
        fitness_center["activity_log"] = []

# Generate report
def generate_report():
    # deleteing the old report
    for widget in report_frame.winfo_children():
        widget.destroy()

    if not fitness_center["members"]:
        tk.Label(report_frame, text="No members registered yet.", font=("Arial", 12)).pack()
        return

    for member in fitness_center["members"]:
        # Member details
        member_details = f"Name: {member['name']}\n" \
                         f"Contact Info: {member['contact_info']}\n" \
                         f"Membership Expiry: {member['expiration_date']}\n" \
                         f"Activities: {', '.join(member['activities']) if member['activities'] else 'None'}"

        tk.Label(report_frame, text=member_details, justify="left", font=("Arial", 10)).pack(anchor="w")

        # Member photo
        photo_path = member.get("photo_path")
        if photo_path and os.path.exists(photo_path):
            img = Image.open(photo_path).resize((100, 100))
            photo = ImageTk.PhotoImage(img)
            photo_label = tk.Label(report_frame, image=photo)
            photo_label.pack(anchor="w")
            photo_label.image = photo

        # Member QR code
        qr_code_path = member.get("qr_code_path")
        if qr_code_path and os.path.exists(qr_code_path):
            qr_img = Image.open(qr_code_path).resize((100, 100))
            qr_photo = ImageTk.PhotoImage(qr_img)
            qr_label = tk.Label(report_frame, image=qr_photo)
            qr_label.pack(anchor="w")
            qr_label.image = qr_photo

        tk.Label(report_frame, text="-" * 50).pack()

# Capture face image for member
def capture_face_image(member_name):
    video_capture = cv2.VideoCapture(0)
    messagebox.showinfo("Face Capture", "Please position your face in front of the camera.")
    
    while True:
        ret, frame = video_capture.read()
        if not ret:
            messagebox.showerror("Error", "Failed to access the camera.")
            return None

        # el live feed
        cv2.imshow("Face Capture (Press 's' to save or 'q' to cancel)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):  # Save el face
            image_path = os.path.join(FACE_IMAGES_DIR, f"{member_name}.jpg")
            cv2.imwrite(image_path, frame)
            video_capture.release()
            cv2.destroyAllWindows()
            return image_path
        elif key == ord('q'):  # Quit men ghair ma7fazha
            video_capture.release()
            cv2.destroyAllWindows()
            return None

# adding member 
def add_member():
    name = name_entry.get()
    contact_info = contact_entry.get()
    email = email_entry.get() 
    expiry_date_str = expiry_entry.get()

    # check inputs

    if not name:
        messagebox.showerror("Error", "Name cannot be empty!")
        return
    
    if len(str(contact_info)) != 11:
        messagebox.showerror("Error", "Invalid contact info! Please enter a valid 11-digit phone number.")
        return

    if not email or "@" not in email or "." not in email:
        messagebox.showerror("Error", "Invalid email address!")
        return

    try:
        expiration_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    except ValueError:
        messagebox.showerror("Error", "Invalid date format! Please enter in YYYY-MM-DD format.")
        return

    if expiration_date < datetime.datetime.now().date():
        messagebox.showerror("Error", "Membership expiry date cannot be in the past!")
        return
    
    # face image
    face_image_path = capture_face_image(name)
    if not face_image_path:
        return

    # Generate QR code
    qr_code_path = generate_qr_code(name, contact_info)

    # benba3t aala elemail elqrcode
    try:
        send_email_with_qr(email, name, qr_code_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email to {email}: {e}")
        return

    # add member to the data the jason file
    fitness_center["members"].append({
        "name": name,
        "contact_info": contact_info,
        "email": email,  
        "expiration_date": str(expiration_date),
        "activities": [],
        "photo_path": face_image_path,
        "qr_code_path": qr_code_path  
    })
    save_data()
    messagebox.showinfo("Success", f"Member {name} added successfully, and QR code sent to {email}!")
    clear_inputs()



# Register for an activity
def register_for_activity():
    member_name = member_name_entry.get()
    activity_name = activity_entry.get().lower()
    
    #check inputs
    if not member_name:
        messagebox.showerror("Error", "Please enter a member name.")
        return
    
    # check activity
    if activity_name not in fitness_center["activities"]:
        messagebox.showerror("Error", f"Activity '{activity_name}' not found. available activities are: {', '.join(fitness_center['activities'].keys())}")
        return

    # check member
    member = None
    for m in fitness_center["members"]:
       if m["name"].lower() == member_name.lower():
            member = m
            break
    if not member:
        messagebox.showerror("Error", "Member not found.")
        return

    # register the activity for the member
    member["activities"].append(activity_name)
    save_data()
    messagebox.showinfo("Success", f"{member_name} has been successfully registered for {activity_name}.")

    clear_inputs()



# Clearing the inputs
def clear_inputs():
    name_entry.delete(0, tk.END)
    contact_entry.delete(0, tk.END)
    expiry_entry.delete(0, tk.END)
    member_name_entry.delete(0, tk.END)
    activity_entry.delete(0, tk.END)
    email_entry.delete(0, tk.END)
    member_name_entry.delete(0, tk.END)
    activity_entry.delete(0, tk.END)
    

    

# GUI setup
root = tk.Tk()
root.title("Fitness Center Management")
root.geometry("800x600")

# admin login prompt
admin_login()


# create the scrollable frame
main_canvas, main_frame = create_scrollable_frame(root)



def search_and_filter_members():
    # search 
    def search_members():
        search_query = search_entry.get().lower()
        result_text.delete(1.0, tk.END)  
        # search member loop
        for member in fitness_center["members"]:
            if search_query in member["name"].lower():
                member_details = f"Name: {member['name']}\n" \
                                 f"Contact: {member['contact_info']}\n" \
                                 f"Email: {member['email']}\n" \
                                 f"Expiry Date: {member['expiration_date']}\n" \
                                 f"Activities: {', '.join(member['activities']) if member['activities'] else 'None'}\n"
                result_text.insert(tk.END, member_details + "-" * 50 + "\n")

    # filter
    def filter_members():

        filter_activity = filter_entry.get().lower()
        result_text.delete(1.0, tk.END)  
        # filter loop
        for member in fitness_center["members"]:
            if any(filter_activity in activity.lower() for activity in member["activities"]):
                member_details = f"Name: {member['name']}\n" \
                                 f"Contact: {member['contact_info']}\n" \
                                 f"Email: {member['email']}\n" \
                                 f"Expiry Date: {member['expiration_date']}\n" \
                                 f"Activities: {', '.join(member['activities']) if member['activities'] else 'None'}\n"
                result_text.insert(tk.END, member_details + "-" * 50 + "\n")

    # gui for search and filter
    search_window = tk.Toplevel(root)
    search_window.title("Search and Filter Members")
    search_window.geometry("500x400")

    # search
    tk.Label(search_window, text="Search by Name:").pack(pady=5)
    search_entry = tk.Entry(search_window)
    search_entry.pack(pady=5)
    tk.Button(search_window, text="Search", command=search_members).pack(pady=10)

    # ffilter 
    tk.Label(search_window, text="Filter by Activity:").pack(pady=5)
    filter_entry = tk.Entry(search_window)
    filter_entry.pack(pady=5)
    tk.Button(search_window, text="Filter", command=filter_members).pack(pady=10)

    # result
    result_text = tk.Text(search_window, wrap=tk.WORD, height=15, width=60)
    result_text.pack(pady=5)

    
    

# Add a button for searching and filtering members
search_filter_button = tk.Button(main_frame, text="Search and Filter Members", command=search_and_filter_members)
search_filter_button.pack()

    
# Inputs for adding a new member
name_label = tk.Label(main_frame, text="Name:")
name_label.pack()
name_entry = tk.Entry(main_frame)
name_entry.pack()

contact_label = tk.Label(main_frame, text="Contact Info:")
contact_label.pack()
contact_entry = tk.Entry(main_frame)
contact_entry.pack()

email_label = tk.Label(main_frame, text="Email:")
email_label.pack()
email_entry = tk.Entry(main_frame) 
email_entry.pack()

expiry_label = tk.Label(main_frame, text="Membership Expiry (YYYY-MM-DD):")
expiry_label.pack()
expiry_entry = tk.Entry(main_frame)
expiry_entry.pack()

add_member_button = tk.Button(main_frame, text="Add Member", command=add_member)
add_member_button.pack()

edit_member_button = tk.Button(main_frame, text="Edit Member", command=edit_member)
edit_member_button.pack()

delete_member_button = tk.Button(main_frame, text="Delete Member", command=delete_member)
delete_member_button.pack()


# Inputs for registering an activity
member_name_label = tk.Label(main_frame, text="Member Name:")
member_name_label.pack()
member_name_entry = tk.Entry(main_frame)
member_name_entry.pack()

activity_label = tk.Label(main_frame, text="Activity Name:")
activity_label.pack()
activity_entry = tk.Entry(main_frame)
activity_entry.pack()

register_activity_button = tk.Button(main_frame, text="Register for Activity", command=register_for_activity)
register_activity_button.pack()

# Sign-In button
sign_in_button = tk.Button(main_frame, text="Sign In with QR", command=sign_in_with_qr)
sign_in_button.pack()

# Buttons for activity log and reports
view_log_button = tk.Button(main_frame, text="View Activity Log", command=view_activity_log)
view_log_button.pack()

generate_report_button = tk.Button(main_frame, text="Generate Report", command=generate_report)
generate_report_button.pack()

# Frames for displaying logs and reports
log_frame = tk.Frame(main_frame)
log_frame.pack(pady=10)

report_frame = tk.Frame(main_frame)
report_frame.pack(pady=10)


# Load data
load_data()

# Start the GUI mainloop
root.mainloop()



