import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from tkinter import messagebox
from SQLL_database import UserDatabase
import sys
import os
import tkinter as tk


class SignInApp:
    def __init__(self, root=None):
        # Use existing root if provided, otherwise create a new one
        if root:
            self.root = root
        else:
            self.root = tk.Tk()

        # Apply ttkbootstrap theme
        self.style = ttk.Style(theme="darkly")

        # Set window title and make it fullscreen
        self.root.title("Authentication")
        self.root.attributes('-fullscreen', True)

        # Initialize database
        self.db = UserDatabase()

        # Add sample user for testing if needed
        self.db.add_sample_user()

        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Create main container with centered content
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=True)

        # Create content frame to center the sign-in forms (increased height for server fields)
        self.content_frame = ttk.Frame(self.main_container, width=400, height=600)
        self.content_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

        # Create frames for different pages
        self.sign_in_frame = ttk.Frame(self.content_frame)
        self.forgot_password_frame = ttk.Frame(self.content_frame)
        self.verification_frame = ttk.Frame(self.content_frame)
        self.reset_password_frame = ttk.Frame(self.content_frame)
        self.sign_up_frame = ttk.Frame(self.content_frame)
        self.signup_verification_frame = ttk.Frame(self.content_frame)

        # Initialize pages
        self.init_sign_in_page()
        self.init_forgot_password_page()
        self.init_verification_page()
        self.init_reset_password_page()
        self.init_sign_up_page()
        self.init_signup_verification_page()

        # Add variable to track current verification mode
        self.verification_mode = "password_reset"  # or "signup"

        # Track current email for verification purposes
        self.current_email = ""
        self.current_reset_code = ""

        # Show sign in page by default
        self.show_sign_in_page()

        # Add a close button for exiting fullscreen
        close_btn = ttk.Button(
            self.root, text="×",
            command=self.quit,
            bootstyle="danger",
            width=3
        )
        close_btn.place(x=self.screen_width - 50, y=10)

    def set_placeholder(self, entry, placeholder):
        entry.insert(0, placeholder)
        entry.configure(foreground="#888888")

        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.configure(foreground="#ffffff")

        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.configure(foreground="#888888")

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def init_sign_in_page(self):
        # Title
        ttk.Label(self.sign_in_frame, text="Sign In", font=("Helvetica", 24, "bold")).pack(pady=20)

        # Username or Email
        self.username_entry = ttk.Entry(self.sign_in_frame, width=30)
        self.username_entry.pack(pady=10)
        self.set_placeholder(self.username_entry, "Username or Email")

        # Password
        self.password_entry = ttk.Entry(self.sign_in_frame, width=30, show="*")
        self.password_entry.pack(pady=10)
        self.set_placeholder(self.password_entry, "Password")

        # Server Connection Section
        server_frame = ttk.LabelFrame(self.sign_in_frame, text="Server Connection", padding=10)
        server_frame.pack(pady=15, padx=20, fill="x")

        # Server IP
        self.server_ip_entry = ttk.Entry(server_frame, width=30)
        self.server_ip_entry.pack(pady=5)
        self.set_placeholder(self.server_ip_entry, "Server IP (default: 127.0.0.1)")

        # Server Port
        self.server_port_entry = ttk.Entry(server_frame, width=30)
        self.server_port_entry.pack(pady=5)
        self.set_placeholder(self.server_port_entry, "Server Port (default: 33000)")

        # Sign In Button
        ttk.Button(
            self.sign_in_frame,
            text="Sign In",
            command=self.sign_in,
            bootstyle=PRIMARY
        ).pack(pady=10)

        # Forgot Password Link
        ttk.Button(
            self.sign_in_frame,
            text="Forgot Password?",
            command=self.show_forgot_password_page,
            bootstyle=LINK
        ).pack()

        # Sign Up Link
        ttk.Button(
            self.sign_in_frame,
            text="Don't have an account? Sign Up",
            command=self.show_sign_up_page,
            bootstyle=LINK
        ).pack()

    def init_forgot_password_page(self):
        # Title
        ttk.Label(self.forgot_password_frame, text="Forgot Password", font=("Helvetica", 24, "bold")).pack(pady=20)

        # Email
        self.forgot_email_entry = ttk.Entry(self.forgot_password_frame, width=30)
        self.forgot_email_entry.pack(pady=10)
        self.set_placeholder(self.forgot_email_entry, "Email")

        # Send Code Button
        ttk.Button(
            self.forgot_password_frame,
            text="Send Verification Code",
            command=self.send_password_reset_verification_code,
            bootstyle=PRIMARY
        ).pack(pady=20)

        # Return Button
        ttk.Button(
            self.forgot_password_frame,
            text="← Back to Sign In",
            command=self.show_sign_in_page,
            bootstyle=LINK
        ).pack(pady=(20, 0))

    def init_verification_page(self):
        # Title
        ttk.Label(self.verification_frame, text="Verification", font=("Helvetica", 24, "bold")).pack(pady=20)

        # Description
        ttk.Label(
            self.verification_frame,
            text="Enter the 6-digit code sent to your email",
            wraplength=360
        ).pack(pady=(0, 20))

        # Verification Code
        self.verification_code_entry = ttk.Entry(self.verification_frame, width=30)
        self.verification_code_entry.pack(pady=10)
        self.set_placeholder(self.verification_code_entry, "Verification Code")

        # Verify Button
        ttk.Button(
            self.verification_frame,
            text="Verify Code",
            command=self.verify_code,
            bootstyle=PRIMARY
        ).pack(pady=10)

        # Resend Code
        ttk.Button(
            self.verification_frame,
            text="Resend Code",
            command=self.resend_verification_code,
            bootstyle=SECONDARY
        ).pack(pady=(0, 20))

        # Return Button
        self.verification_back_button = ttk.Button(
            self.verification_frame,
            text="← Back to Forgot Password",
            command=self.show_forgot_password_page,
            bootstyle=LINK
        )
        self.verification_back_button.pack(pady=(20, 0))

    def init_signup_verification_page(self):
        # Title
        ttk.Label(self.signup_verification_frame, text="Email Verification", font=("Helvetica", 24, "bold")).pack(
            pady=20)

        # Description
        ttk.Label(
            self.signup_verification_frame,
            text="Enter the 6-digit code sent to your email to complete registration",
            wraplength=360
        ).pack(pady=(0, 20))

        # Verification Code
        self.signup_verification_code_entry = ttk.Entry(self.signup_verification_frame, width=30)
        self.signup_verification_code_entry.pack(pady=10)
        self.set_placeholder(self.signup_verification_code_entry, "Verification Code")

        # Verify Button
        ttk.Button(
            self.signup_verification_frame,
            text="Verify Code",
            command=self.verify_signup_code,
            bootstyle=PRIMARY
        ).pack(pady=10)

        # Resend Code
        ttk.Button(
            self.signup_verification_frame,
            text="Resend Code",
            command=self.resend_signup_verification_code,
            bootstyle=SECONDARY
        ).pack(pady=(0, 20))

        # Return Button
        ttk.Button(
            self.signup_verification_frame,
            text="← Back to Sign Up",
            command=self.show_sign_up_page,
            bootstyle=LINK
        ).pack(pady=(20, 0))

    def init_reset_password_page(self):
        # Title
        ttk.Label(self.reset_password_frame, text="Reset Password", font=("Helvetica", 24, "bold")).pack(pady=20)

        # New Password
        self.new_password_entry = ttk.Entry(self.reset_password_frame, width=30, show="*")
        self.new_password_entry.pack(pady=10)
        self.set_placeholder(self.new_password_entry, "New Password")

        # Confirm Password
        self.confirm_password_entry = ttk.Entry(self.reset_password_frame, width=30, show="*")
        self.confirm_password_entry.pack(pady=10)
        self.set_placeholder(self.confirm_password_entry, "Confirm Password")

        # Reset Button
        ttk.Button(
            self.reset_password_frame,
            text="Reset Password",
            command=self.reset_password,
            bootstyle=SUCCESS
        ).pack(pady=20)

        # Return Button
        ttk.Button(
            self.reset_password_frame,
            text="← Back to Sign In",
            command=self.show_sign_in_page,
            bootstyle=LINK
        ).pack(pady=(20, 0))

    def init_sign_up_page(self):
        # Title
        ttk.Label(self.sign_up_frame, text="Sign Up", font=("Helvetica", 24, "bold")).pack(pady=20)

        # Username
        self.signup_username_entry = ttk.Entry(self.sign_up_frame, width=30)
        self.signup_username_entry.pack(pady=10)
        self.set_placeholder(self.signup_username_entry, "Username")

        # Email
        self.signup_email_entry = ttk.Entry(self.sign_up_frame, width=30)
        self.signup_email_entry.pack(pady=10)
        self.set_placeholder(self.signup_email_entry, "Email")

        # Password
        self.signup_password_entry = ttk.Entry(self.sign_up_frame, width=30, show="*")
        self.signup_password_entry.pack(pady=10)
        self.set_placeholder(self.signup_password_entry, "Password")

        # Confirm Password
        self.signup_confirm_password_entry = ttk.Entry(self.sign_up_frame, width=30, show="*")
        self.signup_confirm_password_entry.pack(pady=10)
        self.set_placeholder(self.signup_confirm_password_entry, "Confirm Password")

        # Sign Up Button
        ttk.Button(
            self.sign_up_frame,
            text="Sign Up",
            command=self.initiate_sign_up,
            bootstyle=SUCCESS
        ).pack(pady=20)

        # Return Button
        ttk.Button(
            self.sign_up_frame,
            text="Already have an account? Sign In",
            command=self.show_sign_in_page,
            bootstyle=LINK
        ).pack(pady=(10, 0))

    def show_sign_in_page(self):
        self.sign_in_frame.pack(fill=BOTH, expand=True)
        self.forgot_password_frame.pack_forget()
        self.verification_frame.pack_forget()
        self.reset_password_frame.pack_forget()
        self.sign_up_frame.pack_forget()
        self.signup_verification_frame.pack_forget()

    def show_forgot_password_page(self):
        self.sign_in_frame.pack_forget()
        self.forgot_password_frame.pack(fill=BOTH, expand=True)
        self.verification_frame.pack_forget()
        self.reset_password_frame.pack_forget()
        self.sign_up_frame.pack_forget()
        self.signup_verification_frame.pack_forget()

    def show_verification_page(self, mode="password_reset"):
        self.verification_mode = mode
        if mode == "password_reset":
            self.verification_back_button.configure(text="← Back to Forgot Password",
                                                    command=self.show_forgot_password_page)

        self.sign_in_frame.pack_forget()
        self.forgot_password_frame.pack_forget()
        self.verification_frame.pack(fill=BOTH, expand=True)
        self.reset_password_frame.pack_forget()
        self.sign_up_frame.pack_forget()
        self.signup_verification_frame.pack_forget()

    def show_signup_verification_page(self):
        self.sign_in_frame.pack_forget()
        self.forgot_password_frame.pack_forget()
        self.verification_frame.pack_forget()
        self.reset_password_frame.pack_forget()
        self.sign_up_frame.pack_forget()
        self.signup_verification_frame.pack(fill=BOTH, expand=True)

    def show_reset_password_page(self):
        self.sign_in_frame.pack_forget()
        self.forgot_password_frame.pack_forget()
        self.verification_frame.pack_forget()
        self.reset_password_frame.pack(fill=BOTH, expand=True)
        self.sign_up_frame.pack_forget()
        self.signup_verification_frame.pack_forget()

    def show_sign_up_page(self):
        self.sign_in_frame.pack_forget()
        self.forgot_password_frame.pack_forget()
        self.verification_frame.pack_forget()
        self.reset_password_frame.pack_forget()
        self.sign_up_frame.pack(fill=BOTH, expand=True)
        self.signup_verification_frame.pack_forget()

    def get_server_connection_info(self):
        """Get server IP and port from the input fields"""
        server_ip = self.server_ip_entry.get()
        server_port = self.server_port_entry.get()

        # Use defaults if placeholders are still present or fields are empty
        if server_ip == "Server IP (default: 127.0.0.1)" or not server_ip.strip():
            server_ip = "127.0.0.1"

        if server_port == "Server Port (default: 33000)" or not server_port.strip():
            server_port = "33000"

        try:
            port = int(server_port)
            if port < 1 or port > 65535:
                raise ValueError("Port out of range")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number. Using default port 33000.")
            port = 33000

        return server_ip.strip(), port

    def load_home_screen(self, username):
        """Load the home screen module and transition to it"""
        # Add the current directory to sys.path if it's not already there
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)

        # Import homeScreen_graphics
        try:
            import homeScreen_graphics
            # Get server connection info and pass it to the chess client
            server_ip, server_port = self.get_server_connection_info()

            # Set the server connection info in the chess client before loading home screen
            import chess_client_graphics
            chess_client_graphics.set_server_connection(server_ip, server_port)

            # Pass the current window and username to the home screen module
            homeScreen_graphics.run_home_screen(self.root, username)

        except ImportError as e:
            messagebox.showerror("Error", f"Could not load home screen: {str(e)}")

    def sign_in(self):
        username_or_email = self.username_entry.get()
        password = self.password_entry.get()

        # Check if fields contain placeholders
        if username_or_email == "Username or Email" or password == "Password":
            messagebox.showerror("Error", "Please enter both username/email and password")
            return

        # Authenticate with database
        success, result = self.db.authenticate_user(username_or_email, password)

        if success:
            messagebox.showinfo("Success", f"Welcome back, {result['username']}!")
            # Load the home screen after successful login
            self.load_home_screen(result['username'])
        else:
            messagebox.showerror("Error", result)

    def send_password_reset_verification_code(self):
        email = self.forgot_email_entry.get()

        if email == "Email":
            messagebox.showerror("Error", "Please enter your email address")
            return

        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            return

        # Check if email exists in database
        if not self.db.email_exists(email):
            messagebox.showerror("Error", "Email not found in our records")
            return

        # Generate a random 6-digit code
        code = str(random.randint(100000, 999999))

        # Store code in database
        success, message = self.db.create_password_reset(email, code)

        if not success:
            messagebox.showerror("Error", message)
            return

        # Save current email and code for verification
        self.current_email = email
        self.current_reset_code = code

        # Send email with verification code
        self.send_verification_email(email, code, "Password Reset")

        # Navigate to verification page
        self.show_verification_page("password_reset")

    def initiate_sign_up(self):
        username = self.signup_username_entry.get()
        email = self.signup_email_entry.get()
        password = self.signup_password_entry.get()
        confirm_password = self.signup_confirm_password_entry.get()

        # Check if fields contain placeholders
        if (username == "Username" or email == "Email" or
                password == "Password" or confirm_password == "Confirm Password"):
            messagebox.showerror("Error", "Please fill in all fields")
            return

        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            return

        if self.db.email_exists(email):
            messagebox.showerror("Error", "Email already exists")
            return

        if self.db.username_exists(username):
            messagebox.showerror("Error", "Username already exists")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return

        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters long")
            return

        # Generate and send verification code
        code = str(random.randint(100000, 999999))

        # Add to pending users
        success = self.db.add_pending_user(username, email, password, code)

        if not success:
            messagebox.showerror("Error", "Failed to register user")
            return

        # Save current email
        self.current_email = email

        # Send verification email
        self.send_verification_email(email, code, "Account Verification")

        # Navigate to signup verification page
        self.show_signup_verification_page()

    def send_verification_email(self, email, code, purpose="Password Reset"):
        # Email sending details (replace with your SMTP details)
        sender_email = "chess.master9544@gmail.com"
        sender_password = "xvdbnrghfruyoyfl"
        subject = f"{purpose} Code"
        body = f"Your {purpose.lower()} code is: {code}"

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, msg.as_string())
            print(f"Verification code sent to {email}: {code}")
            messagebox.showinfo("Success", "Verification code sent to your email")
        except Exception as e:
            print(f"Failed to send email: {e}")
            messagebox.showerror("Error", f"Failed to send email: {e}")

    def resend_verification_code(self):
        if self.verification_mode == "password_reset":
            self.send_password_reset_verification_code()

    def resend_signup_verification_code(self):
        email = self.current_email

        if email:
            # Generate a new code
            code = str(random.randint(100000, 999999))

            # Update verification code in database
            success, message = self.db.resend_verification(email, code)

            if success:
                self.send_verification_email(email, code, "Account Verification")
            else:
                messagebox.showerror("Error", message)
        else:
            messagebox.showerror("Error", "Invalid email address")

    def verify_code(self):
        code = self.verification_code_entry.get()
        email = self.current_email

        if code == "Verification Code":
            messagebox.showerror("Error", "Please enter the verification code")
            return

        if not email:
            messagebox.showerror("Error", "Email not found")
            return

        # Verify code with database
        success, message = self.db.verify_reset_code(email, code)

        if success:
            messagebox.showinfo("Success", "Code verified successfully!")
            self.current_reset_code = code
            # Navigate to reset password page
            self.show_reset_password_page()
        else:
            messagebox.showerror("Error", message)

    def verify_signup_code(self):
        code = self.signup_verification_code_entry.get()
        email = self.current_email

        if code == "Verification Code":
            messagebox.showerror("Error", "Please enter the verification code")
            return

        if not email:
            messagebox.showerror("Error", "No pending registration found")
            return

        # Verify code and complete registration
        success, message = self.db.verify_user(email, code)

        if success:
            messagebox.showinfo("Success", "Email verified! Your account has been created!")
            # Navigate back to sign in page
            self.show_sign_in_page()
        else:
            messagebox.showerror("Error", message)

    def reset_password(self):
        email = self.current_email
        reset_code = self.current_reset_code
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        if new_password == "New Password" or confirm_password == "Confirm Password":
            messagebox.showerror("Error", "Please fill in all fields")
            return

        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return

        if len(new_password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters long")
            return

        if not email or not reset_code:
            messagebox.showerror("Error", "Invalid password reset session")
            return

        # Reset password in database
        success, message = self.db.reset_password(email, reset_code, new_password)

        if success:
            messagebox.showinfo("Success", message)
            # Navigate back to sign in page
            self.show_sign_in_page()
        else:
            messagebox.showerror("Error", message)

    def validate_email(self, email):
        # Simple email validation using regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def quit(self):
        """Quit the application"""
        self.root.quit()


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = SignInApp(root)
    root.mainloop()