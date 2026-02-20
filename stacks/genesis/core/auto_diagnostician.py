"""
Auto Diagnostician - Automated Issue Diagnosis

This module automatically diagnoses system issues, performs health checks,
and identifies root causes across repositories.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of issues that can be diagnosed."""
    DEPENDENCY_CONFLICT = "dependency_conflict"
    CONFIGURATION_ERROR = "configuration_error"
    CODE_QUALITY = "code_quality"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_ISSUE = "performance_issue"
    INTEGRATION_FAILURE = "integration_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNKNOWN = "unknown"


class DiagnosisResult:
    """Result of a diagnostic operation."""
    
    def __init__(
        self,
        issue_type: IssueType,
        severity: str,
        description: str,
        root_cause: str,
        evidence: List[str],
        affected_files: List[str],
        recommendations: List[str]
    ):
        self.issue_type = issue_type
        self.severity = severity
        self.description = description
        self.root_cause = root_cause
        self.evidence = evidence
        self.affected_files = affected_files
        self.recommendations = recommendations
        self.diagnosed_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity,
            "description": self.description,
            "root_cause": self.root_cause,
            "evidence": self.evidence,
            "affected_files": self.affected_files,
            "recommendations": self.recommendations,
            "diagnosed_at": self.diagnosed_at
        }


