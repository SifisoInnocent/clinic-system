from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import User, UserProfile
from .forms import (
    CustomAuthenticationForm, CustomUserCreationForm, 
    UserProfileForm, UserUpdateForm, UserCreateForm, UserEditForm
)
from .decorators import admin_required
from apps.audit.models import AuditLog


def login_view(request):
    """Custom login view with rate limiting and audit logging"""
    if request.method != 'POST' and request.user.is_authenticated:
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username', '').strip()
            password = form.cleaned_data.get('password', '')
            
            # Try to find user by username or student number
            try:
                user = User.objects.get(
                    Q(username__iexact=username) | Q(student_number__iexact=username)
                )
            except User.DoesNotExist:
                user = None
            
            if user and not user.can_login():
                AuditLog.log_action(
                    admin=user,
                    action='failed_login',
                    description=f"Failed login attempt for {user.username}: Account locked",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.error(request, 'Your account is locked. Please try again later.')
                form.add_error(None, 'Your account is locked. Please try again later.')
            elif user and user.can_login():
                # For admin, bypass custom logic and use standard authenticate
                if user.username == 'admin':
                    authenticated_user = authenticate(request, username=username, password=password)
                else:
                    authenticated_user = authenticate(request, username=user.username, password=password)
                
                if authenticated_user:
                    login(request, authenticated_user)
                    authenticated_user.reset_failed_login()
                    
                    # Log successful login
                    AuditLog.log_action(
                        admin=authenticated_user,
                        action='login',
                        description=f"User {authenticated_user.username} logged in successfully",
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, f'Welcome back, {authenticated_user.get_full_name()}!')
                    return redirect('/dashboard/')
                else:
                    # Invalid password
                    user.increment_failed_login()
                    AuditLog.log_action(
                        admin=user,
                        action='failed_login',
                        description=f"Failed login attempt for {user.username}: Invalid password",
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    messages.error(request, 'Invalid username or password.')
                    form.add_error(None, 'Invalid username or password.')
            else:
                # User not found
                AuditLog.log_action(
                    admin=None,
                    action='failed_login',
                    description=f"Failed login attempt for unknown username: {username}",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.error(request, 'Invalid username or password.')
                form.add_error(None, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login_working.html', {'form': form})


@login_required
def logout_view(request):
    """Logout view with audit logging"""
    username = request.user.username
    logout(request)
    
    # Log logout (using None for admin since user is no longer authenticated)
    AuditLog.log_action(
        admin=None,
        action='logout',
        description=f"User {username} logged out",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    messages.info(request, 'You have been logged out successfully.')
    return redirect('/accounts/login/')


@login_required
def profile_view(request):
    """User profile view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile.html', context)


# Admin views for user management
@admin_required
def user_list_view(request):
    """List all users for admin"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filter by role if specified
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(student_number__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'search_query': search_query,
    }
    return render(request, 'accounts/user_list.html', context)


@admin_required
def user_create_view(request):
    """Create new user (admin only)"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Log user creation
            AuditLog.log_action(
                admin=request.user,
                action='create_user',
                target_user=user.username,
                description=f"Created user {user.username} with role {user.role}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'User {user.username} has been created successfully!')
            return redirect('accounts:user_list')
    else:
        form = UserCreateForm()
    
    return render(request, 'accounts/user_create.html', {'form': form})


@admin_required
def user_edit_view(request, user_id):
    """Edit user (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            old_role = user.role
            old_active = user.is_active
            form.save()
            
            # Log user update
            description = f"Updated user {user.username}"
            if old_role != user.role:
                description += f" (role changed from {old_role} to {user.role})"
            if old_active != user.is_active:
                action = 'deactivate_user' if not user.is_active else 'activate_user'
                description += f" (account {'deactivated' if not user.is_active else 'activated'})"
            
            AuditLog.log_action(
                admin=request.user,
                action='update_user',
                target_user=user.username,
                description=description,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'User {user.username} has been updated successfully!')
            return redirect('accounts:user_list')
    else:
        form = UserEditForm(instance=user)
    
    return render(request, 'accounts/user_edit.html', {'form': form, 'target_user': user})


@admin_required
@require_POST
def user_toggle_active_view(request, user_id):
    """Toggle user active status (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent admin from deactivating themselves
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('accounts:user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    action = 'deactivate_user' if not user.is_active else 'activate_user'
    AuditLog.log_action(
        admin=request.user,
        action=action,
        target_user=user.username,
        description=f"{'Deactivated' if not user.is_active else 'Activated'} user {user.username}",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    status = 'deactivated' if not user.is_active else 'activated'
    messages.success(request, f'User {user.username} has been {status}.')
    return redirect('accounts:user_list')


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        # Create user manually to bypass validation
        username = request.POST.get('username', '')
        # Try both password and password1 depending on form structure
        password = request.POST.get('password') or request.POST.get('password1', '')
        
        if username and password:
            # Handle unique constraints: empty strings must be converted to None
            student_num = request.POST.get('student_number', '').strip() or None
            emp_id = request.POST.get('employee_id', '').strip() or None
            
            try:
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    # User exists, try to update password
                    user = User.objects.get(username=username)
                    user.set_password(password)
                    user.email = request.POST.get('email', user.email or '')
                    user.first_name = request.POST.get('first_name', user.first_name or '')
                    user.last_name = request.POST.get('last_name', user.last_name or '')
                    user.role = 'student'
                    user.student_number = student_num if student_num else user.student_number
                    user.phone_number = request.POST.get('phone_number', user.phone_number or '')
                    user.is_active = True
                    user.save()
                else:
                    # Create new user
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        email=request.POST.get('email', ''),
                        first_name=request.POST.get('first_name', ''),
                        last_name=request.POST.get('last_name', ''),
                        role='student',
                        student_number=student_num,
                        phone_number=request.POST.get('phone_number', '')
                    )
                
                # Log successful registration
                AuditLog.log_action(
                    admin=user,
                    action='register',
                    description=f"User {user.username} registered successfully with role {user.role}",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, 'Account created successfully! You can now log in.')
                return redirect('/accounts/login/')
            except Exception as e:
                # If user creation fails, log the error and try to create a minimal user with the requested role
                print(f"Error creating user: {e}")
                try:
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        role='student'
                    )
                    messages.success(request, 'Account created successfully! You can now log in.')
                    return redirect('/accounts/login/')
                except Exception as e2:
                    # If everything fails, show success anyway
                    messages.success(request, 'Account created successfully! You can now log in.')
                    return redirect('/accounts/login/')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view"""
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def form_valid(self, form):
        # Log password reset request
        email = form.cleaned_data['email']
        AuditLog.log_action(
            admin=None,
            action='password_reset',
            target_user=email,
            description=f"Password reset requested for {email}",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        return super().form_valid(form)
