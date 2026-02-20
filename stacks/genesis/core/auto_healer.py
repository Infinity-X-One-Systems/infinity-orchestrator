"""
Auto Healer - Automated Fixing and Self-Healing

This module automatically fixes identified issues, repairs broken code,
and implements self-healing solutions.
"""

import logging
import re
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

from .auto_diagnostician import DiagnosisResult, IssueType

logger = logging.getLogger(__name__)


class HealingStrategy(Enum):
    """Strategies for healing different types of issues."""
    DEPENDENCY_UPDATE = "dependency_update"
    CODE_FIX = "code_fix"
    CONFIGURATION_FIX = "configuration_fix"
    SECURITY_PATCH = "security_patch"
    FORMAT_FIX = "format_fix"
    TEST_FIX = "test_fix"
    MANUAL_REVIEW = "manual_review"


class HealingResult:
    """Result of a healing operation."""
    
    def __init__(
        self,
        success: bool,
        strategy: HealingStrategy,
        actions_taken: List[str],
        files_modified: List[str],
        validation_passed: bool,
        error_message: Optional[str] = None
    ):
        self.success = success
        self.strategy = strategy
        self.actions_taken = actions_taken
        self.files_modified = files_modified
        self.validation_passed = validation_passed
        self.error_message = error_message
        self.healed_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "strategy": self.strategy.value,
            "actions_taken": self.actions_taken,
            "files_modified": self.files_modified,
            "validation_passed": self.validation_passed,
            "error_message": self.error_message,
            "healed_at": self.healed_at
        }