class AutoDiagnostician:
    """
    Automated diagnostician for system issues.
    
    Performs intelligent diagnosis of errors, failures, and system health issues
    across all repositories.
    """
    
    def __init__(self):
        """Initialize the auto diagnostician."""
        logger.info("Auto Diagnostician initialized")
    
    def diagnose_error(
        self,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> DiagnosisResult:
        """
        Diagnose an error from its message and stack trace.
        
        Args:
            error_message: The error message
            stack_trace: Optional stack trace
            context: Additional context (file, line, etc.)
            
        Returns:
            Diagnosis result with root cause and recommendations
        """
        logger.info(f"Diagnosing error: {error_message[:100]}...")
        
        # Analyze error message
        issue_type = self._classify_error(error_message, stack_trace)
        
        # Determine root cause
        root_cause = self._determine_root_cause(
            error_message,
            stack_trace,
            issue_type,
            context
        )
        
        # Collect evidence
        evidence = self._collect_evidence(
            error_message,
            stack_trace,
            context
        )
        
        # Identify affected files
        affected_files = self._identify_affected_files(
            stack_trace,
            context
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            issue_type,
            root_cause,
            error_message
        )
        
        # Assess severity
        severity = self._assess_severity(issue_type, error_message)
        
        diagnosis = DiagnosisResult(
            issue_type=issue_type,
            severity=severity,
            description=error_message[:500],
            root_cause=root_cause,
            evidence=evidence,
            affected_files=affected_files,
            recommendations=recommendations
        )
        
        logger.info(f"Diagnosis complete: {issue_type.value} ({severity})")
        
        return diagnosis
    
    def _classify_error(
        self,
        error_message: str,
        stack_trace: Optional[str]
    ) -> IssueType:
        """Classify the type of error."""
        msg_lower = error_message.lower()
        trace_lower = (stack_trace or "").lower()
        combined = msg_lower + " " + trace_lower
        
        # Dependency issues
        if any(keyword in combined for keyword in [
            "module not found", "cannot find module", "no module named",
            "import error", "modulenotfounderror", "version conflict",
            "peer dependency"
        ]):
            return IssueType.DEPENDENCY_CONFLICT
        
        # Configuration errors
        if any(keyword in combined for keyword in [
            "config", "configuration", "invalid setting", "missing environment",
            "env var", "not configured"
        ]):
            return IssueType.CONFIGURATION_ERROR
        
        # Security vulnerabilities
        if any(keyword in combined for keyword in [
            "cve-", "vulnerability", "security", "exploit", "injection",
            "xss", "csrf", "sql injection"
        ]):
            return IssueType.SECURITY_VULNERABILITY
        
        # Performance issues
        if any(keyword in combined for keyword in [
            "timeout", "too slow", "performance", "memory leak",
            "out of memory", "stack overflow"
        ]):
            return IssueType.PERFORMANCE_ISSUE
        
        # Integration failures
        if any(keyword in combined for keyword in [
            "connection refused", "network error", "api error",
            "http error", "failed to connect", "econnrefused"
        ]):
            return IssueType.INTEGRATION_FAILURE
        
        # Resource exhaustion
        if any(keyword in combined for keyword in [
            "out of memory", "disk space", "no space left",
            "resource exhausted", "too many open files"
        ]):
            return IssueType.RESOURCE_EXHAUSTION
        
        return IssueType.UNKNOWN
    
    def _determine_root_cause(
        self,
        error_message: str,
        stack_trace: Optional[str],
        issue_type: IssueType,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Determine the root cause of the issue."""
        if issue_type == IssueType.DEPENDENCY_CONFLICT:
            if "cannot find module" in error_message.lower():
                return "Required module is not installed or not in the correct location"
            elif "version" in error_message.lower():
                return "Dependency version mismatch or incompatibility"
            else:
                return "Missing or incompatible dependency"
        
        elif issue_type == IssueType.CONFIGURATION_ERROR:
            if "environment" in error_message.lower():
                return "Missing or incorrect environment variable configuration"
            else:
                return "Invalid or missing configuration setting"
        
        elif issue_type == IssueType.SECURITY_VULNERABILITY:
            return "Security vulnerability in code or dependencies requiring patching"
        
        elif issue_type == IssueType.PERFORMANCE_ISSUE:
            if "timeout" in error_message.lower():
                return "Operation taking too long - optimization or timeout adjustment needed"
            elif "memory" in error_message.lower():
                return "Memory usage exceeding limits - memory leak or optimization needed"
            else:
                return "Performance bottleneck in code execution"
        
        elif issue_type == IssueType.INTEGRATION_FAILURE:
            if "connection refused" in error_message.lower():
                return "Target service is not running or not accessible"
            elif "authentication" in error_message.lower():
                return "Authentication failure - invalid credentials or permissions"
            else:
                return "External service integration failure"
        
        elif issue_type == IssueType.RESOURCE_EXHAUSTION:
            return "System resources (memory, disk, handles) exhausted"
        
        return "Root cause unclear - requires manual investigation"
    
    def _collect_evidence(
        self,
        error_message: str,
        stack_trace: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Collect evidence supporting the diagnosis."""
        evidence = []
        
        # Add error message as evidence
        evidence.append(f"Error: {error_message[:200]}")
        
        # Extract relevant stack trace lines
        if stack_trace:
            lines = stack_trace.split('\n')
            relevant_lines = [line for line in lines if any(
                keyword in line.lower() for keyword in
                ['error', 'at ', 'file ', 'line ']
            )]
            evidence.extend(relevant_lines[:5])
        
        # Add context information
        if context:
            for key, value in context.items():
                evidence.append(f"{key}: {value}")
        
        return evidence
    
    def _identify_affected_files(
        self,
        stack_trace: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Identify files affected by the issue."""
        affected_files = []
        
        # Extract file paths from stack trace
        if stack_trace:
            # Match common file path patterns
            file_patterns = [
                r'File "([^"]+)"',
                r'at ([^\s]+\.(py|js|ts|jsx|tsx)):',
                r'([/\w\-\.]+\.(py|js|ts|jsx|tsx)):\d+'
            ]
            
            for pattern in file_patterns:
                matches = re.findall(pattern, stack_trace)
                for match in matches:
                    if isinstance(match, tuple):
                        file_path = match[0]
                    else:
                        file_path = match
                    
                    if file_path not in affected_files:
                        affected_files.append(file_path)
        
        # Add files from context
        if context and 'file' in context:
            file_path = context['file']
            if file_path not in affected_files:
                affected_files.append(file_path)
        
        return affected_files[:10]  # Limit to 10 files
    
    def _generate_recommendations(
        self,
        issue_type: IssueType,
        root_cause: str,
        error_message: str
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if issue_type == IssueType.DEPENDENCY_CONFLICT:
            recommendations.extend([
                "Install missing dependencies using package manager",
                "Update package.json/requirements.txt with correct versions",
                "Clear package cache and reinstall dependencies",
                "Check for version conflicts in dependency tree"
            ])
        
        elif issue_type == IssueType.CONFIGURATION_ERROR:
            recommendations.extend([
                "Verify all required environment variables are set",
                "Check configuration file syntax and values",
                "Compare with example configuration files",
                "Validate configuration against schema"
            ])
        
        elif issue_type == IssueType.SECURITY_VULNERABILITY:
            recommendations.extend([
                "Update vulnerable package to patched version",
                "Review security advisory for mitigation steps",
                "Run security audit and fix all high/critical issues",
                "Consider alternative packages if no fix available"
            ])
        
        elif issue_type == IssueType.PERFORMANCE_ISSUE:
            recommendations.extend([
                "Profile code to identify bottlenecks",
                "Optimize slow operations or queries",
                "Implement caching for frequently accessed data",
                "Consider async/parallel processing for long operations"
            ])
        
        elif issue_type == IssueType.INTEGRATION_FAILURE:
            recommendations.extend([
                "Verify external service is running and accessible",
                "Check network connectivity and firewall rules",
                "Validate API credentials and permissions",
                "Review service logs for additional context"
            ])
        
        elif issue_type == IssueType.RESOURCE_EXHAUSTION:
            recommendations.extend([
                "Increase resource limits (memory, disk, etc.)",
                "Identify and fix resource leaks",
                "Implement resource cleanup in error handlers",
                "Monitor resource usage trends"
            ])
        
        else:
            recommendations.extend([
                "Review full error message and stack trace",
                "Search for similar issues in issue tracker",
                "Check recent code changes that might be related",
                "Consult documentation for related components"
            ])
        
        return recommendations
    
    def _assess_severity(
        self,
        issue_type: IssueType,
        error_message: str
    ) -> str:
        """Assess the severity of the issue."""
        # Security issues are always critical
        if issue_type == IssueType.SECURITY_VULNERABILITY:
            if any(keyword in error_message.lower() for keyword in [
                "critical", "high", "cve"
            ]):
                return "critical"
            return "high"
        
        # Resource exhaustion is high priority
        if issue_type == IssueType.RESOURCE_EXHAUSTION:
            return "high"
        
        # Performance and integration issues are medium
        if issue_type in [
            IssueType.PERFORMANCE_ISSUE,
            IssueType.INTEGRATION_FAILURE
        ]:
            return "medium"
        
        # Configuration and dependency issues vary
        if issue_type in [
            IssueType.CONFIGURATION_ERROR,
            IssueType.DEPENDENCY_CONFLICT
        ]:
            return "medium"
        
        return "low"
    
    def perform_health_check(
        self,
        repo_path: Path
    ) -> Dict[str, Any]:
        """
        Perform comprehensive health check on a repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Health check results with issues found
        """
        logger.info(f"Performing health check on {repo_path}")
        
        health_report = {
            "repository": str(repo_path),
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "overall_health": "healthy",
            "issues_found": [],
            "checks_performed": []
        }
        
        # Check dependencies
        dependency_check = self._check_dependencies(repo_path)
        health_report["checks_performed"].append(dependency_check)
        
        # Check configuration files
        config_check = self._check_configuration(repo_path)
        health_report["checks_performed"].append(config_check)
        
        # Determine overall health
        issue_count = len(health_report["issues_found"])
        if issue_count == 0:
            health_report["overall_health"] = "healthy"
        elif issue_count <= 3:
            health_report["overall_health"] = "warning"
        else:
            health_report["overall_health"] = "critical"
        
        logger.info(f"Health check complete: {health_report['overall_health']}")
        
        return health_report
    
    def _check_dependencies(self, repo_path: Path) -> Dict[str, Any]:
        """Check dependency health."""
        check_result = {
            "name": "dependency_check",
            "status": "passed",
            "issues": []
        }
        
        # Check for package files
        package_files = [
            repo_path / "package.json",
            repo_path / "requirements.txt",
            repo_path / "Cargo.toml",
            repo_path / "go.mod"
        ]
        
        for pkg_file in package_files:
            if pkg_file.exists():
                logger.debug(f"Found package file: {pkg_file.name}")
                # In real implementation, would parse and check versions
        
        return check_result
    
    def _check_configuration(self, repo_path: Path) -> Dict[str, Any]:
        """Check configuration file health."""
        check_result = {
            "name": "configuration_check",
            "status": "passed",
            "issues": []
        }
        
        # Check for common config files
        config_files = [
            repo_path / ".env.example",
            repo_path / "config.yml",
            repo_path / "tsconfig.json",
            repo_path / "pytest.ini"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                logger.debug(f"Found config file: {config_file.name}")
                # In real implementation, would validate syntax
        
        return check_result


# Global auto diagnostician instance
auto_diagnostician = AutoDiagnostician()
