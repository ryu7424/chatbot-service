from typing import List, Dict, Any
from langchain_core.documents import Document
# from langchain_community.document_loaders import ConfluenceLoader, JiraLoader
import os

class SecureConfluenceLoader:
    def __init__(self, url: str, username: str, api_key: str):
        self.url = url
        self.username = username
        self.api_key = api_key
        # In real impl, we initialize the official loader here
        # self.loader = ConfluenceLoader(...)

    def load(self, space_key: str = None, page_ids: List[str] = None) -> List[Document]:
        """
        Mock implementation that returns documents with ACL metadata.
        In production, this would make API calls to fetch permissions.
        """
        # Mock data representing what we would get from Confluence API
        mock_pages = [
            {
                "id": "1001",
                "title": "Employee Handbook",
                "body": "Welcome to the company. Here are the rules...",
                "space": "HR",
                "url": f"{self.url}/display/HR/Handbook",
                # Publicly readable by all employees
                "permissions": ["group:confluence-users"] 
            },
            {
                "id": "1002",
                "title": "Project Secret X Launch Plan",
                "body": "Top secret launch details for Project X...",
                "space": "RD",
                "url": f"{self.url}/display/RD/Project+Secret+X",
                # Restricted to executives and R&D team
                "permissions": ["group:executives", "group:rd-team"]
            }
        ]

        documents = []
        for page in mock_pages:
            # FILTER: If user asks for specific space, filter here
            if space_key and page["space"] != space_key:
                continue
                
            metadata = {
                "source": "confluence",
                "source_id": page["id"],
                "title": page["title"],
                "url": page["url"],
                "space_key": page["space"],
                # IMPORTANT: Mapping API permissions to our schema
                "allowed_groups": page["permissions"],
                "allowed_users": [] # Example if we had specific user grants
            }
            
            doc = Document(page_content=page["body"], metadata=metadata)
            documents.append(doc)
            
        return documents

class SecureJiraLoader:
    def __init__(self, url: str, username: str, api_key: str):
        self.url = url
        
    def load(self, jql: str) -> List[Document]:
        """
        Mock implementation for Jira issues with Project Role mapping.
        """
        # Mock issues
        mock_issues = [
            {
                "key": "JIRA-101",
                "summary": "Login page returns 500 error",
                "description": "Steps to reproduce...",
                "project": "SUP", # Support Project
                "status": "In Progress",
                # Standard permissions for Support project
                "permissions": ["group:jira-software-users"]
            },
            {
                "key": "HR-55",
                "summary": "Salary adjustment for Q1",
                "description": "Confidential salary data...",
                "project": "HR",
                "status": "Done",
                # Sensitive HR data
                "permissions": ["group:hr-administrators"]
            }
        ]
        
        documents = []
        for issue in mock_issues:
            content = f"Summary: {issue['summary']}\nDescription: {issue['description']}\nStatus: {issue['status']}"
            
            metadata = {
                "source": "jira",
                "source_id": issue["key"],
                "title": issue["key"] + ": " + issue["summary"],
                "url": f"{self.url}/browse/{issue['key']}",
                "project_key": issue["project"],
                "allowed_groups": issue["permissions"],
                "allowed_users": []
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
            
        return documents
