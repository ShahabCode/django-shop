import secrets


def generate_code():
    return ''.join(secrets.choice('0123456789') for _ in range(6))


def code_match(entered_code: str, expected_code: str) -> bool:
    if not entered_code or not expected_code:
        return False
    return secrets.compare_digest(entered_code.encode(), expected_code.encode())


def clear_otp_session(request):
    sessions = ['phone', 'verification_code', 'verification_attempts', 'verification_expiry']
    for key in sessions:
        request.session.pop(key, None)