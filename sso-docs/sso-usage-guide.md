# Internal SSO Usage Guide

This guide explains how to use the Single Sign-On system for employees and administrators.

## What is SSO?

Single Sign-On (SSO) allows you to log in once and access all company applications without having to enter your credentials again. This provides:

- **Convenience**: One login for all applications
- **Security**: Centralized authentication and stronger password policies
- **Productivity**: Seamless switching between applications
- **Better Control**: Administrators can manage access from one place

## Getting Started

### Your SSO Account

Your SSO account uses your company email address as the username. If you don't have an account yet, contact your IT administrator or HR department.

**Account Details:**
- **Username**: Your company email address
- **Password**: Set during account creation or password reset
- **Roles**: Assigned based on your job function (User, Manager, Admin)

### First Time Login

1. Go to any company application (see [Available Applications](#available-applications))
2. Click "Login" or "Sign In"
3. You'll be redirected to the SSO login page
4. Enter your email address and password
5. Complete any required steps (email verification, password change)
6. You're now logged in to all applications!

## Available Applications

### Main Application (Port 3000)
- **URL**: http://localhost:3000
- **Purpose**: Primary company application
- **Access**: All authenticated users

### Admin Dashboard (Port 3002)
- **URL**: http://localhost:3002
- **Purpose**: System administration and user management
- **Access**: Administrators only
- **Features**:
  - User management
  - System monitoring
  - Security settings
  - Reports and analytics

### Employee Portal (Port 3003)
- **URL**: http://localhost:3003
- **Purpose**: Employee self-service portal
- **Access**: All authenticated users
- **Features**:
  - Profile management
  - HR services
  - Payroll information
  - IT support

## How SSO Works

### Login Process
1. **Navigate** to any company application
2. **Automatic Check**: System checks if you're already logged in
3. **Login Form**: If not logged in, you're redirected to the login page
4. **Authentication**: Enter your credentials
5. **Access Granted**: You're logged in to all applications

### Session Sharing
Once you log in to one application:
- ✅ All other applications recognize you automatically
- ✅ No need to enter credentials again
- ✅ Switch between apps seamlessly
- ✅ Single logout affects all applications

### Session Management
- **Session Duration**: 30 minutes of inactivity, 10 hours maximum
- **Auto-Refresh**: Tokens refresh automatically while you're active
- **Remember Me**: Option to stay logged in longer (if enabled)
- **Security**: Sessions expire for security

## User Roles and Permissions

### User Role (Default)
- Access to main application
- Access to employee portal
- Basic profile management
- Standard company resources

### Manager Role
- All user permissions
- Team management features
- Departmental reports
- Approval workflows

### Administrator Role
- All manager permissions
- User account management
- System configuration
- Security settings
- Full access to admin dashboard

## Common Tasks

### Updating Your Profile
1. Log in to any application
2. Go to Employee Portal (http://localhost:3003)
3. Click "Update Profile"
4. Modify your information
5. Save changes

### Changing Your Password
1. Go to Employee Portal
2. Click "Change Password"
3. Enter current password
4. Enter new password (must meet security requirements)
5. Confirm new password

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- Cannot be your username or email
- Cannot be one of your last 3 passwords

### Forgot Password
1. Go to any application login page
2. Click "Forgot Password"
3. Enter your email address
4. Check your email for reset instructions
5. Follow the link and set a new password

### Logging Out
- **Single App**: Click logout in any application
- **All Apps**: You'll be logged out of all applications
- **Automatic**: Sessions expire after inactivity

## Security Features

### Brute Force Protection
- **Lockout**: Account locked after 30 failed login attempts
- **Duration**: 15-minute lockout period
- **Progressive**: Longer lockouts for repeated failures
- **Recovery**: Contact IT if locked out

### Session Security
- **Encryption**: All communications encrypted
- **Token Expiry**: Automatic token refresh and expiry
- **Device Tracking**: Monitor active sessions
- **Secure Logout**: Proper session cleanup

### Monitoring
- **Login Events**: All login/logout events logged
- **Failed Attempts**: Failed login attempts tracked
- **Admin Alerts**: Administrators notified of security events
- **Audit Trail**: Complete access history maintained

## Troubleshooting

### Can't Log In
1. **Check Credentials**: Verify email and password
2. **Account Status**: Ensure account is not locked/disabled
3. **Browser Issues**: Clear cache and cookies
4. **Contact IT**: If problems persist

### Session Issues
1. **Refresh Browser**: Try refreshing the page
2. **Clear Browser Data**: Clear cookies and local storage
3. **Private/Incognito**: Try in private browsing mode
4. **Different Browser**: Test with another browser

### Application Access
1. **Check URL**: Ensure you're using the correct application URL
2. **Permissions**: Verify you have access to the specific application
3. **Role Requirements**: Some apps require specific roles
4. **Network**: Check your network connection

### Common Error Messages

#### "Access Denied"
- **Cause**: Insufficient permissions for the application
- **Solution**: Contact your manager or IT administrator

#### "Session Expired"
- **Cause**: Inactive for too long or token expired
- **Solution**: Log in again

#### "Account Locked"
- **Cause**: Too many failed login attempts
- **Solution**: Wait 15 minutes or contact IT

#### "Invalid Credentials"
- **Cause**: Wrong email or password
- **Solution**: Verify credentials or reset password

## Mobile Access

### Mobile Browser
- All applications work on mobile browsers
- Responsive design for optimal mobile experience
- Same SSO functionality as desktop

### Mobile Apps (Future)
- Native mobile apps will integrate with SSO
- Same login credentials
- Consistent user experience

## Best Practices

### Security
1. **Strong Passwords**: Use complex, unique passwords
2. **Regular Updates**: Change password periodically
3. **Secure Devices**: Only use trusted devices
4. **Logout**: Always log out on shared computers
5. **Report Issues**: Report suspicious activity immediately

### Productivity
1. **Bookmarks**: Bookmark frequently used applications
2. **Multiple Tabs**: Open multiple applications in different tabs
3. **Session Awareness**: Understand session timeout limits
4. **Profile Updates**: Keep your profile information current

## Getting Help

### IT Support
- **Portal**: Submit tickets through Employee Portal
- **Email**: it-support@company.com
- **Phone**: Extension 1234
- **Hours**: Monday-Friday, 9 AM - 5 PM

### Self-Service
- **Password Reset**: Use forgot password feature
- **Profile Updates**: Use Employee Portal
- **Documentation**: Check this guide and setup documentation
- **FAQ**: Common questions answered below

## Frequently Asked Questions

### General

**Q: Do I need to remember multiple passwords?**
A: No, you only need one password for SSO. This gives you access to all company applications.

**Q: What if I forget my password?**
A: Use the "Forgot Password" link on any login page to reset it.

**Q: Can I use SSO on my phone?**
A: Yes, all applications work on mobile browsers with the same SSO functionality.

**Q: How long do I stay logged in?**
A: Sessions last 30 minutes of inactivity or 10 hours maximum, whichever comes first.

### Technical

**Q: Why am I being asked to log in again?**
A: Your session may have expired due to inactivity or reaching the maximum session time.

**Q: Can I stay logged in longer?**
A: Use the "Remember Me" option if available, but this may not be enabled for security reasons.

**Q: What browsers are supported?**
A: All modern browsers including Chrome, Firefox, Safari, and Edge.

**Q: Is my data secure?**
A: Yes, all communications are encrypted and we follow industry security standards.

### Access

**Q: I can't access the Admin Dashboard. Why?**
A: The Admin Dashboard requires administrator privileges. Contact IT if you need access.

**Q: Some features are missing. What's wrong?**
A: Features may be restricted based on your role. Contact your manager about additional permissions.

**Q: Can I access applications from home?**
A: Yes, if your organization allows remote access. VPN may be required.

## Contact Information

- **IT Helpdesk**: it-support@company.com
- **System Administrator**: admin@company.com
- **HR Department**: hr@company.com
- **Security Team**: security@company.com

---

*This guide is updated regularly. Please check for the latest version and updates.*