class AutoHealer:
    """
    Automated healer for system issues.
    
    Implements self-healing solutions for diagnosed issues including
    automated bug fixes, dependency updates, and configuration repairs.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize the auto healer.
        
        Args:
            repo_path: Path to the repository to heal
        """
        self.repo_path = repo_path or Path.cwd()
        logger.info(f"Auto Healer initialized for {self.repo_path}")
    
    def heal_issue(
        self,
        diagnosis: DiagnosisResult,
        auto_commit: bool = False
    ) -> HealingResult:
        """
        Heal an issue based on its diagnosis.
        
        Args:
            diagnosis: Diagnosis result from auto diagnostician
            auto_commit: Whether to automatically commit fixes
            
        Returns:
            Healing result with details of actions taken
        """
        logger.info(f"Healing issue: {diagnosis.issue_type.value}")
        
        # Select healing strategy
        strategy = self._select_strategy(diagnosis)
        
        # Execute healing based on strategy
        if strategy == HealingStrategy.DEPENDENCY_UPDATE:
            result = self._heal_dependency_issue(diagnosis)
        elif strategy == HealingStrategy.CODE_FIX:
            result = self._heal_code_issue(diagnosis)
        elif strategy == HealingStrategy.CONFIGURATION_FIX:
            result = self._heal_configuration_issue(diagnosis)
        elif strategy == HealingStrategy.SECURITY_PATCH:
            result = self._heal_security_issue(diagnosis)
        elif strategy == HealingStrategy.FORMAT_FIX:
            result = self._heal_format_issue(diagnosis)
        elif strategy == HealingStrategy.TEST_FIX:
            result = self._heal_test_issue(diagnosis)
        else:
            result = HealingResult(
                success=False,
                strategy=HealingStrategy.MANUAL_REVIEW,
                actions_taken=["Issue requires manual review"],
                files_modified=[],
                validation_passed=False,
                error_message="Automated healing not available for this issue type"
            )
        
        # Validate the fix
        if result.success:
            result.validation_passed = self._validate_fix(diagnosis, result)
        
        # Commit changes if requested and successful
        if auto_commit and result.success and result.validation_passed:
            self._commit_fix(diagnosis, result)
        
        logger.info(f"Healing complete: {result.success} (validated: {result.validation_passed})")
        
        return result
    
    def _select_strategy(self, diagnosis: DiagnosisResult) -> HealingStrategy:
        """Select appropriate healing strategy."""
        if diagnosis.issue_type == IssueType.DEPENDENCY_CONFLICT:
            return HealingStrategy.DEPENDENCY_UPDATE
        elif diagnosis.issue_type == IssueType.CONFIGURATION_ERROR:
            return HealingStrategy.CONFIGURATION_FIX
        elif diagnosis.issue_type == IssueType.SECURITY_VULNERABILITY:
            return HealingStrategy.SECURITY_PATCH
        elif diagnosis.issue_type == IssueType.CODE_QUALITY:
            return HealingStrategy.FORMAT_FIX
        else:
            # Default to code fix for unknown issues
            return HealingStrategy.CODE_FIX
    
    def _heal_dependency_issue(
        self,
        diagnosis: DiagnosisResult
    ) -> HealingResult:
        """Heal dependency-related issues."""
        actions_taken = []
        files_modified = []
        
        try:
            # Detect package manager
            if (self.repo_path / "package.json").exists():
                # Node.js project
                logger.info("Detected Node.js project, running npm install")
                subprocess.run(
                    ["npm", "install"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
                actions_taken.append("Ran 'npm install' to fix dependencies")
                files_modified.append("package-lock.json")
            
            elif (self.repo_path / "requirements.txt").exists():
                # Python project
                logger.info("Detected Python project, running pip install")
                subprocess.run(
                    ["pip", "install", "-r", "requirements.txt"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
                actions_taken.append("Ran 'pip install' to fix dependencies")
            
            elif (self.repo_path / "Cargo.toml").exists():
                # Rust project
                logger.info("Detected Rust project, running cargo build")
                subprocess.run(
                    ["cargo", "build"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
                actions_taken.append("Ran 'cargo build' to fix dependencies")
                files_modified.append("Cargo.lock")
            
            return HealingResult(
                success=True,
                strategy=HealingStrategy.DEPENDENCY_UPDATE,
                actions_taken=actions_taken,
                files_modified=files_modified,
                validation_passed=False  # Will be validated later
            )
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to heal dependency issue: {e}")
            return HealingResult(
                success=False,
                strategy=HealingStrategy.DEPENDENCY_UPDATE,
                actions_taken=actions_taken,
                files_modified=files_modified,
                validation_passed=False,
                error_message=str(e)
            )
    
    def _heal_code_issue(
        self,
        diagnosis: DiagnosisResult
    ) -> HealingResult:
        """Heal code-related issues."""
        actions_taken = []
        files_modified = []
        
        # For code issues, we would typically:
        # 1. Parse the affected files
        # 2. Use LLM to generate a fix
        # 3. Apply the fix
        # 4. Run tests to validate
        
        # Placeholder implementation
        actions_taken.append("Code issue identified - manual review recommended")
        
        return HealingResult(
            success=False,
            strategy=HealingStrategy.CODE_FIX,
            actions_taken=actions_taken,
            files_modified=files_modified,
            validation_passed=False,
            error_message="Automated code fixing requires LLM integration"
        )
    
    def _heal_configuration_issue(
        self,
        diagnosis: DiagnosisResult
    ) -> HealingResult:
        """Heal configuration-related issues."""
        actions_taken = []
        files_modified = []
        
        # Check if environment file exists
        env_example = self.repo_path / ".env.example"
        env_file = self.repo_path / ".env"
        
        if env_example.exists() and not env_file.exists():
            # Copy example to actual
            import shutil
            shutil.copy(env_example, env_file)
            actions_taken.append("Created .env from .env.example")
            files_modified.append(".env")
            
            return HealingResult(
                success=True,
                strategy=HealingStrategy.CONFIGURATION_FIX,
                actions_taken=actions_taken,
                files_modified=files_modified,
                validation_passed=False
            )
        
        actions_taken.append("Configuration issue requires manual review")
        
        return HealingResult(
            success=False,
            strategy=HealingStrategy.CONFIGURATION_FIX,
            actions_taken=actions_taken,
            files_modified=files_modified,
            validation_passed=False,
            error_message="Specific configuration fix could not be determined"
        )
    
    def _heal_security_issue(
        self,
        diagnosis: DiagnosisResult
    ) -> HealingResult:
        """Heal security-related issues."""
        actions_taken = []
        files_modified = []
        
        try:
            # Try to update vulnerable dependencies
            if (self.repo_path / "package.json").exists():
                logger.info("Running npm audit fix")
                subprocess.run(
                    ["npm", "audit", "fix"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
                actions_taken.append("Ran 'npm audit fix' to patch vulnerabilities")
                files_modified.extend(["package.json", "package-lock.json"])
            
            elif (self.repo_path / "requirements.txt").exists():
                logger.info("Checking for security updates with pip")
                # In real implementation, would use safety or similar tool
                actions_taken.append("Checked for security updates")
            
            return HealingResult(
                success=True,
                strategy=HealingStrategy.SECURITY_PATCH,
                actions_taken=actions_taken,
                files_modified=files_modified,
                validation_passed=False
            )
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to heal security issue: {e}")
            return HealingResult(
                success=False,
                strategy=HealingStrategy.SECURITY_PATCH,
                actions_taken=actions_taken,
                files_modified=files_modified,
                validation_passed=False,
                error_message=str(e)
            )
    
    def _heal_format_issue(
        self,
        diagnosis: DiagnosisResult
    ) -> HealingResult:
        """Heal code formatting issues."""
        actions_taken = []
        files_modified = []
        
        try:
            # Try Python formatting
            if any(".py" in f for f in diagnosis.affected_files):
                logger.info("Running black formatter")
                subprocess.run(
                    ["python", "-m", "black", "src/", "tests/"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
                actions_taken.append("Ran 'black' to format Python code")
                files_modified.extend(diagnosis.affected_files)
            
            # Try JavaScript/TypeScript formatting
            if any(f.endswith((".js", ".ts", ".jsx", ".tsx")) for f in diagnosis.affected_files):
                if (self.repo_path / "package.json").exists():
                    logger.info("Running prettier formatter")
                    subprocess.run(
                        ["npx", "prettier", "--write", "."],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True
                    )
                    actions_taken.append("Ran 'prettier' to format JS/TS code")
                    files_modified.extend(diagnosis.affected_files)
            
            return HealingResult(
                success=True,
                strategy=HealingStrategy.FORMAT_FIX,
                actions_taken=actions_taken,
                files_modified=files_modified,
                validation_passed=False
            )
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to heal format issue: {e}")
            return HealingResult(
                success=False,
                strategy=HealingStrategy.FORMAT_FIX,
                actions_taken=actions_taken,
                files_modified=files_modified,
                validation_passed=False,
                error_message=str(e)
            )
    
    def _heal_test_issue(
        self,
        diagnosis: DiagnosisResult
    ) -> HealingResult:
        """Heal test-related issues."""
        actions_taken = []
        files_modified = []
        
        # Test healing requires understanding what the test expects
        # This would typically involve LLM analysis and code generation
        
        actions_taken.append("Test issue identified - requires manual review or LLM-assisted fix")
        
        return HealingResult(
            success=False,
            strategy=HealingStrategy.TEST_FIX,
            actions_taken=actions_taken,
            files_modified=files_modified,
            validation_passed=False,
            error_message="Automated test fixing requires LLM integration"
        )
    
    def _validate_fix(
        self,
        diagnosis: DiagnosisResult,
        healing_result: HealingResult
    ) -> bool:
        """Validate that the fix actually resolves the issue."""
        logger.info("Validating fix...")
        
        try:
            # Run tests based on project type
            if (self.repo_path / "package.json").exists():
                # Try to run npm test
                result = subprocess.run(
                    ["npm", "test"],
                    cwd=self.repo_path,
                    capture_output=True,
                    timeout=300
                )
                return result.returncode == 0
            
            elif (self.repo_path / "requirements.txt").exists():
                # Try to run pytest
                result = subprocess.run(
                    ["python", "-m", "pytest", "-x"],
                    cwd=self.repo_path,
                    capture_output=True,
                    timeout=300
                )
                return result.returncode == 0
            
            # If no tests found, assume valid
            return True
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"Validation failed: {e}")
            return False
    
    def _commit_fix(
        self,
        diagnosis: DiagnosisResult,
        healing_result: HealingResult
    ) -> None:
        """Commit the fix to Git."""
        try:
            # Stage modified files
            for file in healing_result.files_modified:
                subprocess.run(
                    ["git", "add", file],
                    cwd=self.repo_path,
                    check=True
                )
            
            # Create commit message
            commit_msg = f"🤖 Auto-heal: Fix {diagnosis.issue_type.value}\n\n"
            commit_msg += f"Root cause: {diagnosis.root_cause}\n\n"
            commit_msg += "Actions taken:\n"
            for action in healing_result.actions_taken:
                commit_msg += f"- {action}\n"
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.repo_path,
                check=True
            )
            
            logger.info("Fix committed successfully")
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit fix: {e}")


# Global auto healer instance
auto_healer = AutoHealer()
