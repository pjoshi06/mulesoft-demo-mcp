from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import MCPServerAdapter

MCP_SERVER_URL = "https://cdp-mcp-server.onrender.com/mcp"

READ_ONLY_TOOLS = [
    "list_environments",
    "describe_environment",
    "get_environment_audit_events",
    "list_datalakes",
    "describe_datalake",
    "get_datalake_log_descriptors",
    "list_datahubs",
    "describe_datahub",
    "get_datahub_diagnostics",
    "collect_datalake_diagnostics",
    "collect_datahub_diagnostics",
]


@CrewBase
class SageAgentic:
    """SAGE — CDP Incident Management Crew"""

    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    def __init__(self):
        self.mcp_adapter = MCPServerAdapter(
            {"url": MCP_SERVER_URL, "transport": "streamable-http"}
        )
        self.mcp_adapter.__enter__()

        self.diagnostic_tools = [
            t for t in self.mcp_adapter.tools
            if t.name in READ_ONLY_TOOLS
        ]
        print(f"\nMCP Connected. Tools loaded: "
              f"{[t.name for t in self.diagnostic_tools]}\n")

    def __del__(self):
        try:
            self.mcp_adapter.__exit__(None, None, None)
        except Exception:
            pass

    @agent
    def incident_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["incident_manager"],
            verbose=True
        )

    @agent
    def cdp_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["cdp_specialist"],
            tools=self.diagnostic_tools,
            verbose=True
        )

    @task
    def incident_triage_task(self) -> Task:
        return Task(config=self.tasks_config["incident_triage_task"])

    @task
    def cdp_diagnostic_task(self) -> Task:
        return Task(config=self.tasks_config["cdp_diagnostic_task"])

    @task
    def incident_summary_task(self) -> Task:
        return Task(config=self.tasks_config["incident_summary_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )