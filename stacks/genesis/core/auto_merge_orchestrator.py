"""
Auto-Merge Orchestrator - Comprehensive Branch Merging System

This module orchestrates the entire branch merging process including:
- Branch analysis
- Conflict resolution
- Testing
- Auto-healing
- Squashing
- Merging to main
- Branch cleanup
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from genesis.core.branch_manager import BranchManager, BranchHealth


class AutoMergeOrchestrator:
    """Orchestrates automatic branch merging with full validation"""
    
    def __init__(self, repo_path: str = None):
        if repo_path is None:
            repo_path = os.environ.get("GENESIS_REPO_PATH", str(Path(__file__).parent.parent.parent.parent))
        self.manager = BranchManager(repo_path)
        self.repo_path = Path(repo_path)
        self.results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "branches_analyzed": 0,
            "branches_merged": 0,
            "branches_failed": 0,
            "branches_skipped": 0,
            "details": {}
        }
    
    def analyze_all(self) -> Dict[str, Dict]:
        """Analyze all branches"""
        print("🔍 Analyzing all branches...")
        analyses = self.manager.analyze_all_branches()
        self.results["branches_analyzed"] = len(analyses)
        
        # Print summary
        print(f"\n📊 Found {len(analyses)} branches to analyze")
        for branch, analysis in analyses.items():
            status_icon = "✅" if analysis["health"] == BranchHealth.HEALTHY else "⚠️"
            print(f"  {status_icon} {branch}: {analysis['commit_count']} commits, "
                  f"{analysis['diff_stats'].get('files_changed', 0)} files")
        
        return analyses
    
    def test_all_branches(self, branches: List[str]) -> Dict[str, bool]:
        """Test all branches"""
        results = {}
        
        print("\n🧪 Testing all branches...")
        for branch in branches:
            print(f"  Testing {branch}...", end=" ")
            success, output = self.manager.test_branch(branch)
            results[branch] = success
            
            if success:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                # Print last 20 lines of output
                lines = output.split('\n')
                print("    Last errors:")
                for line in lines[-20:]:
                    if line.strip():
                        print(f"      {line}")
        
        return results
    
    def merge_branches_sequentially(self, branches: List[str], test_results: Dict[str, bool]) -> Dict[str, Tuple[bool, str]]:
        """Merge branches one by one to main"""
        merge_results = {}
        
        print("\n🔀 Merging branches to main...")
        
        # Filter to only healthy, passing branches
        branches_to_merge = [
            b for b in branches 
            if test_results.get(b, False)
        ]
        
        if not branches_to_merge:
            print("  ⚠️  No branches ready to merge")
            return merge_results
        
        for branch in branches_to_merge:
            print(f"\n  📦 Merging {branch}...")
            
            # Check one more time for conflicts
            has_conflicts, conflicts = self.manager.check_conflicts(branch, "main")
            
            if has_conflicts:
                print(f"    ⚠️  Conflicts detected, skipping")
                merge_results[branch] = (False, f"Conflicts: {', '.join(conflicts)}")
                self.results["branches_skipped"] += 1
                continue
            
            # Merge with squash
            success, message = self.manager.merge_branch_to_main(branch, squash=True)
            merge_results[branch] = (success, message)
            
            if success:
                print(f"    ✅ Merged successfully")
                self.results["branches_merged"] += 1
                
                # Run tests on main after merge
                print(f"    🧪 Running tests on main...")
                original_branch = self.manager.current_branch
                
                # Switch to main and test
                self.manager._run_command(["git", "checkout", "main"])
                test_success, test_output = self.manager.run_tests()
                
                # Switch back
                self.manager._run_command(["git", "checkout", original_branch])
                
                if test_success:
                    print(f"    ✅ Tests passed on main")
                    
                    # Push to main
                    print(f"    ⬆️  Pushing to main...")
                    code, _, _ = self.manager._run_command(
                        ["git", "push", "origin", "main"],
                        check=False
                    )
                    if code == 0:
                        print(f"    ✅ Pushed successfully")
                    else:
                        print(f"    ⚠️  Push failed")
                else:
                    print(f"    ❌ Tests failed on main, rolling back...")
                    # Reset main
                    self.manager._run_command(["git", "reset", "--hard", "HEAD~1"])
                    merge_results[branch] = (False, "Tests failed after merge")
                    self.results["branches_failed"] += 1
            else:
                print(f"    ❌ Merge failed: {message}")
                self.results["branches_failed"] += 1
        
        return merge_results
    
    def cleanup_merged_branches(self, merge_results: Dict[str, Tuple[bool, str]]):
        """Delete successfully merged branches"""
        print("\n🧹 Cleaning up merged branches...")
        
        for branch, (success, message) in merge_results.items():
            if success:
                print(f"  Deleting {branch}...", end=" ")
                del_success, del_message = self.manager.delete_branch(branch, force=False)
                
                if del_success:
                    print("✅ Deleted")
                else:
                    print(f"⚠️  {del_message}")
    
    def run_full_orchestration(self, cleanup: bool = False) -> Dict:
        """Run the complete orchestration process"""
        print("=" * 60)
        print("🚀 AUTO-MERGE ORCHESTRATOR")
        print("=" * 60)
        
        # Step 1: Analyze all branches
        analyses = self.analyze_all()
        self.results["details"] = analyses
        
        # Step 2: Identify branches to process
        branches_to_process = [
            branch for branch, analysis in analyses.items()
            if analysis["commit_count"] > 0 and 
               analysis["health"] != BranchHealth.CONFLICTED and
               branch != "main"
        ]
        
        if not branches_to_process:
            print("\n✅ No branches need processing")
            self.results["completed_at"] = datetime.now(timezone.utc).isoformat()
            return self.results
        
        # Step 3: Test all branches
        test_results = self.test_all_branches(branches_to_process)
        
        # Step 4: Merge branches
        merge_results = self.merge_branches_sequentially(branches_to_process, test_results)
        
        # Step 5: Cleanup if requested
        if cleanup:
            self.cleanup_merged_branches(merge_results)
        
        # Step 6: Final summary
        self.results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)
        print(f"✅ Branches merged: {self.results['branches_merged']}")
        print(f"❌ Branches failed: {self.results['branches_failed']}")
        print(f"⏭️  Branches skipped: {self.results['branches_skipped']}")
        print("=" * 60)
        
        return self.results
    
    def save_results(self, filepath: str = None):
        """Save results to a JSON file"""
        if filepath is None:
            filepath = self.repo_path / "auto_merge_results.json"
        else:
            filepath = Path(filepath)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filepath}")


def main():
    """Main CLI entry point"""
    orchestrator = AutoMergeOrchestrator()
    
    # Parse command line arguments
    cleanup = "--cleanup" in sys.argv or "-c" in sys.argv
    save = "--save" in sys.argv or "-s" in sys.argv
    
    # Run orchestration
    results = orchestrator.run_full_orchestration(cleanup=cleanup)
    
    # Save results if requested
    if save:
        orchestrator.save_results()
    
    # Exit with appropriate code
    if results["branches_failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
