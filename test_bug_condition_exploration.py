"""
Bug Condition Exploration Test for JWT Token Session Management Bug

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

This test explores the bug condition where JWT tokens are stored in app.config['token']
(application-level) instead of user-specific Flask sessions, causing authentication failures
when users navigate between pages.

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

The test encodes the expected behavior - it will validate the fix when it passes after implementation.

NOTE: These tests directly inspect app.config['token'] to demonstrate the bug exists in the
current implementation. The bug manifests as:
1. Token stored in app.config (application-level) instead of session (user-level)
2. Token overwritten by concurrent users
3. Token not persisting across separate client sessions
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
    
    # NOTE: On unfixed code, app.secret_key is NOT set, so sessions won't work
    # This is part of the bug! We'll set it here for testing purposes to demonstrate
    # what SHOULD happen when sessions are properly configured.
    # On fixed code, app.secret_key will be set in app.py
    if not flask_app.secret_key:
        flask_app.secret_key = 'test-secret-key-for-exploration'
    
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_api():
    """Mock the backend API responses"""
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
        
        # Mock successful dashboard response
        mock_dashboard_response = MagicMock()
        mock_dashboard_response.status_code = 200
        mock_dashboard_response.text = "{'name': 'Test User', 'prescriptions': {}}"
        
        # Mock 401 unauthorized response (for when token is lost)
        mock_unauthorized_response = MagicMock()
        mock_unauthorized_response.status_code = 401
        mock_unauthorized_response.text = "Unauthorized"
        
        # Configure mock to return appropriate responses
        def mock_post_side_effect(url, *args, **kwargs):
            if '/login' in url:
                return mock_login_response
            return MagicMock(status_code=200)
        
        def mock_request_side_effect(method, url, *args, **kwargs):
            if '/dashboard' in url:
                # Check if Authorization header has a valid token
                headers = kwargs.get('headers', {})
                auth_header = headers.get('Authorization', '')
                if 'Bearer test-jwt-token-12345' in auth_header:
                    return mock_dashboard_response
                else:
                    return mock_unauthorized_response
            return MagicMock(status_code=200)
        
        mock_post.side_effect = mock_post_side_effect
        mock_request.side_effect = mock_request_side_effect
        
        yield {
            'post': mock_post,
            'get': mock_get,
            'request': mock_request
        }


class TestBugConditionExploration:
    """
    Property 1: Fault Condition - JWT Token Persistence Across Navigation
    
    Test that JWT tokens should be stored in user-specific sessions, not app.config.
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS (this is correct - it proves the bug exists)
    """
    
    def test_bug_token_stored_in_app_config_not_session(self, client, mock_api):
        """
        Test Case 1: Token Storage Location Bug
        
        Demonstrates that tokens are incorrectly stored in app.config['token'] instead of session['token'].
        This is the ROOT CAUSE of the bug.
        
        EXPECTED ON UNFIXED CODE: FAILS - token is in app.config, not in session
        EXPECTED ON FIXED CODE: PASSES - token is in session, not in app.config
        """
        # Login with valid credentials
        with client.session_transaction() as sess:
            # Session should be empty before login
            initial_session_token = sess.get('token', None)
        
        login_response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword'
        }, follow_redirects=False)
        
        assert login_response.status_code in [302, 200], "Login should succeed"
        
        # Check where the token is stored
        with client.session_transaction() as sess:
            session_token = sess.get('token', None)
        
        app_config_token = flask_app.config.get('token', '')
        
        # ASSERTION: Token should be in session, NOT in app.config
        # On UNFIXED code, this will FAIL because token is in app.config
        assert session_token is not None and session_token != '', \
            f"Token should be stored in session['token'], but session['token'] = {session_token}. " \
            f"This failure indicates the bug exists: token is stored in app.config['{app_config_token}'] instead."
        
        # On fixed code, app.config['token'] should not be used
        # On unfixed code, app.config['token'] will have the token
        print(f"\nDEBUG - Token storage locations:")
        print(f"  session['token'] = {session_token}")
        print(f"  app.config['token'] = {app_config_token}")
    
    
    def test_concurrent_users_token_overwrite(self, mock_api):
        """
        Test Case 2: Concurrent User Token Overwrite
        
        Demonstrates that when multiple users log in, their tokens overwrite each other
        in app.config['token'] because it's application-level storage.
        
        EXPECTED ON UNFIXED CODE: FAILS - User B's token overwrites User A's token
        EXPECTED ON FIXED CODE: PASSES - Each user has their own session token
        """
        # Reset app.config
        flask_app.config['token'] = ""
        flask_app.config['email'] = ""
        
        # Create two separate test clients to simulate concurrent users
        flask_app.config['TESTING'] = True
        client_a = flask_app.test_client()
        client_b = flask_app.test_client()
        
        # Mock different tokens for different users
        with patch('requests.post') as mock_post:
            def mock_login(url, *args, **kwargs):
                if '/login' in url:
                    # Get email from form data
                    data = args[0] if args else {}
                    email = data.get('email', '')
                    
                    mock_response = MagicMock()
                    mock_response.headers = {
                        'authentication': 'success',
                        'token': f'token-for-{email}'
                    }
                    mock_response.status_code = 200
                    return mock_response
                return MagicMock(status_code=200)
            
            mock_post.side_effect = mock_login
            
            # User A logs in
            login_a = client_a.post('/login', data={
                'email': 'userA@example.com',
                'password': 'passwordA'
            }, follow_redirects=False)
            
            assert login_a.status_code in [302, 200], "User A login should succeed"
            
            # Check User A's token in app.config (on unfixed code)
            token_after_a = flask_app.config.get('token', '')
            print(f"\nDEBUG - After User A login: app.config['token'] = {token_after_a}")
            
            # User B logs in (this should overwrite app.config['token'] on unfixed code)
            login_b = client_b.post('/login', data={
                'email': 'userB@example.com',
                'password': 'passwordB'
            }, follow_redirects=False)
            
            assert login_b.status_code in [302, 200], "User B login should succeed"
            
            # Check token after User B login
            token_after_b = flask_app.config.get('token', '')
            print(f"DEBUG - After User B login: app.config['token'] = {token_after_b}")
        
        # Check if each client has its own session token (fixed code)
        # or if they share app.config['token'] (unfixed code)
        with client_a.session_transaction() as sess_a:
            session_token_a = sess_a.get('token', None)
        
        with client_b.session_transaction() as sess_b:
            session_token_b = sess_b.get('token', None)
        
        # ASSERTION: Each user should have their own session token
        # On UNFIXED code, this will FAIL because tokens are in shared app.config
        assert session_token_a is not None and 'userA' in str(session_token_a), \
            f"User A should have their own session token containing 'userA'. " \
            f"Got session_token_a={session_token_a}. " \
            f"This failure indicates the bug exists: tokens are stored in shared app.config instead of separate sessions."
        
        assert session_token_b is not None and 'userB' in str(session_token_b), \
            f"User B should have their own session token containing 'userB'. " \
            f"Got session_token_b={session_token_b}. " \
            f"This failure indicates the bug exists: tokens are stored in shared app.config instead of separate sessions."
    
    
    @given(
        user_count=st.integers(min_value=2, max_value=4)
    )
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_session_isolation_for_concurrent_users(self, mock_api, user_count):
        """
        Property-Based Test: Session Isolation for Concurrent Users
        
        For ANY number of concurrent users, each user should have their own isolated session token.
        
        EXPECTED ON UNFIXED CODE: Test FAILS - all users share the same app.config['token']
        EXPECTED ON FIXED CODE: Test PASSES - each user has their own session['token']
        """
        # Reset app.config
        flask_app.config['token'] = ""
        flask_app.config['TESTING'] = True
        
        # Create multiple test clients
        clients = [flask_app.test_client() for _ in range(user_count)]
        
        # Mock login to return unique tokens
        with patch('requests.post') as mock_post:
            def mock_login(url, *args, **kwargs):
                if '/login' in url:
                    data = args[0] if args else {}
                    email = data.get('email', '')
                    
                    mock_response = MagicMock()
                    mock_response.headers = {
                        'authentication': 'success',
                        'token': f'unique-token-{email}'
                    }
                    mock_response.status_code = 200
                    return mock_response
                return MagicMock(status_code=200)
            
            mock_post.side_effect = mock_login
            
            # Each user logs in
            for i, client in enumerate(clients):
                login_response = client.post('/login', data={
                    'email': f'user{i}@example.com',
                    'password': f'password{i}'
                }, follow_redirects=False)
                
                assert login_response.status_code in [302, 200], f"User {i} login should succeed"
        
        # Check that each client has its own session token
        session_tokens = []
        for i, client in enumerate(clients):
            with client.session_transaction() as sess:
                token = sess.get('token', None)
                session_tokens.append(token)
        
        # ASSERTION: Each user should have a unique session token
        # On UNFIXED code, this will FAIL because all users share app.config['token']
        for i, token in enumerate(session_tokens):
            assert token is not None, \
                f"User {i} should have a session token. " \
                f"This failure indicates the bug exists: tokens are not stored in user sessions."
            
            assert f'user{i}' in str(token), \
                f"User {i} should have their own unique token containing 'user{i}'. Got {token}. " \
                f"This counterexample demonstrates the bug: tokens are shared in app.config instead of isolated in sessions."


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-s'])
