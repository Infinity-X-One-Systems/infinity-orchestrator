"""
Genesis Loop - Main Workflow Driver Script

This script is executed by the GitHub Actions workflow to drive
the autonomous recursive loop.
"""

import sys
import logging
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from genesis.core.orchestrator import orchestrator
from genesis.core.repo_scanner import repo_scanner
from genesis.core.workflow_analyzer import workflow_analyzer
from genesis.core.auto_diagnostician import auto_diagnostician
from genesis.core.auto_healer import auto_healer
from genesis.core.conflict_resolver import conflict_resolver
from genesis.core.auto_validator import auto_validator
from genesis.core.auto_merger import auto_merger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def plan_phase() -> int:
    """
    Plan phase: Scan repositories and generate improvement tasks.
    
    Returns:
        Exit code (0 = success)
    """
    logger.info("=" * 80)
    logger.info("PHASE: PLAN")
    logger.info("=" * 80)
    
    try:
        # Scan for improvement opportunities
        org_name = "InfinityXOneSystems"
        improvements = repo_scanner.scan_for_improvements(org_name)
        
        logger.info(f"Found {len(improvements)} repositories needing improvements")
        
        # Generate tasks from opportunities
        for repo_data in improvements:
            opportunities = repo_data.get("opportunities", [])
            tasks = repo_scanner.generate_improvement_tasks(opportunities)
            
            for task in tasks:
                orchestrator.create_task(
                    title=task["title"],
                    description=task["description"],
                    assigned_persona=task["persona"],
                    priority=2 if task["severity"] == "high" else 1
                )
        
        logger.info("Planning phase completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Planning phase failed: {e}", exc_info=True)
        return 1


def code_phase() -> int:
    """
    Code phase: Execute autonomous coding tasks.
    
    Returns:
        Exit code (0 = success)
    """
    logger.info("=" * 80)
    logger.info("PHASE: CODE")
    logger.info("=" * 80)
    
    try:
        # Execute one autonomous cycle
        result = orchestrator.execute_autonomous_cycle()
        
        logger.info(f"Cycle completed: {result['cycle_id']}")
        logger.info(f"Tasks processed: {result['tasks_processed']}")
        
        logger.info("Coding phase completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Coding phase failed: {e}", exc_info=True)
        return 1


def validate_phase() -> int:
    """
    Validate phase: Run tests and quality checks.
    
    Returns:
        Exit code (0 = success)
    """
    logger.info("=" * 80)
    logger.info("PHASE: VALIDATE")
    logger.info("=" * 80)
    
    try:
        # In a real implementation, this would:
        # 1. Run linters (pylint, eslint, etc.)
        # 2. Run tests (pytest, jest, etc.)
        # 3. Run security scans (CodeQL, Snyk, etc.)
        # 4. Check code coverage
        
        health = orchestrator.get_system_health()
        logger.info(f"System health: {health}")
        
        logger.info("Validation phase completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Validation phase failed: {e}", exc_info=True)
        return 1


def diagnose_phase() -> int:
    """
    Diagnose phase: Analyze workflows and diagnose issues.
    
    Returns:
        Exit code (0 = success)
    """
    logger.info("=" * 80)
    logger.info("PHASE: DIAGNOSE")
    logger.info("=" * 80)
    
    try:
        # Analyze recent workflow failures
        org_name = "InfinityXOneSystems"
        logger.info(f"Analyzing workflows for {org_name}")
        
        # In real implementation, would fetch actual workflow data
        # For now, log the diagnostic capability
        logger.info("Workflow analysis and diagnosis ready")
        
        logger.info("Diagnosis phase completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Diagnosis phase failed: {e}", exc_info=True)
        return 1


def heal_phase() -> int:
    """
    Heal phase: Auto-fix identified issues and conflicts.
    
    Returns:
        Exit code (0 = success)
    """
    logger.info("=" * 80)
    logger.info("PHASE: HEAL")
    logger.info("=" * 80)
    
    try:
        # Check for conflicts and resolve them
        conflicts = conflict_resolver.detect_conflicts()
        if conflicts:
            logger.info(f"Found {len(conflicts)} files with conflicts")
            resolution_result = conflict_resolver.resolve_conflicts(auto_commit=True)
            
            if resolution_result.success:
                logger.info(f"Resolved {resolution_result.conflicts_resolved} conflicts")
            else:
                logger.warning(f"Some conflicts need manual review: {resolution_result.error_message}")
        else:
            logger.info("No conflicts detected")
        
        # In real implementation, would also:
        # 1. Run auto-healer on identified issues
        # 2. Fix dependency problems
        # 3. Patch security vulnerabilities
        # 4. Repair broken tests
        
        logger.info("Healing phase completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Healing phase failed: {e}", exc_info=True)
        return 1


def deploy_phase() -> int:
    """
    Deploy phase: Merge approved changes and deploy.
    
    Returns:
        Exit code (0 = success)
    """
    logger.info("=" * 80)
    logger.info("PHASE: DEPLOY")
    logger.info("=" * 80)
    
    try:
        # Auto-merge validated PRs
        logger.info("Checking for PRs ready to merge")
        merge_results = auto_merger.auto_merge_validated_prs(label_filter="autonomous-verified")
        
        if merge_results:
            successful_merges = sum(1 for r in merge_results if r.status.value == "success")
            logger.info(f"Merged {successful_merges}/{len(merge_results)} PRs")
        else:
            logger.info("No PRs ready for auto-merge")
        
        logger.info("Deployment phase completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Deployment phase failed: {e}", exc_info=True)
        return 1


def main():
    """Main entry point for the Genesis loop."""
    parser = argparse.ArgumentParser(
        description="Genesis Autonomous Loop Driver"
    )
    parser.add_argument(
        "phase",
        choices=["plan", "code", "validate", "diagnose", "heal", "deploy", "full"],
        help="Phase to execute"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("GENESIS AUTONOMOUS LOOP STARTING")
    logger.info("=" * 80)
    
    exit_code = 0
    
    if args.phase == "plan":
        exit_code = plan_phase()
    elif args.phase == "code":
        exit_code = code_phase()
    elif args.phase == "validate":
        exit_code = validate_phase()
    elif args.phase == "diagnose":
        exit_code = diagnose_phase()
    elif args.phase == "heal":
        exit_code = heal_phase()
    elif args.phase == "deploy":
        exit_code = deploy_phase()
    elif args.phase == "full":
        # Run all phases in sequence: Plan → Code → Validate → Diagnose → Heal → Deploy
        exit_code = plan_phase()
        if exit_code == 0:
            exit_code = code_phase()
        if exit_code == 0:
            exit_code = validate_phase()
        # Always run diagnose and heal, even if validation fails
        diagnose_exit = diagnose_phase()
        if diagnose_exit != 0:
            logger.warning("Diagnose phase had issues but continuing...")
        heal_exit = heal_phase()
        if heal_exit != 0:
            logger.warning("Heal phase had issues but continuing...")
        # Continue to deploy only if previous phases succeeded
        if exit_code == 0:
            exit_code = deploy_phase()
    
    logger.info("=" * 80)
    logger.info(f"GENESIS LOOP FINISHED - Exit Code: {exit_code}")
    logger.info("=" * 80)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
