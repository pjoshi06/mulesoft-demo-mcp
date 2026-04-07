from sage_agentic.crew import SageAgentic


def run():
    inputs = {
        "incident_id": "INC001234",
        "incident_details": (
            "YARN ResourceManager on analytics-cluster "
            "not responding since 02:14 IST. "
            "Finance ETL jobs are queued and not executing."
        )
    }
    SageAgentic().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()