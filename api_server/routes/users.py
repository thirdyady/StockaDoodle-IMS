from flask import Blueprint, request, jsonify
from models.user import User
from core.user_manager import UserManager, UserError
from core.mfa_service import MFAService
from core.activity_logger import ActivityLogger
from utils import get_image_binary

bp = Blueprint('users', __name__)


# ----------------------------------------------------------------------
# GET /api/v1/users → list all users
# role: String (optional) - filter by role
# ----------------------------------------------------------------------
@bp.route('', methods=['GET'])
def list_users():
    """List all users with optional role filtering"""
    role = request.args.get('role')
    include_image = request.args.get('include_image') == 'true'
    
    users = UserManager.get_all_users(role=role)
    
    return jsonify({
        'total': len(users),
        'users': [u.to_dict(include_image) for u in users]
    }), 200


# ----------------------------------------------------------------------
# GET /api/v1/users/<id> → get single user
# ----------------------------------------------------------------------
@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get single user by ID"""
    user = UserManager.get_user(user_id)
    if not user:
        return jsonify({"errors": ["User not found"]}), 404
    
    include_image = request.args.get('include_image') == 'true'
    return jsonify(user.to_dict(include_image)), 200


# ----------------------------------------------------------------------
# POST /api/v1/users → create new user
# username: String (required, unique)
# password: String (required)
# full_name: String (required)
# role: String (optional, default="staff")
# user_image: File (optional, multipart/form-data)
# ----------------------------------------------------------------------
@bp.route('', methods=['POST'])
def create_user():
    """Create new user account"""
    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})
    
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    email = data.get('email')
    
    if not username or not password or not full_name or not email:
        return jsonify({"errors": ["username, password, and full_name are required"]}), 400
    
    role = data.get('role', 'staff')
    
    # Handle image
    user_image = get_image_binary()
    
    try:
        user = UserManager.create_user(
            username=username,
            password=password,
            full_name=full_name,
            role=role,
            email=email,
            user_image=user_image
        )
        
        # Log activity
        ActivityLogger.log_api_activity(
            method='POST',
            target_entity='user',
            user_id=user.id,
            details=f"Created user: {username} (role: {role})"
        )
        
        return jsonify(user.to_dict(include_image=True)), 201
        
    except UserError as e:
        return jsonify({"errors": [str(e)]}), 400


# ----------------------------------------------------------------------
# PUT /api/v1/users/<id> → replace user
# username: String (required)
# full_name: String (required)
# role: String (required)
# password: String (optional, will update if provided)
# user_image: File (optional)
# ----------------------------------------------------------------------
@bp.route('/<int:user_id>', methods=['PUT'])
def replace_user(user_id):
    """Replace entire user record"""
    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})
    
    username = data.get('username')
    full_name = data.get('full_name')
    role = data.get('role')
    email = data.get('email')
    
    if not username or not full_name or not role:
        return jsonify({"errors": ["username, full_name, role, and email are required for PUT"]}), 400
    
    # Handle image
    user_image = get_image_binary()
    if user_image is not None:
        data['user_image'] = user_image
    
    try:
        user = UserManager.update_user(user_id, **data)
        
        # Log activity
        ActivityLogger.log_api_activity(
            method='PUT',
            target_entity='user',
            user_id=user_id,
            details=f"Replaced user: {username}"
        )
        
        return jsonify(user.to_dict(include_image=True)), 200
        
    except UserError as e:
        return jsonify({"errors": [str(e)]}), 400


# ----------------------------------------------------------------------
# PATCH /api/v1/users/<id> → update user
# username: String (optional)
# full_name: String (optional)
# role: String (optional)
# email: String (optional)
# password: String (optional)
# user_image: File (optional)
# ----------------------------------------------------------------------
@bp.route('/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    """Partially update user"""
    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})
    
    # Handle image
    user_image = get_image_binary()
    if user_image is not None:
        data['user_image'] = user_image
    
    try:
        user = UserManager.update_user(user_id, **data)
        
        # Log activity
        changes = [k for k in data.keys() if k != 'password']
        ActivityLogger.log_api_activity(
            method='PATCH',
            target_entity='user',
            user_id=user_id,
            details=f"Updated user {user.username}: {', '.join(changes)}"
        )
        
        return jsonify(user.to_dict(include_image=True)), 200
        
    except UserError as e:
        return jsonify({"errors": [str(e)]}), 400


# ----------------------------------------------------------------------
# DELETE /api/v1/users/<id> → delete user
# ----------------------------------------------------------------------
@bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user account"""
    try:
        user = UserManager.get_user(user_id)
        if not user:
            return jsonify({"errors": ["User not found"]}), 404
        
        username = user.username
        UserManager.delete_user(user_id)
        
        # Log activity
        ActivityLogger.log_api_activity(
            method='DELETE',
            target_entity='user',
            user_id=user_id,
            details=f"Deleted user: {username}"
        )
        
        return jsonify({
            "message": f"User '{username}' deleted successfully"
        }), 200
        
    except UserError as e:
        return jsonify({"errors": [str(e)]}), 400


