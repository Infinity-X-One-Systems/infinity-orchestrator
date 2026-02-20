"""
Conflict Resolver - Automated Merge Conflict Resolution

This module automatically resolves merge conflicts using semantic analysis
and intelligent merging strategies.
"""

import logging
import re
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ConflictResolutionResult:
    """Result of a conflict resolution operation."""
    
    def __init__(
        self,
        success: bool,
        conflicts_resolved: int,
        files_modified: List[str],
        strategy_used: str,
        manual_review_needed: bool = False,
        error_message: Optional[str] = None
    ):
        self.success = success
        self.conflicts_resolved = conflicts_resolved
        self.files_modified = files_modified
        self.strategy_used = strategy_used
        self.manual_review_needed = manual_review_needed
        self.error_message = error_message
        self.resolved_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "conflicts_resolved": self.conflicts_resolved,
            "files_modified": self.files_modified,
            "strategy_used": self.strategy_used,
            "manual_review_needed": self.manual_review_needed,
            "error_message": self.error_message,
            "resolved_at": self.resolved_at
        }


class ConflictResolver:
    """
    Automated merge conflict resolver.
    
    Uses semantic analysis and intelligent merging strategies to
    automatically resolve Git merge conflicts.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize the conflict resolver.
        
        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = repo_path or Path.cwd()
        logger.info(f"Conflict Resolver initialized for {self.repo_path}")
    
    def detect_conflicts(self) -> List[str]:
        """
        Detect files with merge conflicts.
        
        Returns:
            List of file paths with conflicts
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            conflicted_files = [
                line.strip() for line in result.stdout.split('\n')
                if line.strip()
            ]
            
            logger.info(f"Found {len(conflicted_files)} files with conflicts")
            return conflicted_files
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to detect conflicts: {e}")
            return []
    
    def resolve_conflicts(
        self,
        auto_commit: bool = False
    ) -> ConflictResolutionResult:
        """
        Automatically resolve all detected conflicts.
        
        Args:
            auto_commit: Whether to automatically commit resolved conflicts
            
        Returns:
            Resolution result with details of conflicts resolved
        """
        logger.info("Starting automated conflict resolution")
        
        conflicted_files = self.detect_conflicts()
        
        if not conflicted_files:
            logger.info("No conflicts found")
            return ConflictResolutionResult(
                success=True,
                conflicts_resolved=0,
                files_modified=[],
                strategy_used="none",
                manual_review_needed=False
            )
        
        resolved_files = []
        manual_review_files = []
        
        for file_path in conflicted_files:
            logger.info(f"Resolving conflicts in {file_path}")
            
            success = self._resolve_file_conflicts(file_path)
            
            if success:
                resolved_files.append(file_path)
            else:
                manual_review_files.append(file_path)
        
        # Stage resolved files
        for file_path in resolved_files:
            try:
                subprocess.run(
                    ["git", "add", file_path],
                    cwd=self.repo_path,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to stage {file_path}: {e}")
        
        # Commit if requested
        if auto_commit and resolved_files:
            self._commit_resolution(resolved_files)
        
        result = ConflictResolutionResult(
            success=len(manual_review_files) == 0,
            conflicts_resolved=len(resolved_files),
            files_modified=resolved_files,
            strategy_used="semantic_merge",
            manual_review_needed=len(manual_review_files) > 0,
            error_message=f"{len(manual_review_files)} files require manual review" if manual_review_files else None
        )
        
        logger.info(
            f"Resolution complete: {len(resolved_files)} resolved, "
            f"{len(manual_review_files)} need manual review"
        )
        
        return result
    
    def _resolve_file_conflicts(self, file_path: str) -> bool:
        """
        Resolve conflicts in a single file.
        
        Args:
            file_path: Path to the conflicted file
            
        Returns:
            True if successfully resolved, False otherwise
        """
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        try:
            # Read file content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse conflicts
            conflicts = self._parse_conflicts(content)
            
            if not conflicts:
                logger.warning(f"No conflict markers found in {file_path}")
                return False
            
            # Resolve each conflict
            resolved_content = content
            for conflict in reversed(conflicts):  # Process from end to avoid offset issues
                resolution = self._resolve_conflict(conflict, file_path)
                
                if resolution is None:
                    logger.warning(f"Could not auto-resolve conflict in {file_path}")
                    return False
                
                # Replace conflict markers with resolution
                start_pos = conflict['start_pos']
                end_pos = conflict['end_pos']
                resolved_content = (
                    resolved_content[:start_pos] +
                    resolution +
                    resolved_content[end_pos:]
                )
            
            # Write resolved content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(resolved_content)
            
            logger.info(f"Successfully resolved conflicts in {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error resolving conflicts in {file_path}: {e}")
            return False
    
    def _parse_conflicts(self, content: str) -> List[Dict]:
        """
        Parse conflict markers in file content.
        
        Returns:
            List of conflict dictionaries with positions and content
        """
        conflicts = []
        
        # Regex pattern for conflict markers
        pattern = re.compile(
            r'^<<<<<<< (.+?)\n(.*?)^=======\n(.*?)^>>>>>>> (.+?)\n',
            re.MULTILINE | re.DOTALL
        )
        
        for match in pattern.finditer(content):
            conflicts.append({
                'start_pos': match.start(),
                'end_pos': match.end(),
                'ours_label': match.group(1),
                'ours_content': match.group(2),
                'theirs_content': match.group(3),
                'theirs_label': match.group(4)
            })
        
        logger.debug(f"Found {len(conflicts)} conflict sections")
        return conflicts
    
    def _resolve_conflict(self, conflict: Dict, file_path: str) -> Optional[str]:
        """
        Resolve a single conflict section.
        
        Args:
            conflict: Conflict dictionary with ours/theirs content
            file_path: Path to the file (for context)
            
        Returns:
            Resolved content or None if cannot auto-resolve
        """
        ours = conflict['ours_content']
        theirs = conflict['theirs_content']
        
        # Strategy 1: If one side is empty, use the other
        if not ours.strip():
            logger.debug("Using theirs (ours is empty)")
            return theirs
        if not theirs.strip():
            logger.debug("Using ours (theirs is empty)")
            return ours
        
        # Strategy 2: If both sides are identical, use either
        if ours == theirs:
            logger.debug("Both sides identical")
            return ours
        
        # Strategy 3: If changes are in different sections, merge both
        if self._are_changes_compatible(ours, theirs):
            logger.debug("Changes are compatible, merging both")
            return self._merge_compatible_changes(ours, theirs)
        
        # Strategy 4: For specific file types, use specialized strategies
        if file_path.endswith('.json'):
            return self._resolve_json_conflict(ours, theirs)
        elif file_path.endswith(('.yml', '.yaml')):
            return self._resolve_yaml_conflict(ours, theirs)
        elif file_path.endswith('.md'):
            return self._resolve_markdown_conflict(ours, theirs)
        
        # Strategy 5: For imports/dependencies, merge both
        if 'import ' in ours or 'import ' in theirs:
            return self._merge_imports(ours, theirs)
        
        # Cannot auto-resolve
        logger.debug("Cannot auto-resolve conflict")
        return None
    
    def _are_changes_compatible(self, ours: str, theirs: str) -> bool:
        """Check if changes are in different parts and can be merged."""
        # Simple heuristic: if they share most lines, changes might be compatible
        ours_lines = set(ours.split('\n'))
        theirs_lines = set(theirs.split('\n'))
        
        # If there's significant overlap, changes might conflict
        common_lines = ours_lines & theirs_lines
        total_lines = ours_lines | theirs_lines
        
        if not total_lines:
            return False
        
        overlap_ratio = len(common_lines) / len(total_lines)
        
        # If less than 30% overlap, changes are likely in different areas
        return overlap_ratio < 0.3
    
    def _merge_compatible_changes(self, ours: str, theirs: str) -> str:
        """Merge compatible changes from both sides."""
        # Simple merge: combine unique lines
        ours_lines = ours.split('\n')
        theirs_lines = theirs.split('\n')
        
        # Use ours as base and add unique lines from theirs
        merged_lines = ours_lines.copy()
        
        for line in theirs_lines:
            if line not in merged_lines:
                merged_lines.append(line)
        
        return '\n'.join(merged_lines)
    
    def _resolve_json_conflict(self, ours: str, theirs: str) -> Optional[str]:
        """Resolve JSON conflicts by merging objects."""
        try:
            import json
            
            ours_json = json.loads(ours)
            theirs_json = json.loads(theirs)
            
            # Merge dictionaries
            if isinstance(ours_json, dict) and isinstance(theirs_json, dict):
                merged = {**ours_json, **theirs_json}
                return json.dumps(merged, indent=2)
        except Exception as e:
            logger.debug(f"Failed to merge JSON: {e}")
        
        return None
    
    def _resolve_yaml_conflict(self, ours: str, theirs: str) -> Optional[str]:
        """Resolve YAML conflicts."""
        # For now, prefer ours for YAML
        # In a real implementation, would parse and merge YAML
        return ours
    
    def _resolve_markdown_conflict(self, ours: str, theirs: str) -> str:
        """Resolve Markdown conflicts by concatenating."""
        # For markdown, often safe to concatenate both versions
        return ours + "\n\n" + theirs
    
    def _merge_imports(self, ours: str, theirs: str) -> str:
        """Merge import statements from both sides."""
        # Extract and merge unique imports
        import_pattern = re.compile(r'^(?:import|from)\s+.+$', re.MULTILINE)
        
        ours_imports = set(import_pattern.findall(ours))
        theirs_imports = set(import_pattern.findall(theirs))
        
        # Combine all unique imports
        all_imports = sorted(ours_imports | theirs_imports)
        
        return '\n'.join(all_imports)
    
    def _commit_resolution(self, resolved_files: List[str]) -> None:
        """Commit resolved conflicts."""
        try:
            commit_msg = "🤖 Auto-resolve: Merge conflicts resolved\n\n"
            commit_msg += "Files resolved:\n"
            for file_path in resolved_files:
                commit_msg += f"- {file_path}\n"
            
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.repo_path,
                check=True
            )
            
            logger.info("Committed conflict resolution")
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit resolution: {e}")
    
    def resolve_pr_conflicts(
        self,
        pr_number: int,
        base_branch: str = "main"
    ) -> ConflictResolutionResult:
        """
        Resolve conflicts for a pull request.
        
        Args:
            pr_number: Pull request number
            base_branch: Base branch to merge into
            
        Returns:
            Resolution result
        """
        logger.info(f"Resolving conflicts for PR #{pr_number}")
        
        try:
            # Fetch latest from base branch
            subprocess.run(
                ["git", "fetch", "origin", base_branch],
                cwd=self.repo_path,
                check=True
            )
            
            # Try to merge base into current branch
            result = subprocess.run(
                ["git", "merge", f"origin/{base_branch}"],
                cwd=self.repo_path,
                capture_output=True
            )
            
            if result.returncode == 0:
                # No conflicts
                return ConflictResolutionResult(
                    success=True,
                    conflicts_resolved=0,
                    files_modified=[],
                    strategy_used="auto_merge"
                )
            
            # Conflicts detected, resolve them
            return self.resolve_conflicts(auto_commit=True)
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to resolve PR conflicts: {e}")
            return ConflictResolutionResult(
                success=False,
                conflicts_resolved=0,
                files_modified=[],
                strategy_used="failed",
                error_message=str(e)
            )


# Global conflict resolver instance
conflict_resolver = ConflictResolver()
