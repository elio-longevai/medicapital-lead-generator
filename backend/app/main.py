import datetime
import typer
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
import logging

from app.db.models import Base
from app.db.session import engine, SessionLocal
from app.db.models import Company
from app.graph.workflow import main_workflow
from app.graph.state import GraphState

# --- Logging Setup ---
# Using basicConfig for simplicity, but with a custom format for clean, emoji-enhanced output.
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)
# ---


cli = typer.Typer()


def load_icp_text() -> str:
    """Loads the ICP text from an external file."""
    icp_path = Path(__file__).parent.parent / "prompts" / "icp.txt"
    try:
        return icp_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.critical("❌ FATAL: icp.txt not found in prompts/ directory.")
        raise typer.Exit(code=1)


def run_lead_generation_for_country(country_code: str, query_limit: int | None = None):
    """Executes the full lead generation workflow for a given country."""
    logging.info(f"\n{'=' * 50}")
    logging.info(f"🚀 STARTING LEAD GENERATION RUN FOR: {country_code.upper()} 🚀")
    if query_limit:
        logging.warning(f"⚠️  Query Limit: {query_limit} searches")
    logging.info(f"{'=' * 50}\n")

    initial_state = GraphState(
        raw_icp_text=load_icp_text(),
        target_country=country_code,
        search_query_limit=query_limit,
    )

    # The .stream() method is useful for observing the state at each step
    final_state = None
    for event in main_workflow.stream(initial_state):
        state_key = list(event.keys())[0]
        final_state = event[state_key]
        logging.info(f"--- Just finished {state_key} ---")

    logging.info(f"\n{'=' * 50}")
    logging.info(f"🏁 LEAD GENERATION RUN FOR {country_code.upper()} COMPLETE 🏁")
    saved = final_state.get("newly_saved_leads_count", 0)
    logging.info(f"✅ New Leads Saved: {saved}")
    logging.info(f"{'=' * 50}\n")


@cli.command()
def run_once(
    country: str = typer.Option("NL", help="Country to target ('NL' or 'BE')."),
    query_limit: int = typer.Option(
        None, "--limit", help="Limit the number of search queries to run."
    ),
):
    """Run the lead generation process one time for the specified country."""
    run_lead_generation_for_country(country.upper(), query_limit)


@cli.command()
def start_scheduler(
    interval_hours: int = typer.Option(4, help="Number of hours between runs."),
):
    """
    Start the scheduler to run the lead generation process periodically.
    It will alternate between NL and BE on each run.
    """
    scheduler = BlockingScheduler(timezone="UTC")

    # Schedule the job to run immediately and then at intervals
    scheduler.add_job(
        run_lead_generation_for_country,
        "interval",
        hours=interval_hours,
        args=["NL"],
        id="nl_run",
        # Run immediately on start
        next_run_time=datetime.datetime.now(datetime.timezone.utc),
    )

    logging.info(f"📅 Scheduler started. Running every {interval_hours} hours for NL.")
    logging.info("ℹ️ Press Ctrl+C to exit.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("\n✅ Scheduler stopped.")


@cli.command()
def create_db():
    """Creates the database tables based on the models."""
    logging.info("⚙️  Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logging.info("✅ Done.")


@cli.command()
def view_leads():
    """View all leads in the database."""
    db = SessionLocal()
    try:
        leads = db.query(Company).order_by(Company.created_at.desc()).all()
        if not leads:
            logging.info("🤷 No leads found in database.")
            return

        logging.info(f"\n{'=' * 80}")
        logging.info(f"📊 FOUND {len(leads)} LEADS IN DATABASE")
        logging.info(f"{'=' * 80}")

        for i, lead in enumerate(leads, 1):
            logging.info(f"\n[{i}] {lead.discovered_name}")
            logging.info(f"    Country: {lead.country}")
            logging.info(f"    Industry: {lead.primary_industry}")
            logging.info(f"    Status: {lead.status}")
            logging.info(f"    Source: {lead.source_url}")
            logging.info(f"    Reasoning: {lead.initial_reasoning}")
            logging.info(f"    Created: {lead.created_at}")

    except Exception as e:
        logging.error(f"❌ Error querying database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
