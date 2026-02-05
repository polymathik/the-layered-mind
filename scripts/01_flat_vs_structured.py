"""
01_flat_vs_structured.py
========================
The Layered Mind — Part 1 Companion Script

Demonstrates the fundamental difference between querying flat/unstructured
knowledge (keyword search over text) vs. structured knowledge (graph traversal).

Question we'll answer both ways:
    "Who works at an organization that uses Python?"

Install: pip install networkx
Run:     python 01_flat_vs_structured.py
"""

import networkx as nx
from typing import List, Dict


# ============================================================================
# APPROACH 1: Flat / Unstructured Knowledge (Keyword Search)
# ============================================================================

def build_flat_knowledge() -> List[Dict[str, str]]:
    """
    Simulates unstructured knowledge — like documents in a vector store
    or rows in a spreadsheet. Each 'document' is a text blob about a person.
    """
    return [
        {
            "id": "doc_1",
            "text": "Alice is a software engineer at TechCorp. "
                    "She specializes in backend systems and distributed computing."
        },
        {
            "id": "doc_2",
            "text": "Bob works at DataLab as a data scientist. "
                    "He enjoys using statistical methods and machine learning."
        },
        {
            "id": "doc_3",
            "text": "TechCorp is a technology company that builds cloud platforms. "
                    "Their tech stack includes Python, Go, and Kubernetes."
        },
        {
            "id": "doc_4",
            "text": "DataLab specializes in analytics. "
                    "They primarily use R and SQL for their projects."
        },
        {
            "id": "doc_5",
            "text": "Carol is a researcher at OpenMind Labs. "
                    "She focuses on natural language processing."
        },
        {
            "id": "doc_6",
            "text": "OpenMind Labs is an AI research organization. "
                    "They use Python and PyTorch extensively."
        },
    ]


def keyword_search(documents: List[Dict], keyword: str) -> List[str]:
    """
    Simple keyword search — finds documents containing the keyword.
    This is a simplified version of what happens in text-based retrieval.
    """
    return [doc["id"] for doc in documents if keyword.lower() in doc["text"].lower()]


def flat_approach():
    """
    Try to answer: "Who works at an organization that uses Python?"
    using only keyword search over flat documents.
    """
    print("=" * 65)
    print("APPROACH 1: Flat Knowledge (Keyword Search)")
    print("=" * 65)
    print()
    print('Question: "Who works at an organization that uses Python?"')
    print()

    docs = build_flat_knowledge()

    # Step 1: Search for "Python"
    python_docs = keyword_search(docs, "Python")
    print(f"Step 1 — Search for 'Python': found in {python_docs}")
    for doc_id in python_docs:
        doc = next(d for d in docs if d["id"] == doc_id)
        print(f"  {doc_id}: {doc['text'][:80]}...")
    print()

    # The problem: We found docs mentioning Python (TechCorp, OpenMind Labs),
    # but we can't automatically link these to the PEOPLE who work there.
    # We'd need a second search, then manual/heuristic joining.

    print("Step 2 — Problem: We found organizations using Python, but")
    print("         linking them to people requires heuristic matching.")
    print("         'Alice' appears in doc_1, 'TechCorp' in doc_1 and doc_3...")
    print("         We'd need NLP/co-reference resolution to connect them.")
    print()

    # Attempt: search for people in Python-org docs? Won't work directly.
    print("Result:  Keyword search CANNOT directly answer relational questions.")
    print("         It finds relevant documents, but can't traverse relationships.")
    print()


# ============================================================================
# APPROACH 2: Structured Knowledge (Knowledge Graph)
# ============================================================================

def build_knowledge_graph() -> nx.DiGraph:
    """
    Builds the same knowledge as a directed graph with typed edges.
    Each edge (triple) represents: Subject --predicate--> Object
    """
    G = nx.DiGraph()

    # --- Nodes with types (this is a mini ontology!) ---
    G.add_node("Alice",       type="Person",       role="Software Engineer")
    G.add_node("Bob",         type="Person",       role="Data Scientist")
    G.add_node("Carol",       type="Person",       role="Researcher")
    G.add_node("TechCorp",    type="Organization", domain="Cloud Platforms")
    G.add_node("DataLab",     type="Organization", domain="Analytics")
    G.add_node("OpenMind",    type="Organization", domain="AI Research")
    G.add_node("Python",      type="Technology")
    G.add_node("Go",          type="Technology")
    G.add_node("R",           type="Technology")
    G.add_node("SQL",         type="Technology")
    G.add_node("PyTorch",     type="Technology")
    G.add_node("Kubernetes",  type="Technology")

    # --- Edges (triples): Subject --predicate--> Object ---
    # People work at organizations
    G.add_edge("Alice", "TechCorp",  relation="worksAt")
    G.add_edge("Bob",   "DataLab",   relation="worksAt")
    G.add_edge("Carol", "OpenMind",  relation="worksAt")

    # Organizations use technologies
    G.add_edge("TechCorp", "Python",     relation="uses")
    G.add_edge("TechCorp", "Go",         relation="uses")
    G.add_edge("TechCorp", "Kubernetes", relation="uses")
    G.add_edge("DataLab",  "R",          relation="uses")
    G.add_edge("DataLab",  "SQL",        relation="uses")
    G.add_edge("OpenMind", "Python",     relation="uses")
    G.add_edge("OpenMind", "PyTorch",    relation="uses")

    return G


