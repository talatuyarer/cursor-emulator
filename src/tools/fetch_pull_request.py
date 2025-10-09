import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..state.validators import ValidationError


class GitHubPRFetcher:
    """Fetches GitHub pull request data using GitHub API"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-PR-Fetcher/1.0"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_pr(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Fetch pull request data from GitHub API"""
        if not self.session:
            raise ValidationError("GitHubPRFetcher not properly initialized")
        
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 404:
                    raise ValidationError(f"Pull request #{pull_number} not found in {owner}/{repo}")
                elif response.status == 403:
                    raise ValidationError("GitHub API rate limit exceeded or insufficient permissions")
                elif response.status != 200:
                    raise ValidationError(f"GitHub API error: {response.status} - {await response.text()}")
                
                pr_data = await response.json()
                return await self._enrich_pr_data(owner, repo, pull_number, pr_data)
                
        except aiohttp.ClientError as e:
            raise ValidationError(f"Network error fetching PR: {str(e)}")
    
    async def _enrich_pr_data(self, owner: str, repo: str, pull_number: int, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich PR data with additional information"""
        enriched_data = {
            "number": pr_data.get("number"),
            "title": pr_data.get("title"),
            "body": pr_data.get("body"),
            "state": pr_data.get("state"),
            "merged": pr_data.get("merged"),
            "author": {
                "login": pr_data.get("user", {}).get("login"),
                "avatar_url": pr_data.get("user", {}).get("avatar_url"),
                "html_url": pr_data.get("user", {}).get("html_url")
            },
            "created_at": pr_data.get("created_at"),
            "updated_at": pr_data.get("updated_at"),
            "merged_at": pr_data.get("merged_at"),
            "closed_at": pr_data.get("closed_at"),
            "html_url": pr_data.get("html_url"),
            "diff_url": pr_data.get("diff_url"),
            "patch_url": pr_data.get("patch_url"),
            "labels": [label.get("name") for label in pr_data.get("labels", [])],
            "assignees": [assignee.get("login") for assignee in pr_data.get("assignees", [])],
            "reviewers": [reviewer.get("login") for reviewer in pr_data.get("requested_reviewers", [])],
            "commits": pr_data.get("commits", 0),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
            "changed_files": pr_data.get("changed_files", 0),
            "draft": pr_data.get("draft", False),
            "mergeable": pr_data.get("mergeable"),
            "mergeable_state": pr_data.get("mergeable_state"),
            "head": {
                "ref": pr_data.get("head", {}).get("ref"),
                "sha": pr_data.get("head", {}).get("sha"),
                "repo": pr_data.get("head", {}).get("repo", {}).get("full_name")
            },
            "base": {
                "ref": pr_data.get("base", {}).get("ref"),
                "sha": pr_data.get("base", {}).get("sha"),
                "repo": pr_data.get("base", {}).get("repo", {}).get("full_name")
            }
        }
        
        # Fetch additional data
        try:
            enriched_data["files"] = await self._fetch_pr_files(owner, repo, pull_number)
            enriched_data["comments"] = await self._fetch_pr_comments(owner, repo, pull_number)
        except Exception as e:
            # Don't fail the entire request if additional data fails
            enriched_data["files"] = []
            enriched_data["comments"] = []
            enriched_data["_fetch_errors"] = str(e)
        
        return enriched_data
    
    async def _fetch_pr_files(self, owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
        """Fetch list of files changed in the PR"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                files_data = await response.json()
                return [
                    {
                        "filename": file.get("filename"),
                        "status": file.get("status"),
                        "additions": file.get("additions", 0),
                        "deletions": file.get("deletions", 0),
                        "changes": file.get("changes", 0),
                        "blob_url": file.get("blob_url"),
                        "raw_url": file.get("raw_url"),
                        "contents_url": file.get("contents_url"),
                        "patch": file.get("patch", "")[:1000]  # Limit patch size
                    }
                    for file in files_data
                ]
            return []
    
    async def _fetch_pr_comments(self, owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
        """Fetch comments on the PR"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pull_number}/comments"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                comments_data = await response.json()
                return [
                    {
                        "id": comment.get("id"),
                        "body": comment.get("body"),
                        "author": comment.get("user", {}).get("login"),
                        "created_at": comment.get("created_at"),
                        "updated_at": comment.get("updated_at"),
                        "html_url": comment.get("html_url")
                    }
                    for comment in comments_data
                ]
            return []


def validate_pr_parameters(owner: str, repo: str, pull_number: int) -> None:
    """Validate PR fetch parameters"""
    if not owner or not isinstance(owner, str) or not owner.strip():
        raise ValidationError("Owner must be a non-empty string")
    
    if not repo or not isinstance(repo, str) or not repo.strip():
        raise ValidationError("Repository must be a non-empty string")
    
    if not isinstance(pull_number, int) or pull_number <= 0:
        raise ValidationError("Pull number must be a positive integer")
    
    # Basic validation for owner/repo format
    if "/" in owner or "/" in repo:
        raise ValidationError("Owner and repository names cannot contain '/'")
    
    if len(owner) > 100 or len(repo) > 100:
        raise ValidationError("Owner and repository names must be less than 100 characters")


async def fetch_pull_request(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch GitHub pull request data including metadata, files, and comments.
    
    Parameters:
        params: Dictionary containing:
            - owner: GitHub repository owner (required)
            - repo: GitHub repository name (required)
            - pull_number: Pull request number (required)
            - token: GitHub personal access token (optional)
    
    Returns:
        Dictionary with comprehensive PR data including:
        - Basic metadata (title, description, author, status)
        - Timestamps (created, updated, merged, closed)
        - Statistics (commits, additions, deletions, changed files)
        - Branch information (head and base)
        - Files changed in the PR
        - Comments on the PR
        - Labels, assignees, and reviewers
    """
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    required_fields = {"owner", "repo", "pull_number"}
    missing_fields = required_fields - set(params.keys())
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}")
    
    owner = params["owner"]
    repo = params["repo"]
    pull_number = params["pull_number"]
    token = params.get("token")
    
    # Validate parameters
    validate_pr_parameters(owner, repo, pull_number)
    
    try:
        async with GitHubPRFetcher(token) as fetcher:
            pr_data = await fetcher.fetch_pr(owner, repo, pull_number)
            
            return {
                "success": True,
                "pr": pr_data,
                "fetched_at": datetime.now().isoformat(),
                "source": f"github.com/{owner}/{repo}/pull/{pull_number}"
            }
            
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to fetch pull request: {str(e)}")
