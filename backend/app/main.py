import datetime
import typer
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
import logging

from app.db.models import Base, Company
from app.db.session import engine, get_db
from app.graph.workflow import main_workflow
from app.graph.state import GraphState

# --- ICP Configuration ---
# This list defines which Ideal Customer Profiles the system will run.
# Each dict contains the file's basename and its target country.
ICP_CONFIG = [
    {
        "name": "sustainability_supplier",
        "country": "NL",
        "file": "icp_sustainability_supplier.txt",
    },
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


def _run_single_icp_workflow(
    icp_name: str,
    raw_icp_text: str,
    country_code: str,
    queries_per_icp: int | None,
):
    """Executes the full lead generation workflow for a single ICP."""
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

    # The .stream() method is useful for observing the state at each step
    final_state = None
    for event in main_workflow.stream(initial_state):
        state_key = list(event.keys())[0]
        final_state = event[state_key]
        # logging.info(f"--- Just finished {state_key} ---") # Optional: for verbose debugging

    logging.info(f"\n{'=' * 50}")
    logging.info(f"🏁 RUN FOR ICP '{icp_name}' COMPLETE 🏁")
    saved = final_state.get("newly_saved_leads_count", 0)
    logging.info(f"✅ New Leads Saved: {saved}")
    logging.info(f"{'=' * 50}\n")


def run_all_icps(queries_per_icp: int | None = None):
    """Iterates through all configured ICPs and runs the workflow for each."""
    for icp_config in ICP_CONFIG:
        raw_icp_text = load_icp_text(icp_config["file"])
        _run_single_icp_workflow(
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
    run_all_icps(queries_per_icp)


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
    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(
        run_all_icps,
        "interval",
        hours=interval_hours,
        kwargs={"queries_per_icp": queries_per_icp},
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
    """Creates the database tables based on the models."""
    logging.info("⚙️  Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logging.info("✅ Done.")


@cli.command(name="list-leads")
def list_leads_command(
    limit: int = typer.Option(20, help="Number of leads to list."),
):
    """List the most recent leads from the database."""
    db = next(get_db())
    try:
        logging.info(f"\n{'=' * 80}")
        logging.info("📋 Querying most recent leads from the database...")

        leads = db.query(Company).order_by(Company.created_at.desc()).limit(limit).all()

        logging.info(f"-> Found {len(leads)} leads.")
        for lead in leads:
            logging.info(f"\n--- Lead: {lead.discovered_name} ---")
            logging.info(f"    ICP: {lead.icp_name or 'N/A'}")
            logging.info(f"    Status: {lead.status}")
            logging.info(f"    Source: {lead.source_url}")
            logging.info(f"    Reasoning: {lead.initial_reasoning}")
            logging.info(f"    Score: {lead.qualification_score or 'N/A'}")
            logging.info(f"    Created: {lead.created_at}")

        logging.info(f"\n{'=' * 80}")

    except Exception as e:
        logging.error(f"❌ Error querying database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
