from extensions import db
from models.user import User
from models.retailer_metrics import RetailerMetrics
from werkzeug.security import generate_password_hash


class UserError(Exception):
    """Custom exception for user-related issues."""
    pass


class UserManager:
    """
    Handles user authentication, authorization, and CRUD operations.
    Manages role-based access control (Admin, Manager, Retailer).
    """

    @staticmethod
    def authenticate_user(username, password):
        """
        Authenticate a user by username and password.
        
        Args:
            username (str): Username
            password (str): Plain text password
            
        Returns:
            User: User object if authentication successful, None otherwise
        """
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return None
        
        if user.check_password(password):
            return user
        
        return None

    @staticmethod
    def create_user(username, password, full_name, role="staff", user_image=None):
        """
        Create a new user account.
        
        Args:
            username (str): Unique username
            password (str): Plain text password (will be hashed)
            full_name (str): User's full name
            role (str): User role (admin, manager, retailer/staff)
            user_image (bytes, optional): Profile picture
            
        Returns:
            User: Created user object
            
        Raises:
            UserError: If username exists or validation fails
        """
        # Check if username already exists
        existing = User.query.filter_by(username=username).first()
        if existing:
            raise UserError(f"Username '{username}' already exists")

        # Validate role
        valid_roles = ['admin', 'manager', 'staff', 'retailer']
        if role not in valid_roles:
            raise UserError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")

        # Create user
        user = User(
            username=username,
            full_name=full_name,
            role=role,
            user_image=user_image
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # Get user ID

        # Create retailer metrics if role is retailer
        if role in ['retailer', 'staff']:
            metrics = RetailerMetrics(
                retailer_id=user.id,
                daily_quota=500.0,  # Default quota
                current_streak=0
            )
            db.session.add(metrics)

        db.session.commit()
        return user

    @staticmethod
    def get_user(user_id):
        """
        Get a user by ID.
        
        Args:
            user_id (int): User ID
            
        Returns:
            User: User object or None if not found
        """
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_username(username):
        """
        Get a user by username.
        
        Args:
            username (str): Username
            
        Returns:
            User: User object or None if not found
        """
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_all_users(role=None):
        """
        Get all users, optionally filtered by role.
        
        Args:
            role (str, optional): Filter by specific role
            
        Returns:
            list: List of User objects
        """
        query = User.query
        
        if role:
            query = query.filter_by(role=role)
        
        return query.order_by(User.full_name).all()

    @staticmethod
    def update_user(user_id, **kwargs):
        """
        Update user information.
        
        Args:
            user_id (int): User ID to update
            **kwargs: Fields to update (username, full_name, role, password, user_image)
            
        Returns:
            User: Updated user object
            
        Raises:
            UserError: If user not found or validation fails
        """
        user = User.query.get(user_id)
        if not user:
            raise UserError(f"User ID {user_id} not found")

        # Check username uniqueness if changing
        if 'username' in kwargs and kwargs['username'] != user.username:
            existing = User.query.filter_by(username=kwargs['username']).first()
            if existing:
                raise UserError(f"Username '{kwargs['username']}' already exists")

        # Update fields
        if 'username' in kwargs:
            user.username = kwargs['username']
        if 'full_name' in kwargs:
            user.full_name = kwargs['full_name']
        if 'role' in kwargs:
            valid_roles = ['admin', 'manager', 'staff', 'retailer']
            if kwargs['role'] not in valid_roles:
                raise UserError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
            user.role = kwargs['role']
        if 'password' in kwargs:
            user.set_password(kwargs['password'])
        if 'user_image' in kwargs:
            user.user_image = kwargs['user_image']

        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        """
        Delete a user account.
        
        Args:
            user_id (int): User ID to delete
            
        Returns:
            bool: True if successful
            
        Raises:
            UserError: If user not found
        """
        user = User.query.get(user_id)
        if not user:
            raise UserError(f"User ID {user_id} not found")

        db.session.delete(user)
        db.session.commit()
        return True

    @staticmethod
    def change_password(user_id, old_password, new_password):
        """
        Change a user's password (with verification).
        
        Args:
            user_id (int): User ID
            old_password (str): Current password for verification
            new_password (str): New password
            
        Returns:
            bool: True if successful
            
        Raises:
            UserError: If verification fails
        """
        user = User.query.get(user_id)
        if not user:
            raise UserError(f"User ID {user_id} not found")

        if not user.check_password(old_password):
            raise UserError("Current password is incorrect")

        user.set_password(new_password)
        db.session.commit()
        return True

    @staticmethod
    def reset_password(user_id, new_password):
        """
        Reset a user's password (admin function, no verification).
        
        Args:
            user_id (int): User ID
            new_password (str): New password
            
        Returns:
            bool: True if successful
            
        Raises:
            UserError: If user not found
        """
        user = User.query.get(user_id)
        if not user:
            raise UserError(f"User ID {user_id} not found")

        user.set_password(new_password)
        db.session.commit()
        return True

    @staticmethod
    def check_permission(user_id, required_role):
        """
        Check if a user has the required role permission.
        
        Args:
            user_id (int): User ID
            required_role (str or list): Required role(s)
            
        Returns:
            bool: True if user has permission
        """
        user = User.query.get(user_id)
        if not user:
            return False

        if isinstance(required_role, str):
            return user.role == required_role
        elif isinstance(required_role, list):
            return user.role in required_role
        
        return False