# ----------------------------------------------------------------------
# POST /api/v1/users/auth/login → authenticate user
# username: String (required)
# password: String (required)
# ----------------------------------------------------------------------
@bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and initiate MFA if needed"""
    data = request.get_json() or {}
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"errors": ["username and password required"]}), 400
    
    user = UserManager.authenticate_user(username, password)
    if not user:
        return jsonify({"errors": ["Invalid credentials"]}), 401
    
    # Check if MFA required (admin/manager roles)
    if user.role in ['admin', 'manager']:
        return jsonify({
            "message": "MFA required",
            "mfa_required": True,
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "email": user.email
        }), 200
    
    # Log successful login
    ActivityLogger.log_api_activity(
        method='POST',
        target_entity='auth',
        user_id=user.id,
        source='API',
        details=f"User {username} logged in"
    )
    
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict()
    }), 200


# ----------------------------------------------------------------------
# POST /api/v1/users/auth/mfa/send → send MFA code
# username: String (required)
# email: String (required)
# ----------------------------------------------------------------------
@bp.route('/auth/mfa/send', methods=['POST'])
def send_mfa():
    """Send MFA code to user email"""
    data = request.get_json() or {}
    
    username = data.get('username')
    email = data.get('email')
    
    if not username:
        return jsonify({"errors": ["username"]}), 400
    
    user = UserManager.get_user_by_username(username)
    if not user:
        return jsonify({"errors": ["User not found"]}), 404
    
    try:
        MFAService.send_mfa_code(email, username)
        
        # Log activity
        ActivityLogger.log_api_activity(
            method='POST',
            target_entity='auth',
            user_id=user.id,
            details=f"MFA code sent to {username}"
        )
        
        return jsonify({
            "message": "MFA code sent",
            "expires_in_minutes": MFAService.MFA_CODE_EXPIRY_MINUTES
        }), 200
        
    except Exception as e:
        return jsonify({"errors": [str(e)]}), 500


# ----------------------------------------------------------------------
# POST /api/v1/users/auth/mfa/verify → verify MFA code
# username: String (required)
# code: String (required)
# ----------------------------------------------------------------------
@bp.route('/auth/mfa/verify', methods=['POST'])
def verify_mfa():
    """Verify MFA code"""
    data = request.get_json() or {}
    
    username = data.get('username')
    code = data.get('code')
    
    if not username or not code:
        return jsonify({"errors": ["username and code required"]}), 400
    
    if MFAService.verify_code(username, code):
        user = UserManager.get_user_by_username(username)
        
        # Log successful MFA verification
        if user:
            ActivityLogger.log_api_activity(
                method='POST',
                target_entity='auth',
                user_id=user.id,
                details=f"MFA verified for {username}"
            )
        
        return jsonify({
            "message": "MFA verified",
            "user": user.to_dict() if user else None
        }), 200
    else:
        return jsonify({"errors": ["Invalid or expired MFA code"]}), 401


# ----------------------------------------------------------------------
# POST /api/v1/users/<id>/change-password → change password
# old_password: String (required)
# new_password: String (required)
# ----------------------------------------------------------------------
@bp.route('/<int:user_id>/change-password', methods=['POST'])
def change_password(user_id):
    """Change user password with verification"""
    data = request.get_json() or {}
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({"errors": ["old_password and new_password required"]}), 400
    
    try:
        UserManager.change_password(user_id, old_password, new_password)
        
        # Log activity
        ActivityLogger.log_api_activity(
            method='POST',
            target_entity='user',
            user_id=user_id,
            details="Password changed"
        )
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except UserError as e:
        return jsonify({"errors": [str(e)]}), 400