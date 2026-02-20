"""
Workflow Analyzer - CI/CD Analysis and Monitoring

This module analyzes GitHub Actions workflows across repositories,
identifies failures, and provides intelligent insights.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class FailureCategory(Enum):
    """Categories of workflow failures."""
    TEST_FAILURE = "test_failure"
    LINT_FAILURE = "lint_failure"
    BUILD_FAILURE = "build_failure"
    SECURITY_FAILURE = "security_failure"
    DEPENDENCY_FAILURE = "dependency_failure"
    DEPLOYMENT_FAILURE = "deployment_failure"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class WorkflowAnalyzer:
    """
    Analyzes GitHub Actions workflows and provides intelligence.
    
    Monitors workflow runs across all repositories, identifies failures,
    categorizes issues, and provides actionable recommendations.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the workflow analyzer.
        
        Args:
            github_token: GitHub API token for accessing workflows
        """
        self.github_token = github_token
        self.failure_patterns = self._initialize_failure_patterns()
        logger.info("Workflow Analyzer initialized")
    
    def _initialize_failure_patterns(self) -> Dict[FailureCategory, List[str]]:
        """Initialize regex patterns for failure categorization."""
        return {
            FailureCategory.TEST_FAILURE: [
                r"test.*failed",
                r"assertion.*error",
                r"\d+ failed,?\s+\d+ passed",
                r"pytest.*failed",
                r"jest.*failed",
                r"spec.*failed"
            ],
            FailureCategory.LINT_FAILURE: [
                r"lint.*error",
                r"eslint.*error",
                r"pylint.*error",
                r"formatting.*check.*failed",
                r"black.*would reformat",
                r"style.*violation"
            ],
            FailureCategory.BUILD_FAILURE: [
                r"build.*failed",
                r"compilation.*error",
                r"npm.*ERR",
                r"error.*building",
                r"make.*error",
                r"webpack.*error"
            ],
            FailureCategory.SECURITY_FAILURE: [
                r"security.*vulnerability",
                r"cve-\d+-\d+",
                r"high.*severity",
                r"critical.*vulnerability",
                r"snyk.*found.*issues"
            ],
            FailureCategory.DEPENDENCY_FAILURE: [
                r"dependency.*error",
                r"module.*not.*found",
                r"cannot.*resolve",
                r"package.*not.*found",
                r"version.*conflict",
                r"peer.*dependency.*unmet"
            ],
            FailureCategory.DEPLOYMENT_FAILURE: [
                r"deploy.*failed",
                r"deployment.*error",
                r"push.*failed",
                r"publish.*failed"
            ],
            FailureCategory.TIMEOUT: [
                r"timeout",
                r"timed.*out",
                r"exceeded.*time.*limit"
            ]
        }
    
    def analyze_workflow_run(
        self,
        workflow_name: str,
        run_id: int,
        logs: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Analyze a specific workflow run.
        
        Args:
            workflow_name: Name of the workflow
            run_id: Workflow run ID
            logs: Workflow logs content
            status: Run status (success, failure, cancelled)
            
        Returns:
            Analysis results with categorization and recommendations
        """
        logger.info(f"Analyzing workflow run: {workflow_name} (#{run_id})")
        
        analysis = {
            "workflow_name": workflow_name,
            "run_id": run_id,
            "status": status,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "failures": [],
            "category": None,
            "root_cause": None,
            "recommendations": [],
            "severity": "low"
        }
        
        if status != "failure":
            analysis["category"] = "success"
            return analysis
        
        # Categorize the failure
        category = self._categorize_failure(logs)
        analysis["category"] = category.value
        
        # Extract specific failures
        failures = self._extract_failures(logs, category)
        analysis["failures"] = failures
        
        # Determine root cause
        root_cause = self._determine_root_cause(logs, category, failures)
        analysis["root_cause"] = root_cause
        
        # Generate recommendations
        recommendations = self._generate_recommendations(category, root_cause, failures)
        analysis["recommendations"] = recommendations
        
        # Assign severity
        analysis["severity"] = self._assess_severity(category, failures)
        
        logger.info(f"Analysis complete: {category.value} - {analysis['severity']} severity")
        
        return analysis
    
    def _categorize_failure(self, logs: str) -> FailureCategory:
        """Categorize failure based on log patterns."""
        logs_lower = logs.lower()
        
        # Check each category
        for category, patterns in self.failure_patterns.items():
            for pattern in patterns:
                if re.search(pattern, logs_lower, re.IGNORECASE):
                    logger.debug(f"Matched pattern '{pattern}' for {category}")
                    return category
        
        return FailureCategory.UNKNOWN
    
    def _extract_failures(
        self,
        logs: str,
        category: FailureCategory
    ) -> List[Dict[str, str]]:
        """Extract specific failure messages from logs."""
        failures = []
        
        # Extract error messages
        error_patterns = [
            r"Error:\s*(.+?)(?:\n|$)",
            r"FAILED\s+(.+?)(?:\n|$)",
            r"ERROR:\s*(.+?)(?:\n|$)",
            r"✗\s+(.+?)(?:\n|$)"
        ]
        
        for pattern in error_patterns:
            matches = re.finditer(pattern, logs, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                failure_msg = match.group(1).strip()
                if failure_msg and len(failure_msg) > 10:  # Filter noise
                    failures.append({
                        "message": failure_msg[:200],  # Truncate long messages
                        "type": category.value
                    })
        
        return failures[:10]  # Limit to first 10 failures
    
    def _determine_root_cause(
        self,
        logs: str,
        category: FailureCategory,
        failures: List[Dict[str, str]]
    ) -> str:
        """Determine the root cause of the failure."""
        if category == FailureCategory.TEST_FAILURE:
            if "cannot find module" in logs.lower():
                return "Missing module dependencies causing test failures"
            elif "timeout" in logs.lower():
                return "Test timeout - possible infinite loop or slow operation"
            else:
                return "Test assertions failing - code behavior not matching expectations"
        
        elif category == FailureCategory.LINT_FAILURE:
            return "Code style violations or linting rules not followed"
        
        elif category == FailureCategory.BUILD_FAILURE:
            if "cannot resolve" in logs.lower():
                return "Module resolution failure - missing or incorrect imports"
            else:
                return "Compilation errors in source code"
        
        elif category == FailureCategory.SECURITY_FAILURE:
            return "Security vulnerabilities detected in dependencies"
        
        elif category == FailureCategory.DEPENDENCY_FAILURE:
            return "Dependency version conflicts or missing packages"
        
        elif category == FailureCategory.DEPLOYMENT_FAILURE:
            return "Deployment configuration or credentials issue"
        
        elif category == FailureCategory.TIMEOUT:
            return "Operation exceeded time limits - optimization needed"
        
        return "Unable to determine specific root cause"
    
    def _generate_recommendations(
        self,
        category: FailureCategory,
        root_cause: str,
        failures: List[Dict[str, str]]
    ) -> List[str]:
        """Generate actionable recommendations for fixing the issue."""
        recommendations = []
        
        if category == FailureCategory.TEST_FAILURE:
            recommendations.extend([
                "Review and fix failing test assertions",
                "Update test expectations if code behavior intentionally changed",
                "Check for missing test dependencies or setup issues",
                "Run tests locally to reproduce and debug"
            ])
        
        elif category == FailureCategory.LINT_FAILURE:
            recommendations.extend([
                "Run auto-formatting tools (black, prettier, etc.)",
                "Fix linting violations manually if auto-fix unavailable",
                "Update linting configuration if rules too strict",
                "Add pre-commit hooks to catch issues early"
            ])
        
        elif category == FailureCategory.BUILD_FAILURE:
            recommendations.extend([
                "Fix compilation errors in source code",
                "Verify all imports are correct and modules exist",
                "Check build configuration files",
                "Update build dependencies if outdated"
            ])
        
        elif category == FailureCategory.SECURITY_FAILURE:
            recommendations.extend([
                "Update vulnerable dependencies to patched versions",
                "Review security advisories for mitigation steps",
                "Consider alternative packages if no fix available",
                "Add security scanning to CI pipeline"
            ])
        
        elif category == FailureCategory.DEPENDENCY_FAILURE:
            recommendations.extend([
                "Resolve version conflicts in package dependencies",
                "Install missing dependencies",
                "Update lock files (package-lock.json, poetry.lock, etc.)",
                "Clear cache and reinstall dependencies"
            ])
        
        elif category == FailureCategory.DEPLOYMENT_FAILURE:
            recommendations.extend([
                "Verify deployment credentials and permissions",
                "Check deployment configuration files",
                "Ensure target environment is accessible",
                "Review deployment logs for specific errors"
            ])
        
        elif category == FailureCategory.TIMEOUT:
            recommendations.extend([
                "Optimize slow operations or tests",
                "Increase timeout limits if necessary",
                "Parallelize long-running tasks",
                "Cache dependencies to speed up builds"
            ])
        
        return recommendations
    
    def _assess_severity(
        self,
        category: FailureCategory,
        failures: List[Dict[str, str]]
    ) -> str:
        """Assess the severity of the failure."""
        # Security and deployment failures are critical
        if category in [FailureCategory.SECURITY_FAILURE, FailureCategory.DEPLOYMENT_FAILURE]:
            return "critical"
        
        # Build failures are high priority
        if category == FailureCategory.BUILD_FAILURE:
            return "high"
        
        # Test and lint failures are medium priority
        if category in [FailureCategory.TEST_FAILURE, FailureCategory.LINT_FAILURE]:
            return "medium"
        
        # Other failures are low priority
        return "low"
    
    def monitor_repository_workflows(
        self,
        owner: str,
        repo: str
    ) -> List[Dict[str, Any]]:
        """
        Monitor all workflows for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of workflow analyses
        """
        logger.info(f"Monitoring workflows for {owner}/{repo}")
        
        # In a real implementation, this would:
        # 1. Fetch all workflows using GitHub API
        # 2. Get recent runs for each workflow
        # 3. Analyze failed runs
        # 4. Return comprehensive analysis
        
        # Placeholder implementation
        analyses = []
        
        logger.info(f"Found {len(analyses)} workflow issues")
        return analyses
    
    def get_failure_trends(
        self,
        owner: str,
        repo: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get failure trends for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            days: Number of days to analyze
            
        Returns:
            Trend analysis with statistics
        """
        logger.info(f"Analyzing failure trends for {owner}/{repo} over {days} days")
        
        # Placeholder implementation
        trends = {
            "repository": f"{owner}/{repo}",
            "period_days": days,
            "total_runs": 0,
            "failed_runs": 0,
            "failure_rate": 0.0,
            "categories": {},
            "most_common_failures": [],
            "improvement_suggestions": []
        }
        
        return trends


# Global workflow analyzer instance
workflow_analyzer = WorkflowAnalyzer()
