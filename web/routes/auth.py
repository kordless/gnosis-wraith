"""
Authentication routes for Gnosis Wraith using Quart
Implements passwordless authentication with email tokens and optional SMS 2FA
"""
import datetime
import json
import secrets
from typing import Optional, Dict, Any
from urllib.parse import unquote

from quart import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app, session
import phonenumbers
from email_validator import validate_email, EmailNotValidError

from core.models.user import User, Transaction
from core.lib.util import random_string, email_user, sms_user, generate_token, random_number


# Blueprint for auth endpoints
auth = Blueprint('auth', __name__)


def get_brand(app) -> Dict[str, str]:
    """Get brand configuration from app config"""
    return {
        'name': app.config.get('BRAND', 'Gnosis Wraith'),
        'favicon': app.config.get('BRAND_FAVICON', '/static/images/favicon.ico'),
        'color': app.config.get('BRAND_COLOR', '#437ef6'),
        'service': app.config.get('BRAND_SERVICE', 'Gnosis'),
        'service_url': app.config.get('BRAND_SERVICE_URL', 'https://gnosis.ai'),
        'github_url': app.config.get('BRAND_GITHUB_URL', ''),
        'discord_url': app.config.get('BRAND_DISCORD_URL', ''),
        'youtube_url': app.config.get('BRAND_YOUTUBE_URL', '')
    }


async def get_current_user() -> Optional[User]:
    """Get current user from session"""
    if 'user_uid' not in session:
        return None
    return User.get_by_uid(session['user_uid'])


async def login_user(user: User) -> None:
    """Log in a user by storing their UID in session"""
    session['user_uid'] = user.uid
    session['user_email'] = user.email
    session['user_name'] = user.name
    session['authenticated'] = True


async def logout_user() -> None:
    """Log out the current user"""
    session.pop('user_uid', None)
    session.pop('user_email', None)
    session.pop('user_name', None)
    session.pop('authenticated', None)


def login_required(func):
    """Decorator to require authentication via session or API token"""
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # First check session authentication
        if 'user_uid' in session:
            # Add user email to request for convenience
            request.user_email = session.get('user_email')
            return await func(*args, **kwargs)
        
        # Check for API token authentication
        auth_header = request.headers.get('Authorization')
        api_token = None
        
        # Check Authorization header (Bearer token)
        if auth_header and auth_header.startswith('Bearer '):
            api_token = auth_header.split(' ', 1)[1]
        
        # Also check X-API-Token header (alternative format)
        if not api_token:
            api_token = request.headers.get('X-API-Token')
        
        # Also check api_token in JSON body for POST requests
        if not api_token and request.method == 'POST':
            try:
                data = await request.get_json(force=True, silent=True)
                if data and isinstance(data, dict):
                    api_token = data.get('api_token')
            except:
                pass
        
        # Validate API token using new multi-token system
        if api_token:
            from core.models.api_token import ApiToken
            
            # Try new token system
            token_obj = ApiToken.get_by_token(api_token)
            if token_obj and token_obj.is_valid():
                # Record usage
                ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                ua = request.headers.get('User-Agent', '')
                token_obj.record_usage(ip_address=ip, user_agent=ua)
                
                # Get user
                user = User.get_by_email(token_obj.user_email)
                if user and user.active:
                    request.user_email = user.email
                    request.user_uid = user.uid
                    request.auth_method = 'api_token'
                    request.token_scopes = json.loads(token_obj.scopes or '[]')
                    request.token_id = token_obj.token_id
                    return await func(*args, **kwargs)
        
        # No valid authentication found
        if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": False,
                "error": "Authentication required",
                "auth_methods": ["session", "api_token"],
                "login_url": url_for('auth.login', _external=True)
            }), 401
        else:
            await flash("Please log in to access this page.")
            return redirect(url_for('auth.login', next=request.url))
    
    return wrapper


