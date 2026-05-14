from django.shortcuts import render, redirect  # To show HTML pages and redirect users
from django.contrib.auth.models import User, Group, Permission  # Django's built-in user, group, and permission models
from django.contrib.auth import authenticate, login, logout  # Functions to handle login and logout
from django.http import HttpResponseRedirect, HttpResponse  # For redirecting users or sending responses
from django.urls import reverse, reverse_lazy  # Helps get URLs by their names
from django.contrib.auth.decorators import login_required  # Makes sure only logged-in users can access pages
from datetime import datetime
import secrets  # For generating secure random tokens
from datetime import timedelta
from hashlib import sha1  # To hash tokens securely
from django.core.exceptions import ObjectDoesNotExist  # For handling cases when an object is not found

from .models import ResetToken  # Our custom model to store reset tokens

from django.core.mail import EmailMessage  # To send emails
from django.contrib.auth.hashers import make_password  # To hash passwords before saving

# This function handles user login
def login_user(request):
    # When the login form is submitted
    if request.method == 'POST':
        # Get username and password from the form
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the username and password match a user in the database
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # Log the user in and start their session

            # Set the session to expire on 30 Dec 2025 (so user stays logged in until then)
            exp_date = datetime(2025, 12, 30)
            now = datetime.now()
            expiry_seconds = int((exp_date - now).total_seconds())
            if expiry_seconds > 0:
                request.session.set_expiry(expiry_seconds)  # Set the expiry time for the session

            # Save some user info in the session (optional, but useful)
            request.session['user_id'] = user.id
            request.session['username'] = user.username

            # Redirect user to the welcome page after successful login
            return HttpResponseRedirect(reverse('authenticator:welcome'))
        else:
            # If login failed, reload login page with an error message
            return render(request, 'authenticator/login.html', {'error': 'Invalid credentials'})

    # If the user just opened the login page, show the login form
    return render(request, 'authenticator/login.html')


# This function handles user registration (signing up)
def register_user(request):
    if request.method == 'POST':
        # Get data from the form
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Password confirmation
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            return render(request, 'authenticator/register.html', {
                'error': 'Passwords do not match'
            })

        email = request.POST.get('email')

        # Create a new user in the database
        user = User.objects.create_user(username=username, password=password, email=email)

        role = request.POST.get('role')

        # Assign role and creates the group if missing
        if role == 'vendor':
            group, _ = Group.objects.get_or_create(name='Vendors')
        else:
            group, _ = Group.objects.get_or_create(name='Buyers')

        user.groups.add(group)

        # Try to give the user permission to view products (fallback)
        try:
            permission = Permission.objects.get(codename='view_products', content_type__app_label='store')
            user.user_permissions.add(permission)
        except Permission.DoesNotExist:
            pass  # Ignore if permission doesn't exist

        user.save()  # Save all changes to the database

        login(request, user)  # Log the new user in automatically

        # Redirect to welcome page after registration
        return redirect(reverse('authenticator:welcome'))

    # If user visits registration page, show the registration form
    return render(request, 'authenticator/register.html')


# Helper function to change a user's password securely
def change_user_password(username, new_password):
    user = User.objects.get(username=username)  # Find user by username

    user.set_password(new_password)  # Set the new password (hashed automatically)

    user.save()  # Save changes to the database


# Logs the user out and redirects to login page
def logout_user(request):
    if request.user is not None:
        logout(request)  # Log out the current user
        return HttpResponseRedirect(reverse('authenticator:login'))


# Only logged-in users can see the welcome page
@login_required(login_url=reverse_lazy('authenticator:login'))
def welcome(request):
    return render(request, 'authenticator/welcome.html')  # Show the welcome page


# # Creates the email object to send for password reset
def build_email(user, reset_url):
    subject = "Password Reset"
    user_email = user.email
    domain_email = "example@domain.com"  # The "from" email address for the email
    body = f"Hi {user.username},\nHere is your link to reset your password: \n{reset_url}"

    email = EmailMessage(subject, body, domain_email, [user_email])
    return email
