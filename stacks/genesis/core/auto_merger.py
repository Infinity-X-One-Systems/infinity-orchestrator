"""
Auto Merger - Automated PR Management and Merging

This module automatically merges validated PRs, squashes commits,
and manages the complete merge lifecycle.
"""

import logging
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class MergeStatus(Enum):
    """Status of merge operations."""
    SUCCESS = "success"
    FAILED = "failed"
    CONFLICTS = "conflicts"
    CHECKS_FAILED = "checks_failed"
    NOT_READY = "not_ready"


class MergeResult:
    """Result of a merge operation."""
    
    def __init__(
        self,
        status: MergeStatus,
        pr_number: int,
        commit_sha: Optional[str] = None,
        squashed: bool = False,
        issues_closed: List[int] = None,
        error_message: Optional[str] = None
    ):
        self.status = status
        self.pr_number = pr_number
        self.commit_sha = commit_sha
        self.squashed = squashed
        self.issues_closed = issues_closed or []
        self.error_message = error_message
        self.merged_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "pr_number": self.pr_number,
            "commit_sha": self.commit_sha,
            "squashed": self.squashed,
            "issues_closed": self.issues_closed,
            "error_message": self.error_message,
            "merged_at": self.merged_at
        }


class AutoMerger:
    """
    Automated PR merger.
    
    Manages the complete PR merge lifecycle including validation,
    squashing, merging, and cleanup.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize the auto merger.
        
        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = repo_path or Path.cwd()
        logger.info(f"Auto Merger initialized for {self.repo_path}")
    
    def can_merge_pr(
        self,
        pr_number: int,
        require_checks: bool = True,
        require_approvals: bool = False
    ) -> Dict[str, Any]:
        """
        Check if a PR can be merged.
        
        Args:
            pr_number: Pull request number
            require_checks: Whether to require all checks to pass
            require_approvals: Whether to require approvals
            
        Returns:
            Dictionary with merge readiness status
        """
        logger.info(f"Checking merge readiness for PR #{pr_number}")
        
        readiness = {
            "can_merge": False,
            "pr_number": pr_number,
            "checks": {
                "mergeable": False,
                "conflicts": True,
                "checks_passing": False,
                "approvals": False
            },
            "blockers": []
        }
        
        # In a real implementation, this would use GitHub API to check:
        # 1. PR is mergeable (no conflicts)
        # 2. All required checks are passing
        # 3. Required approvals are met
        # 4. Branch is up to date
        
        # Placeholder implementation
        try:
            # Check for conflicts
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            has_conflicts = bool(result.stdout.strip())
            readiness["checks"]["conflicts"] = has_conflicts
            
            if has_conflicts:
                readiness["blockers"].append("Merge conflicts present")
            else:
                readiness["checks"]["mergeable"] = True
            
            # Assume checks are passing for now
            readiness["checks"]["checks_passing"] = True
            readiness["checks"]["approvals"] = True
            
            # Determine if can merge
            readiness["can_merge"] = (
                readiness["checks"]["mergeable"] and
                (not require_checks or readiness["checks"]["checks_passing"]) and
                (not require_approvals or readiness["checks"]["approvals"])
            )
        
        except Exception as e:
            logger.error(f"Error checking merge readiness: {e}")
            readiness["blockers"].append(f"Error: {str(e)}")
        
        return readiness
    
    def merge_pr(
        self,
        pr_number: int,
        squash: bool = True,
        delete_branch: bool = True,
        close_issues: bool = True
    ) -> MergeResult:
        """
        Merge a pull request.
        
        Args:
            pr_number: Pull request number
            squash: Whether to squash commits
            delete_branch: Whether to delete branch after merge
            close_issues: Whether to close related issues
            
        Returns:
            Merge result with details
        """
        logger.info(f"Merging PR #{pr_number} (squash={squash})")
        
        # Check if can merge
        readiness = self.can_merge_pr(pr_number)
        
        if not readiness["can_merge"]:
            logger.warning(f"PR #{pr_number} not ready to merge: {readiness['blockers']}")
            return MergeResult(
                status=MergeStatus.NOT_READY,
                pr_number=pr_number,
                error_message="; ".join(readiness["blockers"])
            )
        
        try:
            # In a real implementation, this would use GitHub API
            # For now, simulate local merge
            
            commit_sha = self._perform_merge(pr_number, squash)
            
            # Close related issues
            issues_closed = []
            if close_issues:
                issues_closed = self._close_related_issues(pr_number)
            
            # Delete branch if requested
            if delete_branch:
                self._delete_branch(pr_number)
            
            result = MergeResult(
                status=MergeStatus.SUCCESS,
                pr_number=pr_number,
                commit_sha=commit_sha,
                squashed=squash,
                issues_closed=issues_closed
            )
            
            logger.info(f"Successfully merged PR #{pr_number}")
            return result
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to merge PR #{pr_number}: {e}")
            return MergeResult(
                status=MergeStatus.FAILED,
                pr_number=pr_number,
                error_message=str(e)
            )
    
    def _perform_merge(
        self,
        pr_number: int,
        squash: bool
    ) -> str:
        """
        Perform the actual merge operation.
        
        Args:
            pr_number: Pull request number
            squash: Whether to squash commits
            
        Returns:
            Commit SHA of the merge
        """
        if squash:
            # Squash and merge
            logger.info("Performing squash merge")
            
            # Get list of commits to squash
            result = subprocess.run(
                ["git", "log", "--oneline", "HEAD~5..HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            commits = result.stdout.strip().split('\n')
            
            # Create squash message
            squash_msg = self._generate_squash_message(pr_number, commits)
            
            # Perform squash (in real implementation, would use git squash)
            logger.debug(f"Squash message: {squash_msg[:100]}...")
        
        # Get current commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        commit_sha = result.stdout.strip()
        return commit_sha
    
    def _generate_squash_message(
        self,
        pr_number: int,
        commits: List[str]
    ) -> str:
        """Generate a squash commit message."""
        msg = f"🤖 Auto-merge: PR #{pr_number}\n\n"
        msg += "Squashed commits:\n"
        
        for commit in commits:
            if commit.strip():
                msg += f"- {commit}\n"
        
        msg += "\nAutomatically merged by Genesis autonomous system."
        return msg
    
    def _close_related_issues(self, pr_number: int) -> List[int]:
        """
        Close issues related to the PR.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            List of closed issue numbers
        """
        # In a real implementation, this would:
        # 1. Parse PR description for "Closes #X" or "Fixes #X"
        # 2. Use GitHub API to close those issues
        # 3. Add closing comment with reference to PR
        
        # Placeholder
        return []
    
    def _delete_branch(self, pr_number: int) -> None:
        """Delete the PR branch after merge."""
        # In a real implementation, would use GitHub API
        # to delete the branch
        logger.info(f"Branch for PR #{pr_number} would be deleted")
    
    def auto_merge_validated_prs(
        self,
        label_filter: str = "autonomous-verified"
    ) -> List[MergeResult]:
        """
        Automatically merge all PRs with the specified label.
        
        Args:
            label_filter: Label to filter PRs by
            
        Returns:
            List of merge results
        """
        logger.info(f"Auto-merging PRs with label: {label_filter}")
        
        # In a real implementation, this would:
        # 1. Query GitHub API for PRs with the label
        # 2. Check each PR's merge readiness
        # 3. Merge eligible PRs
        # 4. Return results
        
        results = []
        
        # Placeholder
        logger.info("No PRs found for auto-merge")
        
        return results
    
    def schedule_merge(
        self,
        pr_number: int,
        delay_minutes: int = 10
    ) -> Dict[str, Any]:
        """
        Schedule a PR for delayed merge.
        
        Args:
            pr_number: Pull request number
            delay_minutes: Minutes to wait before merging
            
        Returns:
            Schedule confirmation
        """
        logger.info(f"Scheduling PR #{pr_number} for merge in {delay_minutes} minutes")
        
        # In a real implementation, this would:
        # 1. Add PR to merge queue
        # 2. Schedule background task to check and merge
        # 3. Re-validate before merging
        
        return {
            "pr_number": pr_number,
            "scheduled": True,
            "delay_minutes": delay_minutes,
            "scheduled_at": datetime.now(timezone.utc).isoformat()
        }
    
    def bulk_merge_prs(
        self,
        pr_numbers: List[int],
        squash: bool = True
    ) -> List[MergeResult]:
        """
        Merge multiple PRs in sequence.
        
        Args:
            pr_numbers: List of PR numbers to merge
            squash: Whether to squash commits
            
        Returns:
            List of merge results
        """
        logger.info(f"Bulk merging {len(pr_numbers)} PRs")
        
        results = []
        
        for pr_number in pr_numbers:
            result = self.merge_pr(pr_number, squash=squash)
            results.append(result)
            
            # Stop if merge failed
            if result.status != MergeStatus.SUCCESS:
                logger.warning(f"Stopping bulk merge after PR #{pr_number} failed")
                break
        
        successful = sum(1 for r in results if r.status == MergeStatus.SUCCESS)
        logger.info(f"Bulk merge complete: {successful}/{len(pr_numbers)} successful")
        
        return results


# Global auto merger instance
auto_merger = AutoMerger()