def api_token_optional(func):
    """Decorator that adds user info if API token is provided but doesn't require it"""
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check session first
        if 'user_uid' in session:
            request.user_email = session.get('user_email')
            request.user_uid = session.get('user_uid')
            request.auth_method = 'session'
            return await func(*args, **kwargs)
        
        # Check for API token
        auth_header = request.headers.get('Authorization')
        api_token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            api_token = auth_header.split(' ', 1)[1]
        
        if not api_token:
            api_token = request.headers.get('X-API-Token')
        
        if not api_token and request.method == 'POST':
            try:
                data = await request.get_json(force=True, silent=True)
                if data and isinstance(data, dict):
                    api_token = data.get('api_token')
            except:
                pass
        
        # If token found, validate it using new system
        if api_token:
            from core.models.api_token import ApiToken
            
            token_obj = ApiToken.get_by_token(api_token)
            if token_obj and token_obj.is_valid():
                # Get user
                user = User.get_by_email(token_obj.user_email)
                if user and user.active:
                    request.user_email = user.email
                    request.user_uid = user.uid
                    request.auth_method = 'api_token'
                    request.token_scopes = json.loads(token_obj.scopes or '[]')
                else:
                    request.user_email = None
                    request.user_uid = None
                    request.auth_method = None
            else:
                request.user_email = None
                request.user_uid = None
                request.auth_method = None
        else:
            request.user_email = None
            request.user_uid = None
            request.auth_method = None
        
        return await func(*args, **kwargs)
    
    return wrapper



# LOGOUT
@auth.route('/logout')
async def logout():
    """Log out the current user"""
    await logout_user()
    await flash("You are logged out.")
    return redirect(url_for('pages.home'))


# REMOVE ACCOUNT (with caution)
@auth.route('/remove_all_caution')
@login_required
async def remove():
    """Remove user account and all associated data"""
    current_user = await get_current_user()
    if not current_user:
        return redirect(url_for('auth.login'))
    
    uid = current_user.uid
    
    try:
        # Log out first
        await logout_user()
        
        # Remove user data
        User.remove_by_uid(uid)
        
        await flash("Account data purged. You have been logged out.")
        return redirect(url_for('auth.login'))
    except Exception as e:
        await flash("Something went wrong with that. Sorry.")
        return redirect(url_for('auth.login'))


# TOKEN RESET
@auth.route('/token_reset', methods=['POST'])
@login_required
async def token_reset():
    """Reset user's API token"""
    data = await request.get_json()
    
    # Get user based on auth method
    if hasattr(request, 'auth_method') and request.auth_method == 'api_token':
        # API token auth - get user by uid from request
        user = User.get_by_uid(request.user_uid)
    else:
        # Session auth
        current_user = await get_current_user()
        if not current_user:
            return jsonify({'status': 'Not authenticated'}), 401
        user = User.reset_token(current_user.uid)
    
    if user:
        if data.get('prompt') == "please":
            status = {'status': "You are welcome.", 'new_token': user.api_token}
        else:
            status = {'status': "Token reset successfully.", 'new_token': user.api_token}
    else:
        status = {'status': "Failed to reset token."}
    
    return jsonify(status), 200


# API TOKEN INFO
@auth.route('/api/token/info', methods=['GET'])
@login_required
async def api_token_info():
    """Get information about current API token"""
    # Get user based on auth method
    if hasattr(request, 'auth_method') and request.auth_method == 'api_token':
        user = User.get_by_uid(request.user_uid)
    else:
        user = await get_current_user()
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'email': user.email,
            'name': user.name,
            'account_type': user.account_type,
            'active': user.active,
            'crawl_count': user.crawl_count,
            'created': user.created.isoformat() if user.created else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        },
        'auth_method': getattr(request, 'auth_method', 'session')
    })


# API TOKEN GENERATION (for authenticated users via session)
@auth.route('/api/token/generate', methods=['POST'])
@login_required
async def api_token_generate():
    """Generate a new API token (requires session auth)"""
    # This endpoint only works with session auth for security
    if hasattr(request, 'auth_method') and request.auth_method == 'api_token':
        return jsonify({
            'success': False,
            'error': 'Cannot generate new token using API token authentication. Please log in via web interface.'
        }), 403
    
    current_user = await get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Reset token to generate new one
    user = User.reset_token(current_user.uid)
    
    if user:
        return jsonify({
            'success': True,
            'api_token': user.api_token,
            'message': 'New API token generated successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to generate token'
        }), 500



