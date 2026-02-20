"""
Auto Validator - Automated Validation and Verification

This module continuously validates changes, runs tests, and enforces
quality gates for the Genesis system.
"""

import logging
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status of validation checks."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(
        self,
        overall_status: ValidationStatus,
        checks_performed: List[Dict[str, Any]],
        tests_passed: int,
        tests_failed: int,
        quality_score: float,
        issues_found: List[str]
    ):
        self.overall_status = overall_status
        self.checks_performed = checks_performed
        self.tests_passed = tests_passed
        self.tests_failed = tests_failed
        self.quality_score = quality_score
        self.issues_found = issues_found
        self.validated_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_status": self.overall_status.value,
            "checks_performed": self.checks_performed,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "quality_score": self.quality_score,
            "issues_found": self.issues_found,
            "validated_at": self.validated_at
        }


class AutoValidator:
    """
    Automated validator for system changes.
    
    Performs comprehensive validation including tests, linting,
    security scans, and quality checks.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize the auto validator.
        
        Args:
            repo_path: Path to the repository to validate
        """
        self.repo_path = repo_path or Path.cwd()
        logger.info(f"Auto Validator initialized for {self.repo_path}")
    
    def validate_changes(
        self,
        run_tests: bool = True,
        run_linters: bool = True,
        run_security: bool = True
    ) -> ValidationResult:
        """
        Validate all changes comprehensively.
        
        Args:
            run_tests: Whether to run test suites
            run_linters: Whether to run linters
            run_security: Whether to run security scans
            
        Returns:
            Validation result with details of all checks
        """
        logger.info("Starting comprehensive validation")
        
        checks_performed = []
        tests_passed = 0
        tests_failed = 0
        issues_found = []
        
        # Run tests
        if run_tests:
            test_result = self._run_tests()
            checks_performed.append(test_result)
            tests_passed += test_result.get('passed', 0)
            tests_failed += test_result.get('failed', 0)
            if test_result['status'] != ValidationStatus.PASSED.value:
                issues_found.extend(test_result.get('issues', []))
        
        # Run linters
        if run_linters:
            lint_result = self._run_linters()
            checks_performed.append(lint_result)
            if lint_result['status'] != ValidationStatus.PASSED.value:
                issues_found.extend(lint_result.get('issues', []))
        
        # Run security scans
        if run_security:
            security_result = self._run_security_scans()
            checks_performed.append(security_result)
            if security_result['status'] != ValidationStatus.PASSED.value:
                issues_found.extend(security_result.get('issues', []))
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(checks_performed)
        
        # Determine overall status
        if tests_failed > 0 or any(
            check['status'] == ValidationStatus.FAILED.value
            for check in checks_performed
        ):
            overall_status = ValidationStatus.FAILED
        elif any(
            check['status'] == ValidationStatus.WARNING.value
            for check in checks_performed
        ):
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.PASSED
        
        result = ValidationResult(
            overall_status=overall_status,
            checks_performed=checks_performed,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            quality_score=quality_score,
            issues_found=issues_found
        )
        
        logger.info(
            f"Validation complete: {overall_status.value} "
            f"(score: {quality_score:.2f})"
        )
        
        return result
    
    def _run_tests(self) -> Dict[str, Any]:
        """Run test suites."""
        logger.info("Running tests...")
        
        result = {
            "name": "tests",
            "status": ValidationStatus.SKIPPED.value,
            "passed": 0,
            "failed": 0,
            "issues": []
        }
        
        try:
            # Try Python tests
            if (self.repo_path / "tests").exists():
                test_result = subprocess.run(
                    ["python", "-m", "pytest", "-v", "--tb=short"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                # Parse pytest output
                output = test_result.stdout + test_result.stderr
                passed = output.count(" PASSED")
                failed = output.count(" FAILED")
                
                result["passed"] = passed
                result["failed"] = failed
                result["status"] = (
                    ValidationStatus.PASSED.value if failed == 0
                    else ValidationStatus.FAILED.value
                )
                
                if failed > 0:
                    result["issues"].append(f"{failed} test(s) failed")
                
                logger.info(f"Tests: {passed} passed, {failed} failed")
            
            # Try Node.js tests
            elif (self.repo_path / "package.json").exists():
                test_result = subprocess.run(
                    ["npm", "test"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                result["status"] = (
                    ValidationStatus.PASSED.value if test_result.returncode == 0
                    else ValidationStatus.FAILED.value
                )
                
                if test_result.returncode != 0:
                    result["issues"].append("Test suite failed")
        
        except subprocess.TimeoutExpired:
            result["status"] = ValidationStatus.FAILED.value
            result["issues"].append("Tests timed out")
            logger.error("Tests timed out")
        
        except Exception as e:
            result["status"] = ValidationStatus.FAILED.value
            result["issues"].append(f"Test execution error: {str(e)}")
            logger.error(f"Error running tests: {e}")
        
        return result
    
    def _run_linters(self) -> Dict[str, Any]:
        """Run code linters."""
        logger.info("Running linters...")
        
        result = {
            "name": "linters",
            "status": ValidationStatus.PASSED.value,
            "issues": []
        }
        
        try:
            # Python linting
            if (self.repo_path / "src").exists():
                # Run black check
                black_result = subprocess.run(
                    ["python", "-m", "black", "--check", "src/"],
                    cwd=self.repo_path,
                    capture_output=True
                )
                
                if black_result.returncode != 0:
                    result["status"] = ValidationStatus.WARNING.value
                    result["issues"].append("Code formatting issues (black)")
                
                # Run pylint
                pylint_result = subprocess.run(
                    ["python", "-m", "pylint", "src/genesis", "--exit-zero"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                
                # Check for high-priority issues
                if "E:" in pylint_result.stdout:
                    result["status"] = ValidationStatus.WARNING.value
                    result["issues"].append("Linting errors found (pylint)")
            
            # JavaScript/TypeScript linting
            if (self.repo_path / "package.json").exists():
                eslint_result = subprocess.run(
                    ["npx", "eslint", "."],
                    cwd=self.repo_path,
                    capture_output=True
                )
                
                if eslint_result.returncode != 0:
                    result["status"] = ValidationStatus.WARNING.value
                    result["issues"].append("Linting issues (eslint)")
        
        except Exception as e:
            logger.error(f"Error running linters: {e}")
            result["status"] = ValidationStatus.WARNING.value
            result["issues"].append(f"Linter execution error: {str(e)}")
        
        return result
    
    def _run_security_scans(self) -> Dict[str, Any]:
        """Run security scans."""
        logger.info("Running security scans...")
        
        result = {
            "name": "security",
            "status": ValidationStatus.PASSED.value,
            "issues": []
        }
        
        try:
            # Python security check
            if (self.repo_path / "requirements.txt").exists():
                # Run pip audit
                audit_result = subprocess.run(
                    ["pip", "audit", "--desc"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                
                if audit_result.returncode != 0:
                    result["status"] = ValidationStatus.WARNING.value
                    result["issues"].append("Security vulnerabilities found (pip)")
            
            # Node.js security check
            if (self.repo_path / "package.json").exists():
                audit_result = subprocess.run(
                    ["npm", "audit"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                
                # Check for high/critical vulnerabilities
                if "high" in audit_result.stdout.lower() or "critical" in audit_result.stdout.lower():
                    result["status"] = ValidationStatus.FAILED.value
                    result["issues"].append("Critical security vulnerabilities found (npm)")
                elif audit_result.returncode != 0:
                    result["status"] = ValidationStatus.WARNING.value
                    result["issues"].append("Security vulnerabilities found (npm)")
        
        except Exception as e:
            logger.error(f"Error running security scans: {e}")
            result["status"] = ValidationStatus.WARNING.value
            result["issues"].append(f"Security scan error: {str(e)}")
        
        return result
    
    def _calculate_quality_score(
        self,
        checks_performed: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall quality score (0-100)."""
        if not checks_performed:
            return 0.0
        
        score = 100.0
        
        for check in checks_performed:
            status = check.get('status')
            
            if status == ValidationStatus.FAILED.value:
                score -= 30
            elif status == ValidationStatus.WARNING.value:
                score -= 10
            elif status == ValidationStatus.SKIPPED.value:
                score -= 5
        
        # Adjust for test results
        for check in checks_performed:
            if check.get('name') == 'tests':
                passed = check.get('passed', 0)
                failed = check.get('failed', 0)
                total = passed + failed
                
                if total > 0:
                    pass_rate = passed / total
                    # Bonus for high pass rate
                    if pass_rate == 1.0:
                        score += 10
                    elif pass_rate >= 0.9:
                        score += 5
        
        return max(0.0, min(100.0, score))
    
    def validate_pr(self, pr_number: int) -> ValidationResult:
        """
        Validate a pull request.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            Validation result
        """
        logger.info(f"Validating PR #{pr_number}")
        
        # In a real implementation, this would:
        # 1. Checkout the PR branch
        # 2. Run all validation checks
        # 3. Comment on PR with results
        
        return self.validate_changes()


# Global auto validator instance
auto_validator = AutoValidator()
