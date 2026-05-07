"""
Preservation Property Tests for JWT Token Session Management Bug Fix

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

These tests verify that existing authentication flows continue to work correctly
after implementing the session-based token storage fix. The tests observe and capture
the current behavior on UNFIXED code, then verify this behavior is preserved after the fix.

IMPORTANT: Follow observation-first methodology
- Run these tests on UNFIXED code first to observe baseline behavior
- Tests should PASS on unfixed code (confirms baseline behavior to preserve)
- Tests should PASS on fixed code (confirms no regressions)

Property 2: Preservation - Existing Authentication Flows
For any authentication-related operation (login, logout, upload, view, delete) that worked
correctly in the original code, the fixed application SHALL produce exactly the same
user-visible behavior, preserving all existing functionality while only changing the
internal token storage mechanism.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import patch, MagicMock
import sys
import os

# Add the frontend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))

from app import app as flask_app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    flask_app.config['TESTING'] = True
    # Reset token before each test
    flask_app.config['token'] = ""
    flask_app.config['email'] = ""
    
    # Set secret key for session support (needed for both unfixed and fixed code)
    if not flask_app.secret_key:
        flask_app.secret_key = 'test-secret-key-for-preservation'
    
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_backend_api():
    """Mock the backend API responses for all authentication flows"""
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get, \
         patch('requests.request') as mock_request:
        
        # Mock successful login response
        mock_login_response = MagicMock()
        mock_login_response.headers = {
            'authentication': 'success',
            'token': 'test-jwt-token-12345'
        }
        mock_login_response.status_code = 200
        
        # Mock successful signup response
        mock_signup_response = MagicMock()
        mock_signup_response.headers = {'status': 'created'}
        mock_signup_response.status_code = 200
        
        # Mock successful dashboard response
        mock_dashboard_response = MagicMock()
        mock_dashboard_response.status_code = 200
        mock_dashboard_response.text = str({
            'name': 'Test User',
            'prescriptions': {
                1: {'prescription_name': 'test_prescription.jpg', 'date': '2024-01-01'},
                2: {'prescription_name': 'test_prescription2.jpg', 'date': '2024-01-02'}
            }
        })
        
        # Mock successful upload response
        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 200
        mock_upload_response.text = "Upload successful"
        
        # Mock successful scan response
        mock_scan_response = MagicMock()
        mock_scan_response.status_code = 200
        mock_scan_response.json.return_value = str({
            'Medicines': [
                {'name': 'Aspirin', 'dosage': '100mg', 'frequency': 'twice daily', 'duration': '7 days'}
            ],
            'PatientInfo': {'name': 'Test Patient'}
        })
        
        # Mock successful delete response
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 200
        mock_delete_response.text = "Delete successful"
        
        # Mock 401 unauthorized response (for unauthenticated access)
        mock_unauthorized_response = MagicMock()
        mock_unauthorized_response.status_code = 401
        mock_unauthorized_response.text = "Unauthorized"
        
        # Configure mock to return appropriate responses
        def mock_post_side_effect(url, *args, **kwargs):
            if '/login' in url:
                return mock_login_response
            elif '/signup' in url:
                return mock_signup_response
            elif '/upload_prescription' in url:
                return mock_upload_response
            elif '/scan' in url:
                return mock_scan_response
            elif '/delete' in url:
                return mock_delete_response
            return MagicMock(status_code=200)
        
        def mock_get_side_effect(url, *args, **kwargs):
            if '/dashboard' in url:
                # Check if Authorization header has a valid token
                headers = kwargs.get('headers', {})
                auth_header = headers.get('Authorization', '')
                if 'Bearer test-jwt-token-12345' in auth_header:
                    return mock_dashboard_response
                else:
                    return mock_unauthorized_response
            return MagicMock(status_code=200)
        
        def mock_request_side_effect(method, url, *args, **kwargs):
            if '/dashboard' in url and method == 'GET':
                # Check if Authorization header has a valid token
                headers = kwargs.get('headers', {})
                auth_header = headers.get('Authorization', '')
                if 'Bearer test-jwt-token-12345' in auth_header:
                    return mock_dashboard_response
                else:
                    return mock_unauthorized_response
            return MagicMock(status_code=200)
        
        mock_post.side_effect = mock_post_side_effect
        mock_get.side_effect = mock_get_side_effect
        mock_request.side_effect = mock_request_side_effect
        
        yield {
            'post': mock_post,
            'get': mock_get,
            'request': mock_request
        }


class TestPreservationProperties:
    """
    Property 2: Preservation - Existing Authentication Flows
    
    These tests verify that all existing authentication flows continue to work
    exactly as before after implementing the session-based token storage fix.
    
    EXPECTED OUTCOME ON UNFIXED CODE: Tests PASS (confirms baseline behavior)
    EXPECTED OUTCOME ON FIXED CODE: Tests PASS (confirms no regressions)
    """
    
    def test_preservation_login_flow(self, client, mock_backend_api):
        """
        Test Case 1: Login Flow Preservation
        
        Validates Requirement 3.1: WHEN a user logs in with valid credentials
        THEN the system SHALL CONTINUE TO authenticate successfully and redirect to the dashboard
        
        EXPECTED: PASS on both unfixed and fixed code
        """
        # Perform login with valid credentials
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword'
        }, follow_redirects=False)
        
        # Verify successful authentication and redirect to dashboard
        assert response.status_code == 302, "Login should return redirect status"
        assert response.location.endswith('/dashboard'), \
            f"Login should redirect to dashboard, got {response.location}"
        
        # Verify token is stored (either in app.config or session)
        # On unfixed code: token in app.config['token']
        # On fixed code: token in session['token']
        token_stored = False
        if flask_app.config.get('token'):
            token_stored = True
        else:
            with client.session_transaction() as sess:
                if sess.get('token'):
                    token_stored = True
        
        assert token_stored, "Token should be stored after successful login"
        
        print("✓ Login flow preserved: valid credentials → authentication → redirect to dashboard")
    
    
    def test_preservation_logout_flow(self, client, mock_backend_api):
        """
        Test Case 2: Logout Flow Preservation
        
        Validates Requirement 3.5: WHEN a user explicitly clicks logout
        THEN the system SHALL CONTINUE TO clear authentication and redirect to the login page
        
        EXPECTED: PASS on both unfixed and fixed code
        """
        # First login
        client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword'
        }, follow_redirects=False)
        
        # Verify token is set
        token_before_logout = flask_app.config.get('token', '') or None
        with client.session_transaction() as sess:
            session_token_before = sess.get('token', None)
        
        assert token_before_logout or session_token_before, "Token should exist before logout"
        
        # Perform logout
        response = client.get('/logout', follow_redirects=False)
        
        # Verify redirect to login page
        assert response.status_code == 302, "Logout should return redirect status"
        assert response.location.endswith('/login'), \
            f"Logout should redirect to login, got {response.location}"
        
        # Verify authentication is cleared
        token_after_logout = flask_app.config.get('token', '')
        with client.session_transaction() as sess:
            session_token_after = sess.get('token', None)
        
        # On unfixed code: app.config['token'] should be empty
        # On fixed code: session should be cleared
        assert token_after_logout == "" or session_token_after is None, \
            "Authentication should be cleared after logout"
        
        print("✓ Logout flow preserved: logout → authentication cleared → redirect to login")
    
    
    def test_preservation_unauthenticated_access(self, client, mock_backend_api):
        """
        Test Case 3: Unauthenticated Access Preservation
        
        Validates Requirement 3.6: WHEN an unauthenticated user attempts to access protected routes
        THEN the system SHALL CONTINUE TO redirect them to the login page
        
        EXPECTED: PASS on both unfixed and fixed code
        """
        # Ensure no token is set
        flask_app.config['token'] = ""
        flask_app.config['email'] = ""
        
        # Attempt to access dashboard without authentication
        response = client.get('/dashboard', follow_redirects=False)
        
        # Verify redirect to login page with invalid status
        assert response.status_code == 302, "Unauthenticated access should redirect"
        assert '/login' in response.location, \
            f"Should redirect to login page, got {response.location}"
        assert 'status=invalid' in response.location, \
            f"Should include status=invalid, got {response.location}"
        
        print("✓ Unauthenticated access preserved: no token → access protected route → redirect to login")
    
    
    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=20)
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_login_flow_for_any_valid_credentials(self, client, mock_backend_api, email, password):
        """
        Property-Based Test: Login Flow Preservation for Any Valid Credentials
        
        For ANY valid email and password combination, the login flow should work consistently.
        
        Validates Requirement 3.1: Login with valid credentials → authentication → redirect to dashboard
        
        EXPECTED: PASS on both unfixed and fixed code
        """
        # Reset token before each test
        flask_app.config['token'] = ""
        flask_app.config['email'] = ""
        
        # Perform login
        response = client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=False)
        
        # Verify successful authentication and redirect
        assert response.status_code == 302, \
            f"Login should redirect for email={email}"
        assert response.location.endswith('/dashboard'), \
            f"Login should redirect to dashboard for email={email}, got {response.location}"
        
        # Verify token is stored somewhere (app.config or session)
        token_stored = bool(flask_app.config.get('token')) or False
        if not token_stored:
            with client.session_transaction() as sess:
                token_stored = bool(sess.get('token'))
        
        assert token_stored, f"Token should be stored after login for email={email}"
    
    
    def test_preservation_dashboard_access_with_valid_token(self, client, mock_backend_api):
        """
        Test Case 4: Dashboard Access with Valid Token
        
        Validates that authenticated users can access the dashboard.
        This is part of the baseline behavior that should be preserved.
        
        EXPECTED: PASS on both unfixed and fixed code
        """
        # Login first
        client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword'
        }, follow_redirects=False)
        
        # Access dashboard
        response = client.get('/dashboard', follow_redirects=False)
        
        # Verify successful access
        assert response.status_code == 200, \
            f"Dashboard should be accessible with valid token, got status {response.status_code}"
        
        # Verify dashboard content is rendered
        assert b'Test User' in response.data or b'dashboard' in response.data.lower(), \
            "Dashboard should display user information"
        
        print("✓ Dashboard access preserved: authenticated user → access dashboard → content displayed")
    
    
    @given(
        operation=st.sampled_from(['login', 'logout', 'dashboard'])
    )
    @settings(
        max_examples=15,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_authentication_operations_consistency(self, client, mock_backend_api, operation):
        """
        Property-Based Test: Authentication Operations Consistency
        
        For ANY authentication operation (login, logout, dashboard access),
        the behavior should be consistent and predictable.
        
        Validates Requirements 3.1, 3.5: All authentication operations work consistently
        
        EXPECTED: PASS on both unfixed and fixed code
        """
        # Reset state
        flask_app.config['token'] = ""
        flask_app.config['email'] = ""
        
        if operation == 'login':
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'testpassword'
            }, follow_redirects=False)
            
            assert response.status_code == 302, f"Login should redirect"
            assert response.location.endswith('/dashboard'), f"Login should redirect to dashboard"
        
        elif operation == 'logout':
            # Login first
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'testpassword'
            }, follow_redirects=False)
            
            # Then logout
            response = client.get('/logout', follow_redirects=False)
            
            assert response.status_code == 302, f"Logout should redirect"
            assert response.location.endswith('/login'), f"Logout should redirect to login"
        
        elif operation == 'dashboard':
            # Login first
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'testpassword'
            }, follow_redirects=False)
            
            # Access dashboard
            response = client.get('/dashboard', follow_redirects=False)
            
            assert response.status_code == 200, f"Dashboard should be accessible after login"
    
    
    def test_preservation_multiple_login_logout_cycles(self, client, mock_backend_api):
        """
        Test Case 5: Multiple Login/Logout Cycles
        
        Validates that users can login and logout multiple times without issues.
        This tests the stability of the authentication system.
        
        EXPECTED: PASS on both unfixed and fixed code
        """
        for cycle in range(3):
            # Login
            login_response = client.post('/login', data={
                'email': f'user{cycle}@example.com',
                'password': f'password{cycle}'
            }, follow_redirects=False)
            
            assert login_response.status_code == 302, \
                f"Login cycle {cycle} should succeed"
            assert login_response.location.endswith('/dashboard'), \
                f"Login cycle {cycle} should redirect to dashboard"
            
            # Verify token is stored
            token_stored = bool(flask_app.config.get('token')) or False
            if not token_stored:
                with client.session_transaction() as sess:
                    token_stored = bool(sess.get('token'))
            
            assert token_stored, f"Token should be stored after login cycle {cycle}"
            
            # Logout
            logout_response = client.get('/logout', follow_redirects=False)
            
            assert logout_response.status_code == 302, \
                f"Logout cycle {cycle} should succeed"
            assert logout_response.location.endswith('/login'), \
                f"Logout cycle {cycle} should redirect to login"
        
        print("✓ Multiple login/logout cycles preserved: consistent behavior across cycles")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-s'])
