from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph import nodes


def build_workflow():
    """Builds and compiles the LangGraph workflow."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("structure_icp", nodes.structure_icp)
    workflow.add_node("get_used_queries", nodes.get_used_queries)
    workflow.add_node("generate_search_queries", nodes.generate_search_queries)
    workflow.add_node("execute_web_search", nodes.execute_web_search)
    workflow.add_node("triage_and_extract_leads", nodes.triage_and_extract_leads)
    workflow.add_node("scrape_and_enrich_companies", nodes.scrape_and_enrich_companies)
    workflow.add_node("enrich_contact_information", nodes.enrich_contact_information)

    # Add refinement loop nodes
    workflow.add_node("generate_refinement_queries", nodes.generate_refinement_queries)
    workflow.add_node("execute_refinement_search", nodes.execute_refinement_search)
    workflow.add_node(
        "extract_and_merge_missing_info", nodes.extract_and_merge_missing_info
    )

    workflow.add_node("save_leads_to_db", nodes.save_leads_to_db)

    # Define edges
    workflow.set_entry_point("structure_icp")
    workflow.add_edge("structure_icp", "get_used_queries")
    workflow.add_edge("get_used_queries", "generate_search_queries")
    workflow.add_edge("generate_search_queries", "execute_web_search")
    workflow.add_edge("execute_web_search", "triage_and_extract_leads")
    workflow.add_edge("triage_and_extract_leads", "scrape_and_enrich_companies")
    workflow.add_edge("scrape_and_enrich_companies", "enrich_contact_information")

    # Conditional edge for refinement
    workflow.add_conditional_edges(
        "enrich_contact_information",
        nodes.check_enrichment_completeness,
        {
            "refine": "generate_refinement_queries",
            "save": "save_leads_to_db",
        },
    )

    # Refinement loop edges
    workflow.add_edge("generate_refinement_queries", "execute_refinement_search")
    workflow.add_edge("execute_refinement_search", "extract_and_merge_missing_info")

    # After merging, check for completeness again to decide whether to loop or save
    workflow.add_conditional_edges(
        "extract_and_merge_missing_info",
        nodes.check_enrichment_completeness,
        {
            "refine": "generate_refinement_queries",
            "save": "save_leads_to_db",
        },
    )

    workflow.add_edge("save_leads_to_db", END)

    # Compile the graph
    app = workflow.compile()
    return app


# A single, compiled instance to be used by the application
main_workflow = build_workflow()
