# SSO System User Guide

## Overview

Welcome to the i4planet SSO (Single Sign-On) system. This guide will help you understand how to use the system effectively and securely.

## What is SSO?

Single Sign-On (SSO) allows you to authenticate once and access multiple applications without needing to log in again. This provides:

- **Convenience**: One set of credentials for all integrated applications
- **Security**: Centralized authentication with enhanced security features
- **Productivity**: Seamless access across multiple services
- **Consistency**: Unified login experience across all platforms

## Getting Started

### Account Setup

Your SSO account is created using your email address as the username. Contact your system administrator if you need an account.

**Account Information:**
- **Username**: Your email address
- **Password**: Set during account creation or password reset
- **Roles**: Assigned based on your access requirements

### First Login

1. Navigate to any integrated application
2. Click "Sign In" or "Login"
3. You'll be redirected to the SSO login page
4. Enter your email address and password
5. Complete email verification if required
6. You're now authenticated across all applications

## Available Applications

### Main Application
- **URL**: `http://localhost:3000`
- **Description**: Primary application interface
- **Access**: All authenticated users

### Employee Portal
- **URL**: `http://localhost:3003`
- **Description**: Self-service portal for profile management
- **Access**: All authenticated users
- **Features**:
  - Profile management
  - Password changes
  - Account settings

### Admin Dashboard
- **URL**: `http://localhost:3002`
- **Description**: Administrative interface
- **Access**: Administrators only
- **Features**:
  - User management
  - System configuration
  - Security monitoring

## How SSO Works

### Authentication Flow

1. **Access Request**: Navigate to any integrated application
2. **Authentication Check**: System verifies if you're already logged in
3. **Login Redirect**: If not authenticated, you're redirected to the login page
4. **Credential Verification**: Enter your username and password
5. **Token Generation**: System generates secure tokens for your session
6. **Application Access**: You're granted access to the requested application

### Session Management

- **Session Duration**: 30 minutes of inactivity or 10 hours maximum
- **Auto-Refresh**: Tokens automatically refresh while you're active
- **Cross-Application**: Login status is shared across all integrated apps
- **Secure Logout**: Logging out of one application logs you out of all

## User Roles and Permissions

### User (Default)
- Access to main application
- Access to employee portal
- Basic profile management
- Standard application features

### Manager
- All user permissions
- Team management features
- Extended reporting capabilities
- Approval workflows

### Administrator
- All manager permissions
- User account management
- System configuration
- Security settings management
- Full admin dashboard access

## Common Tasks

### Managing Your Profile

1. Log in to any application
2. Navigate to the Employee Portal
3. Click "Profile Settings"
4. Update your information:
   - First and last name
   - Email address (requires verification)
   - Phone number
   - Department/role information
5. Save changes

### Changing Your Password

1. Go to Employee Portal
2. Click "Change Password"
3. Enter your current password
4. Enter new password (must meet requirements)
5. Confirm new password
6. Save changes

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- Cannot be your username or email
- Cannot be one of your last 3 passwords

### Password Reset

If you forget your password:

1. Go to any application login page
2. Click "Forgot Password?"
3. Enter your email address
4. Check your email for reset instructions
5. Click the reset link in your email
6. Set a new password following the requirements
7. Log in with your new password

### Logging Out

- **Single Logout**: Click logout in any application to be logged out of all
- **Automatic Logout**: Sessions expire after inactivity for security
- **Manual Logout**: Always log out when using shared computers

## Security Features

### Account Protection

- **Brute Force Protection**: Account locked after 30 failed attempts
- **Lockout Duration**: 15-minute lockout period
- **Progressive Lockout**: Longer lockouts for repeated failures
- **Account Recovery**: Contact administrator if locked out

### Session Security

- **Encryption**: All communications are encrypted
- **Token Expiry**: Automatic token refresh and expiration
- **Secure Cookies**: Session data protected with secure cookies
- **Device Tracking**: Monitor active sessions across devices

### Monitoring and Audit

