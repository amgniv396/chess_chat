import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from tkinter import messagebox


class SignInApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Authentication")
        self.geometry("400x500")
        self.resizable(False, False)

        # User database (In a real app, this would be a secure database)
        self.users = {
            "user@example.com": "password123"
        }

        # Email verification code storage
        self.verification_codes = {}

        # Create main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=BOTH, expand=True, padx=20, pady=30)

        # Create frames for different pages
        self.sign_in_frame = ttk.Frame(self.main_container)
        self.forgot_password_frame = ttk.Frame(self.main_container)
        self.verification_frame = ttk.Frame(self.main_container)
        self.reset_password_frame = ttk.Frame(self.main_container)
        self.sign_up_frame = ttk.Frame(self.main_container)

        # Initialize pages
        self.init_sign_in_page()
        self.init_forgot_password_page()
        self.init_verification_page()
        self.init_reset_password_page()
        self.init_sign_up_page()

        # Show sign in page by default
        self.show_sign_in_page()

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

        # Username
        self.username_entry = ttk.Entry(self.sign_in_frame, width=30)
        self.username_entry.pack(pady=10)
        self.set_placeholder(self.username_entry, "Username")

        # Password
        self.password_entry = ttk.Entry(self.sign_in_frame, width=30, show="*")
        self.password_entry.pack(pady=10)
        self.set_placeholder(self.password_entry, "Password")

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
            command=self.send_verification_code,
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
        ttk.Button(
            self.verification_frame,
            text="← Back to Forgot Password",
            command=self.show_forgot_password_page,
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
            command=self.sign_up,
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

    def show_forgot_password_page(self):
        self.sign_in_frame.pack_forget()
        self.forgot_password_frame.pack(fill=BOTH, expand=True)
        self.verification_frame.pack_forget()
        self.reset_password_frame.pack_forget()
        self.sign_up_frame.pack_forget()

    def show_verification_page(self):
        self.sign_in_frame.pack_forget()
        self.forgot_password_frame.pack_forget()
        self.verification_frame.pack(fill=BOTH, expand=True)
        self.reset_password_frame.pack_forget()
        self.sign_up_frame.pack_forget()

    def show_reset_password_page(self):
        self.sign_in_frame.pack_forget()
        self.forgot_password_frame.pack_forget()
        self.verification_frame.pack_forget()
        self.reset_password_frame.pack(fill=BOTH, expand=True)
        self.sign_up_frame.pack_forget()

    def show_sign_up_page(self):
        self.sign_in_frame.pack_forget()
        self.forgot_password_frame.pack_forget()
        self.verification_frame.pack_forget()
        self.reset_password_frame.pack_forget()
        self.sign_up_frame.pack(fill=BOTH, expand=True)

    def sign_in(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Check if fields contain placeholders
        if username == "Username" or password == "Password":
            messagebox.showerror("Error", "Please enter both username and password")
            return

        if username in self.users and self.users[username] == password:
            messagebox.showinfo("Success", f"Welcome back, {username}!")
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def sign_out(self):
        if hasattr(self, 'username_entry'):
            self.username_entry.delete(0, 'end')
            self.set_placeholder(self.username_entry, "Username")

        if hasattr(self, 'password_entry'):
            self.password_entry.delete(0, 'end')
            self.set_placeholder(self.password_entry, "Password")

        messagebox.showinfo("Success", "Signed out successfully")

    def send_verification_code(self):
        email = self.forgot_email_entry.get()

        if email == "Email":
            messagebox.showerror("Error", "Please enter your email address")
            return

        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            return

        # Check if email exists in user database
        email_exists = False
        for user, value in self.users.items():
            if user == email or value == email:
                email_exists = True
                break

        if not email_exists:
            messagebox.showerror("Error", "Email not found in our records")
            return

        # Generate a random 6-digit code
        code = str(random.randint(100000, 999999))
        self.verification_codes[email] = code

        # Send email with verification code
        self.send_verification_email(email, code)

        # Navigate to verification page
        self.show_verification_page()

    def send_verification_email(self, email, code):
        # Email sending details (replace with your SMTP details)
        sender_email = "chess.master9544@gmail.com"
        sender_password = "xvdbnrghfruyoyfl"
        subject = "Password Reset Code"
        body = f"Your password reset code is: {code}"

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
        self.send_verification_code()

    def verify_code(self):
        email = self.forgot_email_entry.get()
        code = self.verification_code_entry.get()

        if code == "Verification Code":
            messagebox.showerror("Error", "Please enter the verification code")
            return

        if email in self.verification_codes and self.verification_codes[email] == code:
            messagebox.showinfo("Success", "Code verified successfully!")
            # Navigate to reset password page
            self.show_reset_password_page()
        else:
            messagebox.showerror("Error", "Invalid verification code")

    def reset_password(self):
        email = self.forgot_email_entry.get()
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

        # Update password in the database
        for username, value in self.users.items():
            if username == email or value == email:
                self.users[username] = new_password
                break

        messagebox.showinfo("Success", "Password reset successfully!")

        # Navigate back to sign in page
        self.show_sign_in_page()

    def sign_up(self):
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

        if email in self.users or username in self.users:
            messagebox.showerror("Error", "Username or email already exists")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return

        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters long")
            return

        # Add the new user to the database
        self.users[username] = password
        self.users[email] = email  # Store email as well for verification

        messagebox.showinfo("Success", f"Account created for {username}!")

        # Clear fields and navigate back to sign in page
        self.signup_username_entry.delete(0, 'end')
        self.signup_email_entry.delete(0, 'end')
        self.signup_password_entry.delete(0, 'end')
        self.signup_confirm_password_entry.delete(0, 'end')

        self.set_placeholder(self.signup_username_entry, "Username")
        self.set_placeholder(self.signup_email_entry, "Email")
        self.set_placeholder(self.signup_password_entry, "Password")
        self.set_placeholder(self.signup_confirm_password_entry, "Confirm Password")

        self.show_sign_in_page()

    def return_to_previous_page(self):
        # In a real app, this would navigate back to the previous page
        # For this demo, we'll just exit the application
        self.quit()

    def validate_email(self, email):
        # Simple email validation using regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


# Run the application
if __name__ == "__main__":
    app = SignInApp()
    app.mainloop()