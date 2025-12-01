"""
Governing Agent: Monitors and tracks all agents
Provides observability and coordination using Google ADK Agent.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class GoverningAgent:
    """
    Governing Agent that monitors and tracks all agents in the workflow.
    Provides centralized observability and generates reports.
    """

    def __init__(self):
        self.name = "GoverningAgent"
        self.description = "Monitors and tracks all agents in the workflow"
        self.execution_log: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

        logger.info(f"✅ {self.name} initialized")

    def start_workflow(self):
        """Mark the start of workflow execution."""
        self.start_time = datetime.now()
        logger.info(f"🚀 {self.name}: Workflow started at {self.start_time}")

    def end_workflow(self):
        """Mark the end of workflow execution."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        logger.info(f"✅ {self.name}: Workflow completed in {duration:.2f}s")

    def log_agent_execution(self, agent_name: str, status: str, details: str = ""):
        """
        Log an agent execution event.

        Args:
            agent_name: Name of the agent
            status: Execution status (STARTED, SUCCESS, FAILED)
            details: Additional details
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "status": status,
            "details": details
        }
        self.execution_log.append(event)

        # Log with appropriate emoji
        emoji = "▶️" if status == "STARTED" else "✅" if status == "SUCCESS" else "❌"
        logger.info(f"{emoji} {self.name}: {agent_name} - {status} {details}")

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive workflow execution report.

        Returns:
            Report dictionary with execution details
        """
        if not self.start_time:
            return {"status": "No workflow executed"}

        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0

        # Count statuses
        status_counts = {}
        for event in self.execution_log:
            status = event["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        # Extract agent names
        agents_executed = list(set(event["agent"] for event in self.execution_log))

        report = {
            "workflow_duration_seconds": duration,
            "total_events": len(self.execution_log),
            "agents_executed": len(agents_executed),
            "agent_names": agents_executed,
            "status_summary": status_counts,
            "execution_timeline": self.execution_log,
            "success_rate": f"{(status_counts.get('SUCCESS', 0) / len(self.execution_log) * 100):.1f}%" if self.execution_log else "N/A"
        }

        return report

    def print_report(self):
        """Print a formatted execution report."""
        report = self.generate_report()

        print("GOVERNING AGENT - WORKFLOW EXECUTION REPORT")
        print(f"\n⏱️  Duration: {report.get('workflow_duration_seconds', 0):.2f} seconds")
        print(f"📊 Total Events: {report.get('total_events', 0)}")
        print(f"🤖 Agents Executed: {report.get('agents_executed', 0)}")
        print(f"✅ Success Rate: {report.get('success_rate', 'N/A')}")

        print("\n📋 Agent List:")
        for agent in report.get('agent_names', []):
            print(f"   • {agent}")

        print("\n📈 Status Summary:")
        for status, count in report.get('status_summary', {}).items():
            print(f"   • {status}: {count}")

        print("\n⏰ Execution Timeline:")
        for event in report.get('execution_timeline', [])[-10:]:  # Last 10 events
            print(f"   [{event['timestamp']}] {event['agent']}: {event['status']} {event['details']}")


