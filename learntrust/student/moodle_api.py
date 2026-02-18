"""
Moodle REST API Integration Utility
====================================

Provides functions to interact with Moodle REST API for user management
and course enrollment.

Required settings in Django settings.py:
    MOODLE_BASE_URL = "http://localhost:80/moodle"
    MOODLE_TOKEN = "your_webservice_token"
"""

import requests
from django.conf import settings


class MoodleAPIError(Exception):
    """Custom exception for Moodle API errors"""
    pass


def _make_moodle_request(function, params=None):
    """
    Make a request to Moodle REST API
    
    Args:
        function: Moodle webservice function name
        params: Dictionary of parameters
        
    Returns:
        JSON response from Moodle
        
    Raises:
        MoodleAPIError: If request fails or returns error
    """
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    
    request_params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": function,
        "moodlewsrestformat": "json",
    }
    
    if params:
        request_params.update(params)
    
    try:
        response = requests.post(url, params=request_params)
        response.raise_for_status()
        data = response.json()
        
        # Check for Moodle error
        if isinstance(data, dict) and 'errorcode' in data:
            raise MoodleAPIError(f"Moodle API Error: {data.get('message', 'Unknown error')}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        raise MoodleAPIError(f"Request failed: {str(e)}")


def create_moodle_user(user):
    """
    Create a new user in Moodle
    
    Args:
        user: Django User instance
        
    Returns:
        int: Moodle user ID
        
    Raises:
        MoodleAPIError: If user creation fails
    """
    params = {
        "users[0][username]": user.username,
        "users[0][email]": user.email,
        "users[0][firstname]": user.first_name or user.username,
        "users[0][lastname]": user.last_name or "User",
        "users[0][auth]": "manual",
        "users[0][idnumber]": str(user.id),
    }
    
    response = _make_moodle_request("core_user_create_users", params)
    
    if response and len(response) > 0:
        return response[0].get('id')
    else:
        raise MoodleAPIError("User creation failed: Empty response")


def create_moodle_course(course):
    """
    Create a course in Moodle corresponding to local Course instance.

    Args:
        course: Django Course instance

    Returns:
        int: Moodle course ID
    """
    # Build sensible defaults for Moodle course fields
    shortname = getattr(course, 'title', 'course').strip().replace(' ', '_')[:50]
    params = {
        "courses[0][fullname]": course.title,
        "courses[0][shortname]": shortname,
        "courses[0][categoryid]": getattr(settings, 'MOODLE_DEFAULT_CATEGORY_ID', 1),
        "courses[0][visible]": 1,
        "courses[0][summary]": course.description or '',
    }

    response = _make_moodle_request("core_course_create_courses", params)

    if response and len(response) > 0:
        return response[0].get('id')
    else:
        raise MoodleAPIError("Course creation failed: Empty response")


def get_moodle_user(email):
    """
    Get Moodle user by email
    
    Args:
        email: User email address
        
    Returns:
        dict: User data with 'id' key, or None if not found
    """
    params = {
        "criteria[0][key]": "email",
        "criteria[0][value]": email,
    }
    
    try:
        response = _make_moodle_request("core_user_get_users", params)
        
        users = response.get('users', [])
        if users and len(users) > 0:
            return users[0]
        return None
        
    except MoodleAPIError:
        return None


def enroll_user_to_course(moodle_user_id, course_id):
    """
    Enroll a user to a Moodle course
    
    Args:
        moodle_user_id: Moodle user ID
        course_id: Moodle course ID
        
    Returns:
        bool: True if enrollment successful
        
    Raises:
        MoodleAPIError: If enrollment fails
    """
    params = {
        "enrolments[0][roleid]": 5,  # Student role
        "enrolments[0][userid]": moodle_user_id,
        "enrolments[0][courseid]": course_id,
    }
    
    response = _make_moodle_request("enrol_manual_enrol_users", params)
    
    # Successful enrollment returns None or empty list
    return True


def get_user_courses(moodle_user_id):
    """
    Get list of courses a user is enrolled in
    
    Args:
        moodle_user_id: Moodle user ID
        
    Returns:
        list: List of course dictionaries with id, fullname, shortname, etc.
    """
    params = {
        "userid": moodle_user_id,
    }
    
    try:
        response = _make_moodle_request("core_enrol_get_users_courses", params)
        return response if response else []
    except MoodleAPIError:
        return []


def sync_user_with_moodle(user):
    """
    Sync Django user with Moodle - creates if not exists
    
    Args:
        user: Django User instance
        
    Returns:
        int: Moodle user ID
    """
    # Check if user exists in Moodle
    moodle_user = get_moodle_user(user.email)
    
    if moodle_user:
        return moodle_user['id']
    else:
        # Create new user
        return create_moodle_user(user)


def sync_enrollment_with_moodle(user, course):
    """
    Sync Django enrollment with Moodle - enrolls user in Moodle course
    
    Args:
        user: Django User instance
        course: Django Course instance (must have moodle_course_id field)
        
    Returns:
        bool: True if enrollment successful
    """
    from .models import StudentProfile
    
    try:
        profile = StudentProfile.objects.get(user=user)
        
        # Ensure user has Moodle ID
        if not profile.moodle_user_id:
            moodle_user_id = sync_user_with_moodle(user)
            profile.moodle_user_id = moodle_user_id
            profile.save()
        
        # Get Moodle course ID from course object
        moodle_course_id = getattr(course, 'moodle_course_id', None)
        if not moodle_course_id:
            # If no moodle_course_id set, skip Moodle enrollment
            return False
        
        # Enroll user in Moodle course
        return enroll_user_to_course(profile.moodle_user_id, moodle_course_id)
        
    except StudentProfile.DoesNotExist:
        return False
    except Exception:
        return False
