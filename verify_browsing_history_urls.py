#!/usr/bin/env python
"""Quick verification script for browsing history URLs"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_url_exists(url_path, method='GET'):
    """Test if a URL exists and returns a response (not 404)"""
    try:
        if method == 'GET':
            response = requests.get(f"{BASE_URL}{url_path}", timeout=2)
        elif method == 'POST':
            response = requests.post(f"{BASE_URL}{url_path}", json={}, timeout=2)
        elif method == 'DELETE':
            response = requests.delete(f"{BASE_URL}{url_path}", timeout=2)
        
        if response.status_code == 404:
            return False, f"404 Not Found"
        elif response.status_code == 401:
            return True, f"401 Unauthorized (URL exists but requires auth)"
        elif response.status_code in [200, 201, 400]:
            return True, f"{response.status_code} (URL exists)"
        else:
            return True, f"{response.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "Server not running - start with: python manage.py runserver"
    except Exception as e:
        return None, f"Error: {str(e)}"

if __name__ == '__main__':
    print("=" * 70)
    print("Verifying Browsing History API Endpoints")
    print("=" * 70)
    print()
    
    endpoints = [
        ('GET', '/browsing-history/', 'Get browsing history'),
        ('GET', '/browsing-history/categories/', 'Get browsed categories'),
        ('POST', '/browsing-history/track/', 'Track browsing history'),
        ('DELETE', '/browsing-history/clear/', 'Clear browsing history'),
    ]
    
    all_ok = True
    for method, path, description in endpoints:
        result, message = test_url_exists(path, method)
        if result is True:
            print(f"[OK] {method:6} {path:35} - {description}")
            print(f"     Status: {message}")
        elif result is False:
            print(f"[FAIL] {method:6} {path:35} - {description}")
            print(f"     Error: {message}")
            all_ok = False
        else:
            print(f"[ERROR] {method:6} {path:35} - {description}")
            print(f"     {message}")
            if "Server not running" in message:
                all_ok = None
                break
    
    print()
    print("=" * 70)
    if all_ok is True:
        print("[SUCCESS] All endpoints are accessible!")
        print("Note: 401 errors are expected if you're not authenticated.")
    elif all_ok is False:
        print("[FAIL] Some endpoints returned 404 - server may need restart")
        print("Try: python manage.py runserver")
    else:
        print("[WARNING] Server connection issue")
    print("=" * 70)