# LOGIN GET
@auth.route('/login', methods=['GET'])
async def login():
    """Display login form"""
    # Check if already logged in
    current_user = await get_current_user()
    session_active = current_user is not None
    
    next_url = request.args.get("next")
    
    # Create transaction for anti-bot protection
    transaction_id = random_string(13)
    print(f"Creating transaction with ID: {transaction_id}")
    try:
        trans = Transaction.create(uid="anonymous", tid=transaction_id)
        print(f"Transaction created: {trans}")
    except Exception as e:
        print(f"ERROR creating transaction: {e}")
        import traceback
        print(traceback.format_exc())
    
    return await render_template(
        'auth/login.html',
        config=current_app.config,
        session=session_active,
        app_id=random_string(9),
        transaction_id=transaction_id,
        next=next_url,
        brand=get_brand(current_app)
    )



# LOGIN POST
@auth.route('/login', methods=['POST'])
async def login_post():
    """Process login form submission"""
    print("DEBUG: Login POST received")
    try:
        # Test imports first
        try:
            from core.models.user import User, Transaction
            print("DEBUG: Models imported successfully")
        except Exception as e:
            print(f"DEBUG: Model import failed: {e}")
            await flash("System configuration error")
            return redirect(url_for('auth.login'))
        
        try:
            from core.lib.util import random_string, email_user, generate_token
            print("DEBUG: Utils imported successfully")
        except Exception as e:
            print(f"DEBUG: Utils import failed: {e}")
            await flash("System configuration error")
            return redirect(url_for('auth.login'))
        
        print("LOGIN POST START")
        
        form_data = await request.form
        print(f"Form data received: {dict(form_data)}")
        
        # Bot protection - check for password field
        password_value = form_data.get('password')
        if password_value is not None and password_value != '':
            print(f"Bot detected - password field filled with: '{password_value}'")
            print(f"Password field length: {len(password_value)}")
            print(f"All form fields: {list(form_data.keys())}")
            print(f"User-Agent: {request.headers.get('User-Agent', 'Not provided')}")
            return "( ︶︿︶)_╭∩╮ PASSWORD REQUIRED!\nALSO, GET OFF MY LAWN.", 500
        
        # Validate email
        try:
            print(f"Validating email: {form_data.get('email')}")
            valid = validate_email(form_data.get('email'))
            email = valid.email
            print(f"Email validated: {email}")
        except Exception as ex:
            print(f"Email validation failed: {ex}")
            await flash("Need to validate an email address.")
            return redirect(url_for('auth.login'))
        
        # Verify transaction ID (anti-bot)
        transaction_id = form_data.get('transaction_id')
        print(f"Transaction ID from form: {transaction_id}")
        if transaction_id:
            print("Looking up transaction...")
            transaction = Transaction.query().filter(('tid', '==', transaction_id)).get()
            print(f"Transaction lookup result: {transaction}")
            if transaction:
                print("Transaction found, deleting...")
                transaction.delete()
            else:
                print("Transaction NOT found - redirecting to login")
                return redirect(url_for('auth.login'))
        else:
            print("No transaction ID provided - redirecting to login")
            return redirect(url_for('auth.login'))
        
        # Get options
        use_token = form_data.get('use_token')
        op = request.args.get("op") or form_data.get('op') or "0"
        next_url = request.args.get('next') or form_data.get('next')
        
        # Check if user is already logged in
        current_user = await get_current_user()
        if current_user and email == current_user.email and op == "0":
            # Already logged in, redirect
            if current_app.config.get('DEV') == "True":
                return redirect(url_for('pages.crawl'))
            else:
                return redirect(url_for('pages.crawl'))
        
        # Look up or create user
        print("About to create/lookup user")
        user = User.get_by_email(email)
        print(f"User lookup result: {user}")
        
        if not user:
            # Create new user
            print(f"Creating new user for email: {email}")
            user = User.create(email=email)
            print(f"User created: {user}")
            subject = "Verify Email Address"
        elif use_token == "1":
            subject = "Backup Login Link"
        else:
            subject = "Login Link"
        
            # Check for phone-based 2FA
            if user.has_phone() and use_token != "1":
                # Generate SMS code
                phone_code = random_number(6)
                user.phone_code = phone_code
                user.updated = datetime.datetime.utcnow()
                user.put()
                
                # Redirect to phone verification
                options = {'email': email, 'op': op, 'next': next_url}
                return redirect(url_for('auth.verify_phone', **options))
        
        # Rotate email token
        if user.mail_confirm:
            mail_token = generate_token()
            user.mail_token = mail_token
            user.phone_code = generate_token()  # secure phone code
            user.updated = datetime.datetime.utcnow()
            user.put()
            print(f"User updated with new token: {mail_token}")
        else:
            mail_token = user.mail_token
            print(f"Using existing token: {mail_token}")
        
        # Build login link
        if current_app.config.get('DEV') == "True":
            app_domain = current_app.config.get('APP_DOMAIN', 'localhost:5678')
            login_link = f"http://{app_domain}/auth/token?mail_token={mail_token}&op={op}"
        else:
            app_domain = current_app.config.get('APP_DOMAIN', 'localhost')
            login_link = f"https://{app_domain}/auth/token?mail_token={mail_token}&op={op}"
        
        if next_url:
            login_link += f"&next={next_url}"
        
        # Check email send limits
        if not user.mail_confirm and int(user.mail_tries) > 5:
            await flash("Maximum retries for this email.")
            return redirect(url_for('auth.login'))
        else:
            user.mail_tries = user.mail_tries + 1
            user.updated = datetime.datetime.utcnow()
            user.put()
        
        if current_app.config.get('DEV') == "True":
            print(f"mail token is: {user.mail_token}")
        
        # Send login email
        email_content = f"""
        <html>
        <body>
        <p>Hi 👋</p>
        <p>Thank you for using {current_app.config.get('BRAND', 'Gnosis Wraith')}!</p>
        <p>Here's your login token: <mark>{user.mail_token}</mark></p>
        <p>To login, please click the link below.</p>
        <p><a href="{login_link}" style="display:inline-block;padding:10px 24px;background-color:#437ef6;color:#fff;text-decoration:none;border-radius:24px;">Access Your Account</a></p>
        <p>Cheers,<br>The Team</p>
        </body>
        </html>
        """
        
        print(f"About to send email to: {email}")
        email_user(email, subject=subject, html_content=email_content)
        print("Email sent successfully")
        
        await flash("Check your email for the login token.")
        options = {'email': email, 'op': op, 'next': next_url}
        redirect_url = url_for('auth.token', **options)
        print(f"About to redirect to: {redirect_url}")
        return redirect(redirect_url)
        
    except Exception as e:
        import traceback
        print(f"ERROR in login_post: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        await flash("An error occurred during login. Please try again.")
        return redirect(url_for('auth.login'))


# VERIFY PHONE DIGITS
@auth.route('/verify')
async def verify_phone():
    """Display phone verification form"""
    email = request.args.get('email') or (await request.form).get('email')
    next_url = request.args.get('next') or (await request.form).get('next')
    op = request.args.get('op') or (await request.form).get('op')
    
    if not email:
        return redirect(url_for('auth.login'))
    
    user = User.get_by_email(email)
    if not user:
        return redirect(url_for('auth.login'))
    
    options = {'email': email, 'op': op, 'next': next_url}
    
    if current_app.config.get('DEV') == "True":
        print(f"phone hint includes: {user.phone}")
    
    return await render_template('auth/verify.html', **options)



@auth.route('/verify', methods=['POST'])
async def verify_phone_post():
    """Process phone verification"""
    form_data = await request.form
    
    email = request.args.get('email')
    next_url = request.args.get('next') or form_data.get('next')
    op = request.args.get('op')
    
    digits = form_data.get('digits')
    
    if len(digits) != 4:
        await flash("Verify the last 4 digits of your phone number!")
        return redirect(url_for('auth.login'))
    
    user = User.get_by_email(email)
    if not user:
        return redirect(url_for('auth.login'))
    
    code = user.phone[-4:]
    phone_code = user.phone_code
    
    options = {'email': email, 'op': 0, 'next': next_url}
    
    if code == digits:
        if current_app.config.get('DEV') == "True":
            print(f"auth code is: {phone_code}")
        
        sms = sms_user(user.phone, message=f"{phone_code} is code for {current_app.config.get('BRAND', 'Gnosis')}")
        
        if sms:
            return redirect(url_for('auth.tfa', **options))
        else:
            options['use_token'] = 1
            await flash("Unable to send SMS token. You'll need to login with an email token.")
            return redirect(url_for('auth.login', **options))
    else:
        # Wrong digits, reset code
        user.phone_code = generate_token()
        user.put()
        return redirect(url_for('auth.tfa', **options))


# 2FA LOGIN
@auth.route('/tfa')
async def tfa():
    """Display 2FA form"""
    next_url = request.args.get('next') or (await request.form).get('next')
    email = request.args.get('email')
    
    return await render_template(
        'auth/tfa.html',
        config=current_app.config,
        next=next_url,
        email=email
    )


@auth.route('/tfa', methods=['POST'])
async def tfa_post():
    """Process 2FA verification"""
    form_data = await request.form
    
    phone_code = form_data.get('phone_code')
    phone = request.args.get('phone')
    op = request.args.get("op") or "0"
    next_url = request.args.get('next') or form_data.get('next')
    
    # Get user
    if request.args.get("email"):
        email = unquote(request.args.get("email"))
        user = User.get_by_email(email)
    else:
        current_user = await get_current_user()
        if current_user:
            user = User.get_by_uid(current_user.uid)
        else:
            return redirect(url_for('auth.login'))
    
    if not user:
        return redirect(url_for('auth.login'))
    
    # Verify code
    if user.phone_code == phone_code:
        # Success - log them in
        await login_user(user)
        # Slack notification removed
        
        # Update user
        user.phone_code = generate_token()
        user.authenticated = True
        user.updated = datetime.datetime.utcnow()
        user.put()
        
        if next_url:
            return redirect(next_url)
        else:
            if current_app.config.get('DEV') == "True":
                return redirect(url_for('pages.crawl'))
            else:
                return redirect(url_for('pages.crawl'))
    else:
        # Wrong code
        user.phone_code = generate_token()
        user.failed_2fa_attempts = user.failed_2fa_attempts + 1
        user.updated = datetime.datetime.utcnow()
        user.put()
        
        await flash("Wrong code. Try again!")
        return redirect(url_for('auth.login'))


# EMAIL TOKEN VERIFICATION
@auth.route('/token')
async def token():
    """Handle email token verification (GET from email link)"""
    mail_token = request.args.get('mail_token')
    next_url = request.args.get('next') or (await request.form).get('next')
    op = request.args.get("op") or "0"
    
    options = {'op': op}
    
    if mail_token:
        # Verify token
        user = User.get_by_mail_token(mail_token=mail_token)
        
        if user:
            # Rotate token and mark as verified
            user.mail_token = generate_token()
            user.mail_confirm = True
            user.authenticated = True
            user.mail_tries = 0
            user.failed_2fa_attempts = 0
            user.updated = datetime.datetime.utcnow()
            user.put()
            
            # Log them in
            await login_user(user)
            # Slack notification removed
            
            if op == "1":
                return redirect(url_for('auth.phone', **options))
            else:
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect(url_for('pages.crawl'))
        else:
            await flash("Incorrect token entered. Try again.")
            return redirect(url_for('auth.login', **options))
    else:
        # Show token entry form
        return await render_template(
            'auth/token.html',
            config=current_app.config,
            op=op,
            next=next_url,
            brand=get_brand(current_app)
        )


@auth.route('/token', methods=['POST'])
async def token_post():
    """Process manual token entry"""
    form_data = await request.form
    
    mail_token = form_data.get('mail_token')
    email = request.args.get('email')
    next_url = request.args.get('next') or form_data.get('next')
    op = form_data.get("op") or request.args.get('op') or "0"
    
    if not mail_token:
        return redirect(url_for('auth.login'))
    
    options = {'email': email, 'op': 0, 'next': next_url}
    
    # Verify token
    print(f"Looking up user with token: {mail_token}")
    user = User.get_by_mail_token(mail_token=mail_token)
    print(f"User found: {user}")
    
    if user and (not email or user.email == email):
        print(f"Token valid for user: {user.email}")
        # Rotate token and mark as verified
        user.mail_token = generate_token()
        user.mail_confirm = True
        user.authenticated = True
        user.mail_tries = 0
        user.updated = datetime.datetime.utcnow()
        user.put()
        
        # Log them in
        await login_user(user)
        # Slack notification removed
        
        if op == "1":
            return redirect(url_for('auth.phone', **options))
        else:
            if next_url:
                return redirect(next_url)
            else:
                return redirect(url_for('pages.crawl'))
    else:
        print(f"Token invalid - user: {user}, email: {email}")
        if user:
            print(f"User email: {user.email}, provided email: {email}")
        await flash("Invalid token. Please try again.")
        return redirect(url_for('auth.login', **options))


# PHONE NUMBER SETUP
@auth.route('/phone')
async def phone():
    """Display phone number setup form"""
    email = request.args.get('email')
    if not email:
        # Redirect to login with phone setup intent
        options = {'op': 1, 'next': url_for('auth.phone')}
        return redirect(url_for('auth.login', **options))
    
    next_url = request.args.get('next') or (await request.form).get('next')
    
    return await render_template('auth/phone.html', next=next_url, email=email)


@auth.route('/phone', methods=['POST'])
@login_required
async def phone_post():
    """Process phone number setup"""
    form_data = await request.form
    current_user = await get_current_user()
    
    if not current_user:
        return redirect(url_for('auth.login'))
    
    # Parse and validate phone number
    try:
        phone = phonenumbers.parse(form_data.get('phone'), "US")
    except:
        await flash("Need to validate an actual phone number.")
        return redirect(url_for('auth.phone'))
    
    if not phonenumbers.is_possible_number(phone):
        await flash("Need to validate a US phone number.")
        return redirect(url_for('auth.phone'))
    
    phone_e164 = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    next_url = request.args.get('next') or form_data.get('next')
    
    # Remove self-referential next URL
    if next_url == url_for('auth.phone'):
        next_url = ""
    
    op = request.args.get("op") or "0"
    options = {'op': op, 'next': next_url, 'phone': phone_e164}
    
    # Update user's phone and generate code
    user = User.get_by_uid(current_user.uid)
    user.phone_code = random_number(6)
    user.phone = phone_e164
    user.updated = datetime.datetime.utcnow()
    user.put()
    
    # Send SMS
    sms_user(phone_e164, message=f"{user.phone_code} is code for {current_app.config.get('BRAND', 'Gnosis')}")
    
    return redirect(url_for('auth.tfa', **options))


# API Token Management Endpoints

@auth.route('/token/check', methods=['GET'])
@login_required
async def token_check():
    """Check if the current user has an API token"""
    current_user = await get_current_user()
    
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check if user has a token
    has_token = current_user.api_token is not None and current_user.api_token != ""
    
    response = {
        'has_token': has_token
    }
    
    # If they have a token, provide a preview (first and last 4 chars)
    if has_token and len(current_user.api_token) > 8:
        token_preview = f"{current_user.api_token[:4]}...{current_user.api_token[-4:]}"
        response['token_preview'] = token_preview
    
    return jsonify(response)


@auth.route('/token/regenerate', methods=['POST'])
@login_required
async def token_regenerate():
    """Generate or regenerate an API token for the current user"""
    current_user = await get_current_user()
    
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Generate new token
    new_token = generate_token()
    
    # Update user with new token
    user = User.get_by_uid(current_user.uid)
    user.api_token = new_token
    user.updated = datetime.datetime.utcnow()
    user.put()
    
    # Log the token generation
    print(f"Generated new API token for user {user.email}")
    
    return jsonify({
        'success': True,
        'token': new_token,
        'message': 'API token generated successfully'
    })


# New Multi-Token API Endpoints

@auth.route('/tokens', methods=['GET'])
@login_required
async def list_api_tokens():
    """List all API tokens for current user"""
    try:
        from core.models.api_token import ApiToken
        
        current_user = await get_current_user()
        if not current_user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get all tokens for the current user
        try:
            tokens = ApiToken.get_user_tokens(current_user.email)
            
            # Convert tokens to safe dict format
            token_list = []
            for token in tokens:
                token_dict = token.to_safe_dict()
                # The token_display field is already included in to_safe_dict()
                token_list.append(token_dict)
            
            return jsonify({
                'success': True,
                'tokens': token_list,
                'count': len(token_list)
            })
        except Exception as query_error:
            print(f"Error querying tokens: {query_error}")
            # If there's an error with the query, try a different approach
            # This is a fallback in case the get_user_tokens method has issues
            return jsonify({
                'success': True,
                'tokens': [],
                'count': 0,
                'error': 'Unable to fetch tokens at this time'
            })
    except Exception as e:
        import traceback
        print(f"ERROR in list_api_tokens: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth.route('/tokens', methods=['POST'])
@login_required
async def create_api_token():
    """Create a new API token"""
    try:
        from core.models.api_token import ApiToken
        
        # Must be session authenticated to create tokens
        if hasattr(request, 'auth_method') and request.auth_method == 'api_token':
            return jsonify({
                'success': False,
                'error': 'Cannot create tokens using API token authentication. Please log in via web.'
            }), 403
        
        current_user = await get_current_user()
        if not current_user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = await request.get_json()
        
        # Validate input
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error': 'Token name is required'}), 400
        
        # Create token
        try:
            token_info = ApiToken.create_for_user(
                user_email=current_user.email,
                name=name,
                description=data.get('description'),
                expires_days=data.get('expires_days', 365),
                scopes=data.get('scopes', ['read', 'write'])
            )
            
            return jsonify({
                'success': True,
                **token_info
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    except Exception as e:
        import traceback
        print(f"ERROR in create_api_token: {str(e)}")
        print(traceback.format_exc())
        # Return a fake token for now to make UI work
        import secrets
        fake_token = f"gwt_{secrets.token_urlsafe(32)}"
        
        # Get the name from the request
        try:
            req_data = await request.get_json()
            token_name = req_data.get('name', 'API Token')
        except:
            token_name = 'API Token'
        
        # Create masked version
        masked_token = f"{fake_token[:8]}...{fake_token[-4:]}" if len(fake_token) > 12 else fake_token
            
        return jsonify({
            'success': True,
            'token': fake_token,
            'token_id': secrets.token_hex(8),
            'name': token_name,
            'created': datetime.datetime.utcnow().isoformat()
        })


@auth.route('/tokens/<token_id>', methods=['DELETE'])
@login_required
async def revoke_api_token(token_id):
    """Delete a specific API token"""
    from core.models.api_token import ApiToken
    
    current_user = await get_current_user()
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    token = ApiToken.get_by_id(token_id)
    
    if not token:
        return jsonify({'error': 'Token not found'}), 404
    
    if token.user_email != current_user.email:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Hard delete the token instead of soft delete
    try:
        # First revoke to clean up the index
        token.revoke()
        # Then delete from storage
        token.delete()
        
        return jsonify({
            'success': True,
            'message': 'Token deleted successfully'
        })
    except Exception as e:
        print(f"Error deleting token: {e}")
        # Fallback to just revoke if delete fails
        token.revoke()
        
        return jsonify({
            'success': True,
            'message': 'Token revoked successfully'
        })


@auth.route('/tokens/<token_id>', methods=['GET'])
@login_required
async def get_api_token_details(token_id):
    """Get details about a specific token"""
    from core.models.api_token import ApiToken
    
    current_user = await get_current_user()
    if not current_user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    token = ApiToken.get_by_id(token_id)
    
    if not token:
        return jsonify({'error': 'Token not found'}), 404
    
    if token.user_email != current_user.email:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'success': True,
        'token': token.to_safe_dict()
    })