- **Login Events**: All authentication events are logged
- **Failed Attempts**: Failed login attempts are tracked
- **Admin Notifications**: Administrators are alerted to security events
- **Audit Trail**: Complete access history is maintained

## Troubleshooting

### Login Issues

**Cannot Log In:**
1. Verify your email and password
2. Check if your account is active
3. Clear browser cache and cookies
4. Try a different browser
5. Contact support if issues persist

**Session Expired:**
1. This is normal after inactivity
2. Simply log in again
3. Check if you have the "Remember Me" option enabled

**Account Locked:**
1. Wait 15 minutes for automatic unlock
2. Contact administrator if urgent
3. Review recent login attempts

### Application Access Issues

**Access Denied:**
1. Verify you have permission for the specific application
2. Check your assigned roles
3. Contact your manager or administrator

**Application Not Loading:**
1. Check your internet connection
2. Verify the correct URL
3. Try refreshing the page
4. Clear browser cache

### Browser Compatibility

**Supported Browsers:**
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**Browser Issues:**
1. Update to the latest browser version
2. Enable JavaScript
3. Clear cache and cookies
4. Disable browser extensions temporarily

## Best Practices

### Security

1. **Strong Passwords**: Use complex, unique passwords
2. **Regular Updates**: Change passwords periodically
3. **Secure Devices**: Only use trusted devices
4. **Logout**: Always log out on shared computers
5. **Report Issues**: Report suspicious activity immediately

### Productivity

1. **Bookmarks**: Bookmark frequently used applications
2. **Multiple Tabs**: Open different applications in separate tabs
3. **Session Awareness**: Understand session timeout limits
4. **Profile Maintenance**: Keep your profile information current

### Mobile Access

1. **Mobile Browser**: All applications work on mobile browsers
2. **Responsive Design**: Optimized for mobile devices
3. **Same Functionality**: Full SSO features available on mobile
4. **Data Security**: Same security standards apply

## Getting Help

### Self-Service Options

- **Password Reset**: Use the forgot password feature
- **Profile Updates**: Use the Employee Portal
- **Documentation**: Refer to this guide and setup documentation

### Support Channels

- **IT Helpdesk**: Submit tickets through Employee Portal
- **Email Support**: it-support@company.com
- **Phone Support**: Contact your system administrator
- **Business Hours**: Monday-Friday, 9 AM - 5 PM

### Emergency Access

If you cannot access the system during business hours:
1. Contact your immediate supervisor
2. Use alternative communication methods
3. Document the issue for follow-up

## Frequently Asked Questions

### General Usage

**Q: Do I need different passwords for different applications?**
A: No, SSO allows you to use one password for all integrated applications.

**Q: What happens if I forget my password?**
A: Use the "Forgot Password" link on any login page to reset it via email.

**Q: Can I use SSO on my mobile device?**
A: Yes, all applications work on mobile browsers with full SSO functionality.

**Q: How long do I stay logged in?**
A: Sessions last 30 minutes of inactivity or 10 hours maximum.

### Technical Questions

**Q: Why am I asked to log in again?**
A: Your session expired due to inactivity or reaching the maximum session time.

**Q: Can I extend my session time?**
A: Session times are set for security and cannot be extended by users.

**Q: What browsers are supported?**
A: All modern browsers including Chrome, Firefox, Safari, and Edge.

**Q: Is my data secure?**
A: Yes, all communications are encrypted and we follow industry security standards.

### Access and Permissions

**Q: I can't access certain applications. Why?**
A: Access is based on your assigned roles. Contact your administrator for additional permissions.

**Q: Can I access applications from home?**
A: Yes, if your organization allows remote access. VPN may be required.

**Q: How do I know what applications I have access to?**
A: Check with your administrator or try accessing applications through the main portal.

## Contact Information

For additional support, contact:

- **IT Helpdesk**: it-support@company.com
- **System Administrator**: admin@company.com
- **Emergency Contact**: Your immediate supervisor

---

*This guide is regularly updated. Please check for the latest version and contact support if you have suggestions for improvements.*