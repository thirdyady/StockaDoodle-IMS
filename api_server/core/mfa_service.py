# api_server/core/mfa_service.py

import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()


class MFAService:
    """
    Multi-Factor Authentication service for sending and verifying codes.
    Used for admin and manager login security.
    """
    
    # In-memory store for MFA codes (consider Redis or database for production)
    _active_codes = {}
    
    # MFA Configuration from environment variables
    MFA_CODE_LENGTH = int(os.getenv('MFA_CODE_LENGTH', 6))
    MFA_CODE_EXPIRY_MINUTES = int(os.getenv('MFA_CODE_EXPIRY_MINUTES', 5))
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@stockadoodle.com')
    
    @staticmethod
    def generate_code():
        """
        Generate a random numeric MFA code.
        
        Returns:
            str: Random code of specified length
        """
        return ''.join(random.choices(string.digits, k=MFAService.MFA_CODE_LENGTH))
    
    @staticmethod
    def send_mfa_code(email, username):
        """
        Generate and send an MFA code to the user's email.
        
        Args:
            email (str): Recipient email address
            username (str): Username for personalization
            
        Returns:
            str: The generated code (for testing/verification)
            
        Raises:
            Exception: If email sending fails
        """
        code = MFAService.generate_code()
        expiry = datetime.utcnow() + timedelta(minutes=MFAService.MFA_CODE_EXPIRY_MINUTES)
        
        # Store code with expiry
        MFAService._active_codes[username] = {
            'code': code,
            'expiry': expiry,
            'attempts': 0,
            'email': email
        }
        
        # Create email message
        subject = "StockaDoodle - Your MFA Code"
        body = f"""
Hello {username},

Your Multi-Factor Authentication (MFA) code is:

{code}

This code will expire in {MFAService.MFA_CODE_EXPIRY_MINUTES} minutes.

If you did not request this code, please ignore this email and contact your system administrator.

Best regards,
StockaDoodle Security Team
"""
        
        # Send email
        if MFAService.SMTP_USERNAME and MFAService.SMTP_PASSWORD:
            try:
                msg = MIMEMultipart()
                msg['From'] = MFAService.SENDER_EMAIL
                msg['To'] = email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(MFAService.SMTP_HOST, MFAService.SMTP_PORT)
                server.starttls()
                server.login(MFAService.SMTP_USERNAME, MFAService.SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()
                
                print(f"MFA code sent to {email}")
            except Exception as e:
                print(f"Failed to send MFA email: {e}")
                raise Exception("Failed to send MFA code")
        else:
            # For development: print code to console
            print(f"\n{'='*50}")
            print(f"MFA CODE for {username}: {code}")
            print(f"Email would be sent to: {email}")
            print(f"Expires in {MFAService.MFA_CODE_EXPIRY_MINUTES} minutes")
            print(f"{'='*50}\n")
        
        return code
    
    @staticmethod
    def verify_code(username, entered_code):
        """
        Verify an MFA code entered by the user.
        
        Args:
            username (str): Username to verify code for
            entered_code (str): Code entered by user
            
        Returns:
            bool: True if code is valid and not expired
        """
        if username not in MFAService._active_codes:
            print(f"No MFA code found for username: {username}")
            return False
        
        stored_data = MFAService._active_codes[username]
        
        # Check expiry
        if datetime.utcnow() > stored_data['expiry']:
            print(f"MFA code expired for {username}")
            del MFAService._active_codes[username]
            return False
        
        # Check attempts (max 3 attempts)
        if stored_data['attempts'] >= 3:
            print(f"Maximum MFA attempts exceeded for {username}")
            del MFAService._active_codes[username]
            return False
        
        # Verify code
        if entered_code == stored_data['code']:
            # Success - remove code
            print(f"MFA code verified successfully for {username}")
            del MFAService._active_codes[username]
            return True
        else:
            # Increment attempts
            stored_data['attempts'] += 1
            remaining = 3 - stored_data['attempts']
            print(f"Invalid MFA code for {username}. {remaining} attempts remaining.")
            return False
    
    @staticmethod
    def resend_code(email, username):
        """
        Resend an MFA code (generates a new one).
        
        Args:
            email (str): Recipient email
            username (str): Username
            
        Returns:
            str: The new code
        """
        # Remove old code if exists
        if username in MFAService._active_codes:
            del MFAService._active_codes[username]
        
        # Send new code
        return MFAService.send_mfa_code(email, username)
    
    @staticmethod
    def clear_expired_codes():
        """
        Clean up expired codes from memory (should be run periodically).
        
        Returns:
            int: Number of codes cleared
        """
        now = datetime.utcnow()
        expired = [
            username for username, data in MFAService._active_codes.items()
            if data['expiry'] < now
        ]
        for username in expired:
            del MFAService._active_codes[username]
        
        if expired:
            print(f"Cleared {len(expired)} expired MFA codes")
        
        return len(expired)
    
    @staticmethod
    def get_active_codes_count():
        """
        Get the count of active MFA codes (for monitoring).
        
        Returns:
            int: Number of active codes
        """
        return len(MFAService._active_codes)
    
    @staticmethod
    def get_code_info(username):
        """
        Get information about an active MFA code (for debugging).
        
        Args:
            username (str): Username to check
            
        Returns:
            dict: Code info or None
        """
        if username not in MFAService._active_codes:
            return None
        
        data = MFAService._active_codes[username]
        return {
            'username': username,
            'email': data['email'],
            'attempts': data['attempts'],
            'expires_at': data['expiry'].isoformat(),
            'is_expired': datetime.utcnow() > data['expiry']
        }
    
    @staticmethod
    def revoke_code(username):
        """
        Manually revoke an MFA code (admin function).
        
        Args:
            username (str): Username to revoke code for
            
        Returns:
            bool: True if code was revoked
        """
        if username in MFAService._active_codes:
            del MFAService._active_codes[username]
            print(f"MFA code revoked for {username}")
            return True
        return False