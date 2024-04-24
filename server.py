from getpass import getpass # for passwords

# web interface
from flask import Flask, render_template, flash, request

# payment
from venmo_api import Client, PaymentStatus
import time
import threading

# emails
import smtplib
import ssl

## email message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# configuration
import os.path

class Venmo:
    client = None

    def __init__(self):
        access_token = None
        # read if a access_token already exists
        if os.path.isfile("config/access_token.txt"):
            with open("config/access_token.txt", 'r') as file:
                access_token = file.read().rstrip()
        else:
            while access_token == None:
                # create a new access token if one doesn't already exist
                print("Provide a username and password for the account recieving the funds")
                username = input("Username: ")
                if not username:
                    print("Error: username not provided")
                    continue
                password = getpass()
                if not password:
                    print("Error: password not provided")
                    continue
                access_token = Client.get_access_token(username, password)
                # store access token
                with open("config/access_token.txt", 'w') as file:
                    file.write(access_token)
        self.client = Client(access_token)

    # send a request for payment to a Venmo account
    def request_donation(self, username, amount):
        user = self.client.user.get_user_by_username(username)
        if not user:
            return "Unable to find user"
        self.client.payment.request_money(amount, "Veteran Donation", user.id)
        transactions = self.client.user.get_user_transactions(user.id)
        return None

class Email:
    email = None
    password = None

    smtp = None
    port = None

    def __init__(self):
        self.read_email()

    # setups up email notifications
    def setup_email(self):
        notify = input("Would you like to recieve email notifications? (y/n): ")
        if notify == "y":
            print("Provide an email to send notifcations from")
            email = input("email: ")
            if not email:
                return "Error: No email provided"
            self.address = email.rstrip()
            password = getpass()
            if not password:
                return "Error: No password was provided for the email"
            self.password = password.rstrip()
            smtp = input("What smtp server should emails go through? (ex. smtp.gmail.com for a gmail account): ")
            if not smtp:
                return "Error: No smtp server was provided"
            self.smtp = smtp.rstrip()
            port = input("What port does the smtp server use? (uses 587 if nothing is provided): ")
            if not port:
                port = 587
            try:
                port = int(port)
            except ValueError:
                return "Error: Port wasn't a number"
            self.port = port
            self.write_email()
            print("Restart server!")
            exit()

    # reads the email configuration file or setups up a new one
    def read_email(self):
        if not os.path.isfile("config/email.txt"):
            return self.setup_email()
        with open("config/email.txt", 'r') as file:
            self.email = file.readline().rstrip()
            self.password = file.readline().rstrip()
            self.smtp = file.readline().rstrip()
            self.port = file.readline().rstrip()
            if not self.email or not self.password:
                print("email.txt is not properly formatted")
                setup = input("Would you like to set it up again? (y/n): ")
                if setup == 'n':
                    remove = input("Would you like to remove the pre-existing email configuration? (y/n): ")
                    if remove == 'y':
                        os.remove("email.txt")
                    return None, None
                    exit()
                elif setup == 'y':
                    return self.setup_email()

    # writes email configurations to a file
    def write_email(self):
        if os.path.isfile("config/email.txt"):
            overwrite = input("Are you sure that you want to overwrite the current configuration? (y/n): ")
            if overwrite == 'n':
                return
            elif overwrite == 'y':
                os.remove("config/email.txt")
        with open("config/email.txt", 'w') as file:
            file.write(f"{self.address}\n{self.password}\n{self.smtp}\n{self.port}")

    # sends a message to an email address
    def send_email(self, email, message):
        context = ssl.create_default_context()
        with smtplib.SMTP(self.smtp, self.port) as smtp:
            smtp.starttls()
            smtp.login(self.email, self.password)
            smtp.sendmail(self.email, email, message)

    # sends an email to a donater when their transaction completes
    def notify(self):
        notified_donations = []
        while True:
            ids = []
            charges = payments.client.payment.get_charge_payments()
            for charge in charges:
                ids.append(charge.id)
                # donator's email
                email = charge._json["target"]["email"]
                if charge.status == PaymentStatus.SETTLED:
                    # don't resend notifications when the donator was already notified
                    if charge.id in charges:
                        continue
                    else:
                        charges.append(charge.id)
                    # send an email to the donater if the Venmo account has one
                    if email:
                        self.notify_donater(charge.actor.email, charge.amount)
                    # send an email to the admin
                    self.notify_admin(charge.actor.username, charge.amount)
                    return
            for id in ids:
                if id not in notified_donations:
                    notified_donations.remove(id)
            time.sleep(5) # check for a changed status every 30 seconds


    # sends an email to a donater's email address
    def notify_donator(self, email, amount):
        message = MIMEMultipart()
        message["From"] = self.email
        message["To"] = email
        message["Subject"] = "Project Headspace and Timing"
        message.attach(MIMEText(f"Thank you for donating ${amount} to Veterans in need!", "plain"))
        self.send_email(email, message.as_string())

    # emails the admin that a transaction completed
    def notify_admin(self, username, amount):
        message = MIMEMultipart()
        message["From"] = self.email
        message["To"] = self.email
        message["Subject"] = "Donation: Completed"
        message.attach(MIMEText(f"A donation of ${amount} was completed from {username}", "plain"))
        self.send_email(self.email, message.as_string())

payments = Venmo()
email = Email()
notifications = threading.Thread(target = email.notify)
notifications.start()
flask = Flask(__name__)
flask.secret_key = "492050b4de974f459637303458f5ff09" # random string for cookies

@flask.route("/donate", methods=("GET", "POST"))
def donate():
    # read submitted form
    if request.method == "POST":
        error = None
        username = request.form["username"]
        if not username:
            flash("No username was specified!")
            return render_template("donate.html")
        amount = request.form["amount"]
        if not amount:
            flash("No amount was specified!")
            return render_template("donate.html")
        try:
            amount = float(amount)
        except ValueError:
            flash("Specified amount must be a number!")
            return render_template("donate.html")
        if payments.request_donation(username, amount):
            flash("Couldn't find a Venmo account with that username!")
            return render_template("donate.html")
        flash("Thank you for donating!")
    # otherwise display the donate webpage
    return render_template("donate.html")

print("Server started!")
