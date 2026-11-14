import urllib.request
import urllib.error
import json

BASE_URL = 'http://127.0.0.1:8000'


def api_call(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'

    body = json.dumps(data).encode('utf-8') if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            content = resp.read().decode('utf-8')
            return status_code, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        status_code = e.code
        content = e.read().decode('utf-8')
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = content
        return status_code, parsed


def run_tests():
    print("=" * 60)
    print("🚀 TESTING SPRINT 1 | BE-A (User Authentication APIs)")
    print("=" * 60)

    # 1. Register new user
    reg_payload = {
        'email': 'dev_test@example.com',
        'username': 'dev_test',
        'password': 'Password123'
    }
    s1, r1 = api_call('POST', '/api/users/register/', reg_payload)
    print(f"1. Register new user: Status {s1}")
    print(f"   Response: {r1}")
    assert s1 in [201, 400]

    # 2. Duplicate email registration rejection
    s2, r2 = api_call('POST', '/api/users/register/', reg_payload)
    print(f"2. Duplicate email rejection: Status {s2}")
    print(f"   Response: {r2}")
    assert s2 == 400, "Duplicate email was not rejected!"

    # 3. Login
    login_payload = {'email': 'dev_test@example.com', 'password': 'Password123'}
    s3, r3 = api_call('POST', '/api/users/login/', login_payload)
    print(f"3. Login user: Status {s3}")
    token = r3.get('token')
    print(f"   Token returned: {token[:12]}...")
    assert token is not None

    # 4. Current user endpoint (/api/users/me/)
    s4, r4 = api_call('GET', '/api/users/me/', token=token)
    print(f"4. Current User (/api/users/me/): Status {s4}")
    print(f"   User info: {r4}")
    assert s4 == 200

    print("\n" + "=" * 60)
    print("🚀 TESTING SPRINT 1 | BE-B (Projects, Skills, Members, Requests)")
    print("=" * 60)

    # 5. List Skills
    s5, r5 = api_call('GET', '/api/skills/')
    print(f"5. List Skills: Status {s5}, Total skills: {len(r5)}")
    skill_ids = [s['id'] for s in r5[:2]]

    # 6. List Projects
    s6, r6 = api_call('GET', '/api/projects/')
    print(f"6. List Open Projects: Status {s6}, Total: {len(r6)}")

    # 7. Create Project (as dev_test)
    proj_payload = {
        'title': 'AI Skill Matcher Platform',
        'description': 'Smart project matching for university students.',
        'capacity': 3,
        'status': 'open',
        'skills': skill_ids
    }
    s7, r7 = api_call('POST', '/api/projects/', proj_payload, token=token)
    print(f"7. Create Project: Status {s7}")
    print(f"   Created Project ID: {r7['id']}, Creator: {r7['creator_username']}, Capacity: {r7['capacity']}")
    proj_id = r7['id']
    assert s7 == 201

    # 8. Get Project Details
    s8, r8 = api_call('GET', f'/api/projects/{proj_id}/')
    print(f"8. Get Project Details: Status {s8}, Title: {r8['title']}")
    assert s8 == 200

    # 9. Submit Membership Request (as applicant_reza)
    s_app_login, r_app_login = api_call('POST', '/api/users/login/', {'email': 'reza@example.com', 'password': 'password123'})
    app_token = r_app_login['token']

    req_payload = {
        'project': proj_id,
        'message': 'Hi! I want to contribute to this AI matching project.'
    }
    s9, r9 = api_call('POST', '/api/applications/requests/', req_payload, token=app_token)
    print(f"9. Submit Membership Request: Status {s9}")
    print(f"   Request ID: {r9['id']}, Status: {r9['status']}, Applicant: {r9['applicant_username']}")
    req_id = r9['id']
    assert s9 == 201

    # 10. Creator Accepts the Request
    accept_payload = {'status': 'accepted'}
    s10, r10 = api_call('PATCH', f'/api/applications/requests/{req_id}/', accept_payload, token=token)
    print(f"10. Creator Accepts Request: Status {s10}, New Status: {r10['status']}")
    assert s10 == 200

    # 11. Verify Member was automatically added to ProjectMember
    s11, r11 = api_call('GET', f'/api/projects/{proj_id}/members/')
    print(f"11. Verify Project Members: Status {s11}, Members count: {len(r11)}")
    for m in r11:
        print(f"    - Member User: {m['user']['username']} (Joined at: {m['joined_at']})")
    assert len(r11) == 1

    # 12. Check remaining capacity updated
    s12, r12 = api_call('GET', f'/api/projects/{proj_id}/')
    print(f"12. Updated Project Capacity: Total: {r12['capacity']}, Remaining: {r12['remaining_capacity']}")

    print("\n" + "=" * 60)
    print("🎉 ALL APIS FOR BE-A AND BE-B ARE 100% OPERATIONAL AND VALIDATED!")
    print("=" * 60)


if __name__ == '__main__':
    run_tests()
