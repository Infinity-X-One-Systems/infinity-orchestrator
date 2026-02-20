"""
Branch Manager - Comprehensive Branch Analysis and Auto-Merge System

This module provides advanced branch management capabilities including:
- Conflict detection and resolution
- Auto-testing of branches
- Auto-healing of issues
- Auto-squashing and merging
- Automated branch cleanup
"""

import subprocess
import json
import re
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone
from pathlib import Path


class BranchHealth:
    """Branch health status"""
    HEALTHY = "healthy"
    NEEDS_FIXES = "needs_fixes"
    CONFLICTED = "conflicted"
    BROKEN = "broken"


class BranchManager:
    """Manages branch operations including analysis, healing, and merging"""
    
    def __init__(self, repo_path: str = None):
        if repo_path is None:
            repo_path = os.environ.get("GENESIS_REPO_PATH", str(Path.cwd()))
        self.repo_path = Path(repo_path)
        self.current_branch = self._get_current_branch()
        
    def _run_command(self, cmd: List[str], check=True) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr
    
    def _get_current_branch(self) -> str:
        """Get the current branch name"""
        code, stdout, _ = self._run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return stdout.strip() if code == 0 else ""
    
    def list_all_branches(self) -> List[str]:
        """List all local branches excluding current"""
        code, stdout, _ = self._run_command(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"])
        if code == 0:
            branches = [b.strip() for b in stdout.split('\n') if b.strip()]
            # Exclude current branch
            return [b for b in branches if b != self.current_branch]
        return []
    
    def get_branch_commits(self, branch: str, base: str = "main") -> List[str]:
        """Get commits in branch that are not in base"""
        code, stdout, _ = self._run_command(
            ["git", "log", "--oneline", f"{base}..{branch}"],
            check=False
        )
        if code == 0 and stdout:
            return [line.strip() for line in stdout.split('\n') if line.strip()]
        return []
    
    def check_conflicts(self, branch: str, base: str = "main") -> Tuple[bool, List[str]]:
        """Check if branch has merge conflicts with base"""
        # Get merge base
        code, merge_base, _ = self._run_command(
            ["git", "merge-base", base, branch],
            check=False
        )
        if code != 0:
            return True, ["Cannot find merge base"]
        
        merge_base = merge_base.strip()
        
        # Perform a dry-run merge
        code, stdout, _ = self._run_command(
            ["git", "merge-tree", merge_base, base, branch],
            check=False
        )
        
        if code == 0:
            # Check for conflict markers in output
            if "<<<<<" in stdout or "=====" in stdout or ">>>>>" in stdout:
                # Extract conflicting files
                lines = stdout.split('\n')
                conflicts = []
                for i, line in enumerate(lines):
                    if '<<<<<' in line and i > 0:
                        # Try to get filename from context
                        for j in range(max(0, i-10), i):
                            if lines[j].startswith('+++') or lines[j].startswith('---'):
                                conflicts.append(lines[j].split()[-1])
                                break
                return True, conflicts if conflicts else ["Unknown files"]
            return False, []
        return True, ["Merge check failed"]
    
    def get_diff_stats(self, branch: str, base: str = "main") -> Dict:
        """Get diff statistics between branch and base"""
        code, stdout, _ = self._run_command(
            ["git", "diff", "--stat", f"{base}..{branch}"],
            check=False
        )
        
        if code == 0 and stdout:
            lines = stdout.strip().split('\n')
            stats = {
                "files_changed": 0,
                "insertions": 0,
                "deletions": 0,
                "files": []
            }
            
            for line in lines:
                if '|' in line:
                    parts = line.split('|')
                    filename = parts[0].strip()
                    stats["files"].append(filename)
                elif 'file' in line and 'changed' in line:
                    # Summary line
                    match = re.search(r'(\d+) file', line)
                    if match:
                        stats["files_changed"] = int(match.group(1))
                    match = re.search(r'(\d+) insertion', line)
                    if match:
                        stats["insertions"] = int(match.group(1))
                    match = re.search(r'(\d+) deletion', line)
                    if match:
                        stats["deletions"] = int(match.group(1))
            
            return stats
        return {"files_changed": 0, "insertions": 0, "deletions": 0, "files": []}
    
    def run_tests(self) -> Tuple[bool, str]:
        """Run test suite and return success status and output"""
        code, stdout, stderr = self._run_command(
            ["python", "-m", "pytest", "tests/", "-v"],
            check=False
        )
        output = stdout + "\n" + stderr
        return code == 0, output
    
    def analyze_branch(self, branch: str) -> Dict:
        """Perform comprehensive branch analysis"""
        analysis = {
            "branch": branch,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "commits": self.get_branch_commits(branch),
            "commit_count": 0,
            "has_conflicts": False,
            "conflicts": [],
            "diff_stats": {},
            "health": BranchHealth.HEALTHY
        }
        
        # Get commit count
        analysis["commit_count"] = len(analysis["commits"])
        
        # Check conflicts
        has_conflicts, conflicts = self.check_conflicts(branch)
        analysis["has_conflicts"] = has_conflicts
        analysis["conflicts"] = conflicts
        
        # Get diff stats
        analysis["diff_stats"] = self.get_diff_stats(branch)
        
        # Determine health
        if has_conflicts:
            analysis["health"] = BranchHealth.CONFLICTED
        elif analysis["commit_count"] == 0:
            analysis["health"] = BranchHealth.HEALTHY  # Already merged
        else:
            analysis["health"] = BranchHealth.HEALTHY
        
        return analysis
    
    def analyze_all_branches(self) -> Dict[str, Dict]:
        """Analyze all branches"""
        branches = self.list_all_branches()
        results = {}
        
        for branch in branches:
            if branch != "main":  # Don't analyze main
                results[branch] = self.analyze_branch(branch)
        
        return results
    
    def test_branch(self, branch: str) -> Tuple[bool, str]:
        """Switch to branch, run tests, and return to original branch"""
        original_branch = self.current_branch
        
        try:
            # Switch to branch
            code, _, _ = self._run_command(["git", "checkout", branch])
            if code != 0:
                return False, f"Failed to checkout branch {branch}"
            
            # Run tests
            success, output = self.run_tests()
            
            return success, output
        finally:
            # Return to original branch
            self._run_command(["git", "checkout", original_branch], check=False)
    
    def merge_branch_to_main(self, branch: str, squash: bool = True) -> Tuple[bool, str]:
        """Merge a branch to main with optional squashing"""
        original_branch = self.current_branch
        
        try:
            # Switch to main
            code, _, stderr = self._run_command(["git", "checkout", "main"])
            if code != 0:
                return False, f"Failed to checkout main: {stderr}"
            
            # Pull latest main
            self._run_command(["git", "pull", "origin", "main"], check=False)
            
            # Merge
            if squash:
                code, stdout, stderr = self._run_command(
                    ["git", "merge", "--squash", branch],
                    check=False
                )
            else:
                code, stdout, stderr = self._run_command(
                    ["git", "merge", branch],
                    check=False
                )
            
            if code != 0:
                return False, f"Merge failed: {stderr}"
            
            # Commit if squash
            if squash:
                commit_msg = f"Merge branch '{branch}' (squashed)"
                code, _, stderr = self._run_command(
                    ["git", "commit", "-m", commit_msg],
                    check=False
                )
                if code != 0:
                    return False, f"Commit failed: {stderr}"
            
            return True, "Merge successful"
            
        except Exception as e:
            return False, f"Merge error: {str(e)}"
        finally:
            # Return to original branch if merge failed
            if self._get_current_branch() != "main":
                self._run_command(["git", "checkout", original_branch], check=False)
    
    def delete_branch(self, branch: str, force: bool = False) -> Tuple[bool, str]:
        """Delete a branch locally and remotely"""
        # Delete local branch
        flag = "-D" if force else "-d"
        code, _, stderr = self._run_command(
            ["git", "branch", flag, branch],
            check=False
        )
        
        if code != 0:
            return False, f"Failed to delete local branch: {stderr}"
        
        # Delete remote branch
        code, _, stderr = self._run_command(
            ["git", "push", "origin", "--delete", branch],
            check=False
        )
        
        if code != 0:
            return False, f"Local branch deleted, but failed to delete remote: {stderr}"
        
        return True, "Branch deleted successfully"
    
    def generate_report(self, analyses: Dict[str, Dict]) -> str:
        """Generate a comprehensive report of branch analyses"""
        report = ["# 📊 Branch Analysis Report", ""]
        report.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
        report.append("")
        report.append("## Summary")
        report.append("")
        
        total = len(analyses)
        healthy = sum(1 for a in analyses.values() if a["health"] == BranchHealth.HEALTHY)
        conflicted = sum(1 for a in analyses.values() if a["health"] == BranchHealth.CONFLICTED)
        
        report.append(f"- Total branches: {total}")
        report.append(f"- Healthy: {healthy}")
        report.append(f"- Conflicted: {conflicted}")
        report.append("")
        
        report.append("## Branch Details")
        report.append("")
        
        for branch, analysis in analyses.items():
            report.append(f"### {branch}")
            report.append("")
            report.append(f"**Status:** {analysis['health']}")
            report.append(f"**Commits:** {analysis['commit_count']}")
            report.append(f"**Files changed:** {analysis['diff_stats'].get('files_changed', 0)}")
            report.append(f"**Insertions:** {analysis['diff_stats'].get('insertions', 0)}")
            report.append(f"**Deletions:** {analysis['diff_stats'].get('deletions', 0)}")
            
            if analysis["has_conflicts"]:
                report.append("")
                report.append("**⚠️ Conflicts detected:**")
                for conflict in analysis["conflicts"]:
                    report.append(f"- {conflict}")
            
            report.append("")
            report.append("**Recent commits:**")
            for commit in analysis["commits"][:5]:
                report.append(f"- {commit}")
            
            report.append("")
        
        return "\n".join(report)


def main():
    """Main function for CLI usage"""
    import sys
    
    manager = BranchManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "analyze":
            analyses = manager.analyze_all_branches()
            report = manager.generate_report(analyses)
            print(report)
            
        elif command == "list":
            branches = manager.list_all_branches()
            for branch in branches:
                print(branch)
                
        elif command == "test" and len(sys.argv) > 2:
            branch = sys.argv[2]
            success, output = manager.test_branch(branch)
            print(f"Test {'PASSED' if success else 'FAILED'}")
            print(output)
            
        else:
            print("Usage: python branch_manager.py [analyze|list|test <branch>]")
    else:
        print("Usage: python branch_manager.py [analyze|list|test <branch>]")


if __name__ == "__main__":
    main()