#
#
# # Creates a secure reset URL with a token that expires in 5 minutes
def generate_reset_url(user):
    domain = "http://127.0.0.1:8000/"
    # app_name = "authenticator"  # Make sure this matches your app name in urls.py
    url = f"{domain}/reset/"

    token = secrets.token_urlsafe(16)  # Generate a random secure token

    expiry_date = datetime.now() + timedelta(minutes=5)  # Token expires in 5 minutes

    hashed_token = sha1(token.encode()).hexdigest()  # Hash the token to store securely

    # Save the hashed token and expiry date to the database
    ResetToken.objects.create(
        user=user,
        token=hashed_token,
        expiry_date=expiry_date
    )

    url += f"{token}/"  # Add the raw token (not hashed) to the URL for verification later
    print(url)
    print(token)
    print(hashed_token)
    return url


# Handles sending the password reset email after user submits their email
def send_password_reset(request):
    if request.method == 'POST':
        user_email = request.POST.get('email')
        try:
            user = User.objects.get(email=user_email)  # Find user by email
            reset_url = generate_reset_url(user)  # Generate reset link with token
            email = build_email(user, reset_url)  # Create the email message
            email.send()  # Send the email

            # Show a confirmation page that email was sent
            return render(request, 'authenticator/reset_email_sent.html', {
                'email': user_email
            })

        except ObjectDoesNotExist:
            # Even if no user found, still show confirmation (to avoid info leaks)
            return render(request, 'authenticator/reset_email_sent.html', {
                'email': user_email
            })

    # Show the form where user can enter their email
    return render(request, 'authenticator/request_password_reset.html')


# This view is called when user clicks the reset link in their email
def reset_user_password(request, token):
    hashed_token = sha1(token.encode()).hexdigest()  # Hash the token from URL

    try:
        user_token = ResetToken.objects.get(token=hashed_token)  # Look for token in DB

        # Check if the token expired
        if user_token.expiry_date.replace(tzinfo=None) < datetime.now():
            user_token.delete()  # Delete expired token
            return render(request, 'authenticator/password_reset_expired.html')  # Show expired token message

        # Save user ID and token in session to verify next step
        request.session['user_id'] = user_token.user.id
        request.session['reset_token'] = token

        # Show the password reset form
        return render(request, 'authenticator/password_reset.html', {'token': token})

    except ResetToken.DoesNotExist:
        # Token not found or already used
        return render(request, 'authenticator/password_reset_invalid.html')


# Handles the password reset form submission (when user enters new password)
def reset_password(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        token = request.session.get('reset_token')
        password = request.POST.get('password')
        password_conf = request.POST.get('password_conf')

        # Check if all required data is present
        if not all([user_id, token, password, password_conf]):
            print(token)
            print(password)
            return render(request, 'password_reset.html', {
                'error': 'Missing fields or session expired.',
                'token': token
            })

        # Check if passwords match
        if password != password_conf:
            return render(request, 'password_reset.html', {
                'error': 'Passwords do not match.',
                'token': token
            })

        try:
            user = User.objects.get(id=user_id)  # Find user by user_id
            hashed_token = sha1(token.encode()).hexdigest()
            reset_token = ResetToken.objects.get(token=hashed_token)

            # Check token expiry again (just to be sure)
            if reset_token.expiry_date.replace(tzinfo=None) < datetime.now():
                print("C")
                reset_token.delete()
                return render(request, 'password_reset_expired.html')

            # Update the user's password (hashed securely)
            user.password = make_password(password)
            user.save()

            # Delete the token and clear session info
            reset_token.delete()
            request.session.flush()

            print("D")
            # Redirect user to login page after successful password reset
            return HttpResponseRedirect(reverse('authenticator:login'))

        except (User.DoesNotExist, ResetToken.DoesNotExist):
            return render(request, 'password_reset_invalid.html')

    # If the page was accessed with GET or any other method, redirect to login page
    return HttpResponseRedirect(reverse('authenticator:login'))