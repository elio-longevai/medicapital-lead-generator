import asyncio
import datetime
import logging
from pathlib import Path

import typer
from apscheduler.schedulers.blocking import BlockingScheduler

from app.db.mongodb import mongodb
from app.db.repositories import CompanyRepository
from app.graph.state import GraphState
from app.graph.workflow import main_workflow

# --- ICP Configuration ---
# This list defines which Ideal Customer Profiles the system will run.
# Each dict contains the file's basename and its target country.
ICP_CONFIG = [
    # {
    #     "name": "sustainability_supplier",
    #     "country": "NL",
    #     "file": "icp_sustainability_supplier.txt",
    # },
    {
        "name": "sustainability_end_user",
        "country": "NL",
        "file": "icp_sustainability_end_user.txt",
    },
    {
        "name": "healthcare_end_user",
        "country": "NL",
        "file": "icp_healthcare_end_user.txt",
    },
]


# --- Logging Setup ---
# Using basicConfig for simplicity, but with a custom format for clean, emoji-enhanced output.
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)
# ---


cli = typer.Typer()


def load_icp_text(filename: str) -> str:
    """Loads the ICP text from a specified file in the prompts directory."""
    icp_path = Path(__file__).parent.parent / "prompts" / filename
    try:
        return icp_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.critical(
            f"❌ FATAL: ICP file '{filename}' not found in prompts/ directory."
        )
        raise typer.Exit(code=1)


async def _arun_single_icp_workflow(
    icp_name: str,
    raw_icp_text: str,
    country_code: str,
    queries_per_icp: int | None,
):
    """Executes the full lead generation workflow for a single ICP asynchronously."""
    logging.info(f"\n{'=' * 50}")
    logging.info(f"🚀 STARTING RUN FOR ICP: {icp_name} ({country_code.upper()}) 🚀")
    if queries_per_icp:
        logging.warning(f"⚠️  Query Limit: {queries_per_icp} searches for this ICP")
    logging.info(f"{'=' * 50}\n")

    initial_state = GraphState(
        icp_name=icp_name,
        raw_icp_text=raw_icp_text,
        target_country=country_code,
        queries_per_icp=queries_per_icp,
    )

    final_state = None
    async for event in main_workflow.astream(initial_state):
        state_key = list(event.keys())[0]
        final_state = event[state_key]
        # logging.info(f"--- Just finished {state_key} ---") # Optional: for verbose debugging

    logging.info(f"\n{'=' * 50}")
    logging.info(f"🏁 RUN FOR ICP '{icp_name}' COMPLETE 🏁")
    saved = final_state.get("newly_saved_leads_count", 0)
    logging.info(f"✅ New Leads Saved: {saved}")
    logging.info(f"{'=' * 50}\n")


async def arun_all_icps(queries_per_icp: int | None = None):
    """Iterates through all configured ICPs and runs the workflow for each."""
    for icp_config in ICP_CONFIG:
        raw_icp_text = load_icp_text(icp_config["file"])
        await _arun_single_icp_workflow(
            icp_name=icp_config["name"],
            raw_icp_text=raw_icp_text,
            country_code=icp_config["country"],
            queries_per_icp=queries_per_icp,
        )


@cli.command()
def run_once(
    queries_per_icp: int = typer.Option(
        5, "--queries-per-icp", help="Limit the number of search queries per ICP."
    ),
):
    """Run the lead generation process one time for all configured ICPs."""
    asyncio.run(arun_all_icps(queries_per_icp))


@cli.command()
def start_scheduler(
    interval_hours: int = typer.Option(4, help="Number of hours between runs."),
    queries_per_icp: int = typer.Option(
        5, "--queries-per-icp", help="Limit the number of search queries per ICP."
    ),
):
    """
    Start a scheduler to run lead generation for all ICPs periodically.
    """

    def sync_run_all_icps():
        """Wrapper to run the async function in a sync context for the scheduler."""
        asyncio.run(arun_all_icps(queries_per_icp))

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        sync_run_all_icps,
        "interval",
        hours=interval_hours,
        id="all_icps_run",
        next_run_time=datetime.datetime.now(datetime.timezone.utc),
    )

    logging.info(
        f"📅 Scheduler started. Running for all ICPs every {interval_hours} hours "
        f"(with a limit of {queries_per_icp} queries per ICP)."
    )
    logging.info("ℹ️ Press Ctrl+C to exit.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Scheduler stopped.")


@cli.command()
def create_db():
    """Creates the database connection and indexes (MongoDB)."""
    logging.info("⚙️  Setting up MongoDB connection and indexes...")
    try:
        # Connect to MongoDB
        mongodb.connect()

        # Create indexes (this is handled by the repositories)
        from app.db.repositories import (
            ApiUsageRepository,
            CompanyRepository,
            LeadRepository,
            SearchQueryRepository,
        )

        # Initialize repositories to ensure indexes are created
        CompanyRepository()
        SearchQueryRepository()
        ApiUsageRepository()
        LeadRepository()

        logging.info("✅ MongoDB setup complete.")
    except Exception as e:
        logging.error(f"❌ Failed to setup MongoDB: {e}")
        raise typer.Exit(code=1)
    finally:
        mongodb.disconnect()


@cli.command(name="list-leads")
def list_leads_command(
    limit: int = typer.Option(20, help="Number of leads to list."),
):
    """List the most recent leads from the database."""
    try:
        company_repo = CompanyRepository()

        logging.info(f"\n{'=' * 80}")
        logging.info("📋 Querying most recent leads from the database...")

        leads = company_repo.get_recent_companies(limit)

        logging.info(f"-> Found {len(leads)} leads.")
        for lead in leads:
            logging.info(f"\n--- Lead: {lead['discovered_name']} ---")
            logging.info(f"    ICP: {lead.get('icp_name', 'N/A')}")
            logging.info(f"    Status: {lead.get('status', 'N/A')}")
            logging.info(f"    Source: {lead.get('source_url', 'N/A')}")
            logging.info(f"    Reasoning: {lead.get('initial_reasoning', 'N/A')}")
            logging.info(f"    Score: {lead.get('qualification_score', 'N/A')}")
            logging.info(f"    Created: {lead.get('created_at', 'N/A')}")

        logging.info(f"\n{'=' * 80}")

    except Exception as e:
        logging.error(f"❌ Error querying database: {e}")


if __name__ == "__main__":
    cli()