def graph_query_who_uses(G: nx.DiGraph, technology: str) -> List[dict]:
    """
    Answer: "Who works at an organization that uses {technology}?"

    This traverses the graph:
        Person --worksAt--> Organization --uses--> Technology

    This is a 2-hop traversal: we follow edges by type to connect
    people to technologies through organizations.
    """
    results = []

    # Find all organizations that use the given technology
    orgs_using_tech = [
        source for source, target, data in G.edges(data=True)
        if data.get("relation") == "uses" and target == technology
    ]

    # Find all people who work at those organizations
    for org in orgs_using_tech:
        people = [
            source for source, target, data in G.edges(data=True)
            if data.get("relation") == "worksAt" and target == org
        ]
        for person in people:
            results.append({
                "person": person,
                "organization": org,
                "person_role": G.nodes[person].get("role", "Unknown"),
            })

    return results


def graph_approach():
    """
    Answer the same question using structured knowledge graph traversal.
    """
    print("=" * 65)
    print("APPROACH 2: Structured Knowledge (Knowledge Graph)")
    print("=" * 65)
    print()
    print('Question: "Who works at an organization that uses Python?"')
    print()

    G = build_knowledge_graph()

    # Print the graph structure for visibility
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print()
    print("Triples (a sample):")
    for u, v, data in list(G.edges(data=True))[:6]:
        print(f"  ({u}) --{data['relation']}--> ({v})")
    print("  ...")
    print()

    # Query: 2-hop traversal
    print("Traversal path: Person --worksAt--> Org --uses--> Python")
    print()

    results = graph_query_who_uses(G, "Python")

    print("Results:")
    for r in results:
        print(f"  ✓ {r['person']} ({r['person_role']}) at {r['organization']}")
    print()

    # Bonus: answer a more complex question
    print("-" * 65)
    print('Bonus: "What technologies are used by organizations where')
    print('        Alice or Carol work?"')
    print()

    for person in ["Alice", "Carol"]:
        orgs = [t for s, t, d in G.edges(data=True)
                if s == person and d["relation"] == "worksAt"]
        for org in orgs:
            techs = [t for s, t, d in G.edges(data=True)
                     if s == org and d["relation"] == "uses"]
            print(f"  {person} --worksAt--> {org} --uses--> {techs}")
    print()


# ============================================================================
# APPROACH 3: A Glimpse of Ontological Thinking
# ============================================================================

def ontological_approach():
    """
    Shows how even a tiny ontology (type hierarchy + constraints) adds
    reasoning power on top of the raw graph.
    """
    print("=" * 65)
    print("APPROACH 3: A Glimpse of Ontological Structure")
    print("=" * 65)
    print()

    G = build_knowledge_graph()

    # Define a mini ontology (type hierarchy)
    ontology = {
        "Entity": {
            "children": ["Agent", "Artifact"],
        },
        "Agent": {
            "children": ["Person", "Organization"],
            "description": "Something that can act or make decisions",
        },
        "Artifact": {
            "children": ["Technology"],
            "description": "Something created by agents",
        },
    }

    print("Mini Ontology (Type Hierarchy):")
    print()
    print("  Entity")
    print("  ├── Agent                (can act / make decisions)")
    print("  │   ├── Person")
    print("  │   └── Organization")
    print("  └── Artifact             (created by agents)")
    print("      └── Technology")
    print()

    # With this ontology, we can answer TYPE-LEVEL questions:
    print("Type-level reasoning enabled:")
    print()

    # Q: "What types of Agents exist in our graph?"
    agent_types = ["Person", "Organization"]  # from ontology
    for agent_type in agent_types:
        instances = [n for n, d in G.nodes(data=True) if d.get("type") == agent_type]
        print(f"  Agents of type '{agent_type}': {instances}")

    print()

    # Q: "What relationships exist between Agents and Artifacts?"
    print("  Relationships between Agents and Artifacts:")
    agent_nodes = {n for n, d in G.nodes(data=True) if d.get("type") in agent_types}
    artifact_nodes = {n for n, d in G.nodes(data=True) if d.get("type") == "Technology"}

    for u, v, data in G.edges(data=True):
        if u in agent_nodes and v in artifact_nodes:
            print(f"    ({u}) --{data['relation']}--> ({v})")

    print()
    print("Key insight: The ontology lets us reason about TYPES of things,")
    print("not just individual instances. An agent using this ontology can ask:")
    print('  "What can Agents do with Artifacts?" → Answer: they can \'use\' them')
    print('  "What Agents exist?" → Answer: Persons and Organizations')
    print()
    print("This is the seed of ontological stratification — defining concepts")
    print("at different levels of abstraction so agents can reason at the")
    print("right level for the task at hand.")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print()
    print("THE LAYERED MIND — Part 1: Flat vs. Structured Knowledge")
    print("=" * 65)
    print()

    flat_approach()
    print()
    graph_approach()
    print()
    ontological_approach()

    print()
    print("=" * 65)
    print("SUMMARY")
    print("=" * 65)
    print()
    print("  Keyword Search:   Finds documents, can't traverse relationships")
    print("  Knowledge Graph:  Traverses relationships, answers structural queries")
    print("  Ontology:         Adds type-level reasoning — the foundation for")
    print("                    agents that understand domain structure")
    print()
    print("  Next up (Part 2): Building knowledge graphs from triples")
    print()
