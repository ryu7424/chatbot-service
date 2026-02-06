from locust import HttpUser, task, between
import json

class RAGUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def search_general(self):
        # Regular search
        self.client.post("/v1/chat/completions", json={
            "model": "rag-agent",
            "messages": [{"role": "user", "content": "How to fix login error?"}],
            "user": "dev"
        })

    @task(1)
    def search_secure(self):
        # Search demanding secure docs
        self.client.post("/v1/chat/completions", json={
            "model": "rag-agent",
            "messages": [{"role": "user", "content": "Project Secret X status"}],
            "user": "exec"
        })
