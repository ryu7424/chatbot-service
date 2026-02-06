import pytest
import requests
import json

BASE_URL = "http://localhost:8000/v1/chat/completions"

def query_api(user, question):
    payload = {
        "model": "rag-agent",
        "messages": [{"role": "user", "content": question}],
        "user": user
    }
    try:
        response = requests.post(BASE_URL, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return str(e)

def test_e2e_security_leakage():
    """
    Scenario: User 'intern' tries to access 'Secret X' info (restricted to execs).
    """
    question = "Tell me about Project Secret X."
    
    # 1. Intern (Unauthorized)
    answer_intern = query_api("intern", question)
    print(f"Intern Answer: {answer_intern}")
    
    assert "top secret" not in answer_intern.lower()
    assert "cannot find" in answer_intern.lower() or "not found" in answer_intern.lower()

def test_e2e_security_access():
    """
    Scenario: User 'exec' tries to access 'Secret X' info.
    """
    question = "Tell me about Project Secret X."
    
    # 2. Exec (Authorized)
    answer_exec = query_api("exec", question)
    print(f"Exec Answer: {answer_exec}")
    
    assert "top secret" in answer_exec.lower()

if __name__ == "__main__":
    # Manual run support
    try:
        test_e2e_security_leakage()
        print("PASS: Security Leakage Test")
        test_e2e_security_access()
        print("PASS: Security Access Test")
    except AssertionError as e:
        print(f"FAIL: {e}")
