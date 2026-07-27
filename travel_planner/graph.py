"""Graph wiring — specialists → synthesizer → budget evaluator/optimizer loop."""

from langgraph.graph import END, START, StateGraph

from travel_planner.agents.activities import activity_agent
from travel_planner.agents.flights import flight_agent
from travel_planner.agents.hotels import hotel_agent
from travel_planner.evaluator import evaluator, route_budget
from travel_planner.optimizer import optimizer
from travel_planner.orchestrator import orchestrator
from travel_planner.state import TravelState
from travel_planner.synthesizer import synthesizer


def build_graph():
    builder = StateGraph(TravelState)

    builder.add_node("orchestrator", orchestrator)
    builder.add_node("flights", flight_agent)
    builder.add_node("hotels", hotel_agent)
    builder.add_node("activities", activity_agent)
    builder.add_node("synthesizer", synthesizer)
    builder.add_node("evaluator", evaluator)
    builder.add_node("optimizer", optimizer)

    builder.add_edge(START, "orchestrator")
    builder.add_edge("orchestrator", "flights")
    builder.add_edge("flights", "hotels")
    builder.add_edge("hotels", "activities")
    builder.add_edge("activities", "synthesizer")
    builder.add_edge("synthesizer", "evaluator")
    builder.add_conditional_edges(
        "evaluator",
        route_budget,
        {
            "pass": END,
            "revise": "optimizer",
        },
    )
    # Optimizer cheapens picks, then synthesizer rewrites the plan, then evaluate again
    builder.add_edge("optimizer", "synthesizer")

    return builder.compile()
