import datetime
import typer
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from app.db.models import Base
from app.db.session import engine, SessionLocal
from app.db.models import Company
from app.graph.workflow import main_workflow
from app.graph.state import GraphState

# This is the raw text from the provided documents
# In a real app, this might be loaded from a file or a database
MEDICAPITAL_ICP_TEXT = """
Sectoren leveranciers / gebruikers van Duurzaam => energie voorzieningen / infrastructuur en Healthcare => Medisch (diagnose & behandeling) => Verpleeg => Laboratorium / onderzoek => Sport => Wellness / beauty.
Producten duurzaam: Batterijen, zonnepanelen, laadpalen, LED, infraroodpanelen, ge-electrificeerd bouwmaterieel, boilers, warmtepomp, airco, etc.
Producten healthcare: Medische en laboratorium apparatuur / inrichten zoals Ultrasound, holters, ecg, lasers maar ook behandeltafels, stoelen etc.
Ideale contact bij leveranciers (Duurzaam en healthcare) is de sales verantwoordelijke / eigenaar.
Ideale contact bij klanten / gebruikers van units is dat (project-)verantwoordelijke voor operations/ finance manager bij grotere bedrijven of eigenaar van kleinere bedrijven (< 10 man personeel).
Vereisten klant: B2B, geregistreerd in NL / BE. Financieel: minimale bestaansduur 1,5 jaar, omzet in relatie tot investering (3 x), winstgevend, positief vermogen en werkkapitaal.
Investering minimaal bedrag per unit 2.500,- euro, optimaal bedrag 35.000 tot 125.000.
"""

cli = typer.Typer()


def load_icp_text() -> str:
    """Loads the ICP text from an external file."""
    icp_path = Path(__file__).parent.parent / "prompts" / "icp.txt"
    try:
        return icp_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("FATAL: icp.txt not found in prompts/ directory.")
        raise typer.Exit(code=1)


def run_lead_generation_for_country(country_code: str):
    """Executes the full lead generation workflow for a given country."""
    print(f"\n{'=' * 50}")
    print(f"🚀 STARTING LEAD GENERATION RUN FOR: {country_code.upper()} 🚀")
    print(f"{'=' * 50}\n")

    initial_state = GraphState(
        raw_icp_text=load_icp_text(), target_country=country_code
    )

    # The .stream() method is useful for observing the state at each step
    final_state = None
    for event in main_workflow.stream(initial_state):
        state_key = list(event.keys())[0]
        final_state = event[state_key]
        print(f"\n--- Just finished {state_key} ---")

    print(f"\n{'=' * 50}")
    print(f"🏁 LEAD GENERATION RUN FOR {country_code.upper()} COMPLETE 🏁")
    saved = final_state.get("newly_saved_leads_count", 0)
    print(f"✅ New Leads Saved: {saved}")
    print(f"{'=' * 50}\n")


@cli.command()
def run_once(
    country: str = typer.Option("NL", help="Country to target ('NL' or 'BE')."),
):
    """Run the lead generation process one time for the specified country."""
    if country.upper() not in ["NL", "BE"]:
        print("Error: Country must be 'NL' or 'BE'.")
        raise typer.Exit()
    run_lead_generation_for_country(country.upper())


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
    scheduler.add_job(
        run_lead_generation_for_country,
        "interval",
        hours=interval_hours,
        args=["BE"],
        id="be_run",
        # Start the BE run halfway through the interval
        next_run_time=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=interval_hours / 2),
    )

    print(
        f"📅 Scheduler started. Running every {interval_hours} hours for NL and BE (offset)."
    )
    print("Press Ctrl+C to exit.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler stopped.")


@cli.command()
def create_db():
    """Creates the database tables based on the models."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")


@cli.command()
def view_leads():
    """View all leads in the database."""
    db = SessionLocal()
    try:
        leads = db.query(Company).order_by(Company.created_at.desc()).all()
        if not leads:
            print("No leads found in database.")
            return

        print(f"\n{'=' * 80}")
        print(f"📊 FOUND {len(leads)} LEADS IN DATABASE")
        print(f"{'=' * 80}")

        for i, lead in enumerate(leads, 1):
            print(f"\n[{i}] {lead.discovered_name}")
            print(f"    Country: {lead.country}")
            print(f"    Industry: {lead.primary_industry}")
            print(f"    Status: {lead.status}")
            print(f"    Source: {lead.source_url}")
            print(f"    Reasoning: {lead.initial_reasoning}")
            print(f"    Created: {lead.created_at}")

    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
