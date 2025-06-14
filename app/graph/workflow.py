from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph import nodes


def build_workflow():
    """Builds and compiles the LangGraph workflow."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("structure_icp", nodes.structure_icp)
    workflow.add_node("generate_search_queries", nodes.generate_search_queries)
    workflow.add_node("execute_web_search", nodes.execute_web_search)
    workflow.add_node("triage_and_extract_leads", nodes.triage_and_extract_leads)
    workflow.add_node("save_leads_to_db", nodes.save_leads_to_db)

    # Define edges
    workflow.set_entry_point("structure_icp")
    workflow.add_edge("structure_icp", "generate_search_queries")
    workflow.add_edge("generate_search_queries", "execute_web_search")
    workflow.add_edge("execute_web_search", "triage_and_extract_leads")
    workflow.add_edge("triage_and_extract_leads", "save_leads_to_db")
    workflow.add_edge("save_leads_to_db", END)

    # Compile the graph
    app = workflow.compile()
    return app


# A single, compiled instance to be used by the application
main_workflow = build_workflow()
