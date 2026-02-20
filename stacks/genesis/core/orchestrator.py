"""
Orchestrator - The Main Brain of Genesis Autonomous System

This module coordinates all agent activities, manages task distribution,
and maintains system state.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum

from .agent_team import agent_team, AgentPersona


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of autonomous tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Task:
    """Represents an autonomous task in the system."""
    
    def __init__(
        self,
        task_id: str,
        title: str,
        description: str,
        assigned_persona: str,
        priority: int = 1,
        dependencies: Optional[List[str]] = None
    ):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.assigned_persona = assigned_persona
        self.priority = priority
        self.dependencies = dependencies or []
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "assigned_persona": self.assigned_persona,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result
        }


class GenesisOrchestrator:
    """
    The main orchestrator that coordinates all autonomous agents.
    
    This is the "brain" of the Genesis system that:
    - Loads and manages agent personas
    - Distributes tasks to appropriate agents
    - Monitors system health and progress
    - Manages the autonomous recursive loop
    """
    
    def __init__(self, manifest_path: str = "genesis_manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.agent_team = agent_team
        self.tasks: Dict[str, Task] = {}
        self.system_state = self._load_manifest()
        
        logger.info("Genesis Orchestrator initialized")
        logger.info(f"Available personas: {self.agent_team.list_personas()}")
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load the Genesis manifest file."""
        if self.manifest_path.exists():
            with open(self.manifest_path, 'r') as f:
                return json.load(f)
        
        # Initialize default manifest
        return {
            "version": "0.1.0",
            "epoch": 1,
            "status": "initializing",
            "active_agents": [],
            "task_queue": [],
            "metrics": {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "total_commits": 0,
                "total_prs": 0
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def _save_manifest(self) -> None:
        """Save the current system state to manifest."""
        self.system_state["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        with open(self.manifest_path, 'w') as f:
            json.dump(self.system_state, f, indent=2)
        
        logger.info(f"Manifest saved to {self.manifest_path}")
    
    def create_task(
        self,
        title: str,
        description: str,
        assigned_persona: str,
        priority: int = 1,
        dependencies: Optional[List[str]] = None
    ) -> Task:
        """Create a new task and add it to the queue."""
        task_id = f"task_{len(self.tasks) + 1}_{int(datetime.now(timezone.utc).timestamp())}"
        
        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            assigned_persona=assigned_persona,
            priority=priority,
            dependencies=dependencies
        )
        
        self.tasks[task_id] = task
        self.system_state["task_queue"].append(task.to_dict())
        self._save_manifest()
        
        logger.info(f"Created task: {task_id} - {title}")
        return task
    
    def assign_task_to_persona(self, task_id: str, persona_id: str) -> bool:
        """Assign a task to a specific persona."""
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        persona = self.agent_team.get_persona(persona_id)
        if not persona:
            logger.error(f"Persona {persona_id} not found")
            return False
        
        task.assigned_persona = persona_id
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Assigned task {task_id} to {persona.name}")
        return True
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next task to be processed based on priority."""
        pending_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
        ]
        
        if not pending_tasks:
            return None
        
        # Sort by priority (higher first) and creation time
        pending_tasks.sort(
            key=lambda t: (-t.priority, t.created_at)
        )
        
        return pending_tasks[0]
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update the status of a task."""
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        task.status = status
        task.updated_at = datetime.now(timezone.utc).isoformat()
        
        if result:
            task.result = result
        
        # Update metrics
        if status == TaskStatus.COMPLETED:
            self.system_state["metrics"]["tasks_completed"] += 1
        elif status == TaskStatus.FAILED:
            self.system_state["metrics"]["tasks_failed"] += 1
        
        self._save_manifest()
        logger.info(f"Task {task_id} status updated to {status.value}")
        return True
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get the current system health status."""
        total_tasks = len(self.tasks)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        
        return {
            "status": self.system_state["status"],
            "epoch": self.system_state["epoch"],
            "total_tasks": total_tasks,
            "pending_tasks": pending,
            "in_progress_tasks": in_progress,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "active_personas": len(self.system_state["active_agents"]),
            "metrics": self.system_state["metrics"]
        }
    
    def execute_autonomous_cycle(self) -> Dict[str, Any]:
        """
        Execute one cycle of the autonomous loop.
        
        This is the core of the recursive self-improvement system:
        1. Scan repositories for improvement opportunities
        2. Generate tasks based on findings
        3. Assign tasks to appropriate personas
        4. Execute tasks
        5. Validate results
        6. Update system state
        """
        logger.info("=" * 80)
        logger.info("Starting Autonomous Cycle")
        logger.info("=" * 80)
        
        cycle_results = {
            "cycle_id": f"cycle_{int(datetime.now(timezone.utc).timestamp())}",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "tasks_processed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "changes_made": []
        }
        
        try:
            # Step 1: Check for pending tasks
            task = self.get_next_task()
            
            if task:
                logger.info(f"Processing task: {task.title}")
                
                # Get the persona for this task
                persona = self.agent_team.get_persona(task.assigned_persona)
                
                if persona:
                    logger.info(f"Persona: {persona.name} ({persona.role})")
                    
                    # In a real implementation, this would:
                    # 1. Execute the task using the persona's system prompt
                    # 2. Use LLM to generate code/changes
                    # 3. Create PRs via git_manager
                    # For now, we simulate task processing
                    
                    self.update_task_status(
                        task.task_id,
                        TaskStatus.IN_PROGRESS
                    )
                    
                    cycle_results["tasks_processed"] += 1
                    
                    # Simulate task completion
                    logger.info(f"Task {task.task_id} would be executed here")
            else:
                logger.info("No pending tasks found")
            
            # Update epoch
            self.system_state["epoch"] += 1
            self.system_state["status"] = "active"
            self._save_manifest()
            
            cycle_results["completed_at"] = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            logger.error(f"Error in autonomous cycle: {e}", exc_info=True)
            cycle_results["error"] = str(e)
        
        logger.info("=" * 80)
        logger.info("Autonomous Cycle Complete")
        logger.info("=" * 80)
        
        return cycle_results
    
    def initialize_bootstrap_tasks(self) -> List[Task]:
        """Create initial bootstrap tasks for the system."""
        bootstrap_tasks = [
            {
                "title": "Review System Architecture",
                "description": "Analyze the current Genesis system architecture and propose improvements",
                "persona": "chief_architect",
                "priority": 5
            },
            {
                "title": "Enhance Frontend Dashboard",
                "description": "Improve the Mission Control dashboard with real-time agent status",
                "persona": "frontend_lead",
                "priority": 4
            },
            {
                "title": "Implement API Endpoints",
                "description": "Create RESTful API endpoints for agent communication",
                "persona": "backend_lead",
                "priority": 4
            },
            {
                "title": "Setup Monitoring",
                "description": "Implement system monitoring and alerting",
                "persona": "devsecops_engineer",
                "priority": 3
            },
            {
                "title": "Create Test Suite",
                "description": "Develop comprehensive test suite for core modules",
                "persona": "qa_engineer",
                "priority": 3
            }
        ]
        
        created_tasks = []
        for task_data in bootstrap_tasks:
            task = self.create_task(
                title=task_data["title"],
                description=task_data["description"],
                assigned_persona=task_data["persona"],
                priority=task_data["priority"]
            )
            created_tasks.append(task)
        
        logger.info(f"Created {len(created_tasks)} bootstrap tasks")
        return created_tasks


# Global orchestrator instance
orchestrator = GenesisOrchestrator()
