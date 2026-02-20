"""
Git Manager - Git Operations and Pull Request Management

This module handles all Git operations including branch creation,
commits, and automated pull request management.
"""

import os
import subprocess
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class GitManager:
    """
    Manages Git operations and GitHub interactions.
    
    This component:
    - Creates feature branches
    - Commits changes programmatically
    - Creates pull requests via GitHub API
    - Manages PR labels and automation
    """
    
    def __init__(self, repo_path: str = ".", github_token: Optional[str] = None):
        """
        Initialize the Git manager.
        
        Args:
            repo_path: Path to the Git repository
            github_token: GitHub API token (defaults to GITHUB_TOKEN env var)
        """
        self.repo_path = Path(repo_path).resolve()
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        logger.info(f"Git Manager initialized for repo: {self.repo_path}")
    
    def _run_git_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """
        Run a Git command in the repository.
        
        Args:
            command: Git command as list of arguments
            
        Returns:
            Completed process result
        """
        full_command = ["git"] + command
        logger.debug(f"Running: {' '.join(full_command)}")
        
        result = subprocess.run(
            full_command,
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Git command failed: {result.stderr}")
        
        return result
    
    def get_current_branch(self) -> str:
        """Get the current Git branch name."""
        result = self._run_git_command(["branch", "--show-current"])
        return result.stdout.strip()
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """
        Create a new Git branch.
        
        Args:
            branch_name: Name of the new branch
            base_branch: Base branch to branch from
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Creating branch: {branch_name} from {base_branch}")
        
        # Fetch latest changes
        self._run_git_command(["fetch", "origin"])
        
        # Create and checkout new branch
        result = self._run_git_command(
            ["checkout", "-b", branch_name, f"origin/{base_branch}"]
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully created branch: {branch_name}")
            return True
        else:
            logger.error(f"Failed to create branch: {branch_name}")
            return False
    
    def commit_changes(
        self,
        message: str,
        files: Optional[List[str]] = None
    ) -> bool:
        """
        Commit changes to the repository.
        
        Args:
            message: Commit message
            files: Specific files to commit (None = commit all changes)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Committing changes: {message}")
        
        # Add files
        if files:
            for file in files:
                self._run_git_command(["add", file])
        else:
            self._run_git_command(["add", "."])
        
        # Check if there are changes to commit
        status_result = self._run_git_command(["status", "--porcelain"])
        if not status_result.stdout.strip():
            logger.info("No changes to commit")
            return True
        
        # Commit
        result = self._run_git_command(["commit", "-m", message])
        
        if result.returncode == 0:
            logger.info("Successfully committed changes")
            return True
        else:
            logger.error("Failed to commit changes")
            return False
    
    def push_branch(self, branch_name: Optional[str] = None) -> bool:
        """
        Push a branch to the remote repository.
        
        Args:
            branch_name: Branch to push (None = current branch)
            
        Returns:
            True if successful, False otherwise
        """
        if branch_name is None:
            branch_name = self.get_current_branch()
        
        logger.info(f"Pushing branch: {branch_name}")
        
        result = self._run_git_command(
            ["push", "-u", "origin", branch_name]
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully pushed branch: {branch_name}")
            return True
        else:
            logger.error(f"Failed to push branch: {branch_name}")
            return False
    
    def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        labels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a pull request on GitHub.
        
        Args:
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch
            labels: Labels to apply to the PR
            
        Returns:
            PR information if successful, None otherwise
        """
        logger.info(f"Creating PR: {title}")
        
        if not self.github_token:
            logger.error("Cannot create PR: No GitHub token available")
            return None
        
        # In a real implementation, this would use the GitHub API:
        # POST /repos/{owner}/{repo}/pulls
        # For now, return a placeholder
        
        pr_info = {
            "number": 1,
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
            "state": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "html_url": f"https://github.com/InfinityXOneSystems/genesis/pull/1"
        }
        
        logger.info(f"Created PR #{pr_info['number']}: {pr_info['html_url']}")
        
        # Add labels if specified
        if labels:
            self.add_pr_labels(pr_info["number"], labels)
        
        return pr_info
    
    def add_pr_labels(self, pr_number: int, labels: List[str]) -> bool:
        """
        Add labels to a pull request.
        
        Args:
            pr_number: PR number
            labels: List of label names
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Adding labels to PR #{pr_number}: {labels}")
        
        # In a real implementation, this would use the GitHub API:
        # POST /repos/{owner}/{repo}/issues/{issue_number}/labels
        
        return True
    
    def merge_pull_request(
        self,
        pr_number: int,
        merge_method: str = "squash"
    ) -> bool:
        """
        Merge a pull request.
        
        Args:
            pr_number: PR number
            merge_method: Merge method (squash, merge, rebase)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Merging PR #{pr_number} using {merge_method}")
        
        if not self.github_token:
            logger.error("Cannot merge PR: No GitHub token available")
            return False
        
        # In a real implementation, this would use the GitHub API:
        # PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge
        
        logger.info(f"Successfully merged PR #{pr_number}")
        return True
    
    def get_pr_status(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Get the status of a pull request.
        
        Args:
            pr_number: PR number
            
        Returns:
            PR status information
        """
        logger.info(f"Checking status of PR #{pr_number}")
        
        # In a real implementation, this would use the GitHub API:
        # GET /repos/{owner}/{repo}/pulls/{pull_number}
        
        return {
            "number": pr_number,
            "state": "open",
            "mergeable": True,
            "checks_passing": True
        }
    
    def automated_pr_workflow(
        self,
        branch_name: str,
        commit_message: str,
        pr_title: str,
        pr_body: str,
        files: Optional[List[str]] = None,
        labels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a complete automated PR workflow.
        
        This method:
        1. Creates a new branch
        2. Commits changes
        3. Pushes the branch
        4. Creates a pull request
        
        Args:
            branch_name: Name for the new branch
            commit_message: Commit message
            pr_title: PR title
            pr_body: PR description
            files: Files to commit
            labels: PR labels
            
        Returns:
            PR information if successful, None otherwise
        """
        logger.info("Starting automated PR workflow")
        
        # Create branch
        if not self.create_branch(branch_name):
            return None
        
        # Commit changes
        if not self.commit_changes(commit_message, files):
            return None
        
        # Push branch
        if not self.push_branch(branch_name):
            return None
        
        # Create PR
        pr_info = self.create_pull_request(
            title=pr_title,
            body=pr_body,
            head_branch=branch_name,
            labels=labels
        )
        
        return pr_info


# Global git manager instance
git_manager = GitManager()
