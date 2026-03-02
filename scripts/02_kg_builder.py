"""
02_kg_builder.py
================
The Layered Mind — Part 2 Companion Script (1 of 2)

Builds a small knowledge graph from scratch using triples, then
demonstrates the three fundamental traversal patterns:
  1. One-hop:   Direct lookup
  2. Two-hop:   Compositional reasoning (the query keyword search can't do)
  3. Path-find: Discovering connections between entities

The graph models people, organizations, technologies, roles, and locations.

Install: pip install networkx
Run:     python 02_kg_builder.py
"""

import networkx as nx
from collections import defaultdict
from typing import List, Tuple, Optional


# ============================================================================
# STEP 1: Define triples — the atoms of our knowledge graph
# ============================================================================

# Each triple is (subject, predicate, object).
# This is ALL the knowledge in the system. No documents, no embeddings.
# Just structured facts.

TRIPLES = [
    # Type assertions — what things ARE
    ("Alice",        "rdf:type",    "Person"),
    ("Bob",          "rdf:type",    "Person"),
    ("Carol",        "rdf:type",    "Person"),
    ("Dave",         "rdf:type",    "Person"),
    ("TechCorp",     "rdf:type",    "Organization"),
    ("DataLab",      "rdf:type",    "Organization"),
    ("OpenMind",     "rdf:type",    "Organization"),
    ("Python",       "rdf:type",    "Technology"),
    ("Go",           "rdf:type",    "Technology"),
    ("R",            "rdf:type",    "Technology"),
    ("SQL",          "rdf:type",    "Technology"),
    ("PyTorch",      "rdf:type",    "Technology"),
    ("Kubernetes",   "rdf:type",    "Technology"),
    ("San Francisco","rdf:type",    "City"),
    ("New York",     "rdf:type",    "City"),
    ("London",       "rdf:type",    "City"),

    # Relationship assertions — how things CONNECT
    ("Alice",    "worksAt",    "TechCorp"),
    ("Bob",      "worksAt",    "DataLab"),
    ("Carol",    "worksAt",    "OpenMind"),
    ("Dave",     "worksAt",    "TechCorp"),

    ("TechCorp", "uses",       "Python"),
    ("TechCorp", "uses",       "Go"),
    ("TechCorp", "uses",       "Kubernetes"),
    ("DataLab",  "uses",       "R"),
    ("DataLab",  "uses",       "SQL"),
    ("DataLab",  "uses",       "Python"),
    ("OpenMind", "uses",       "Python"),
    ("OpenMind", "uses",       "PyTorch"),

    ("TechCorp",  "locatedIn", "San Francisco"),
    ("DataLab",   "locatedIn", "New York"),
    ("OpenMind",  "locatedIn", "London"),

    # Property assertions — attributes
    ("Alice", "hasRole", "Software Engineer"),
    ("Bob",   "hasRole", "Data Scientist"),
    ("Carol", "hasRole", "ML Researcher"),
    ("Dave",  "hasRole", "DevOps Engineer"),

    # Hierarchical assertions — concept structure
    ("Software Engineer", "subClassOf", "Engineer"),
    ("DevOps Engineer",   "subClassOf", "Engineer"),
    ("ML Researcher",     "subClassOf", "Researcher"),
    ("Data Scientist",    "subClassOf", "Researcher"),
    ("Engineer",          "subClassOf", "TechnicalRole"),
    ("Researcher",        "subClassOf", "TechnicalRole"),
]


# ============================================================================
# STEP 2: Build the graph from triples
# ============================================================================

def build_graph(triples: List[Tuple[str, str, str]]) -> nx.DiGraph:
    """
    Construct a directed graph from a list of (subject, predicate, object) triples.
    Each triple becomes a directed edge with the predicate stored as metadata.
    """
    G = nx.DiGraph()
    for subj, pred, obj in triples:
        G.add_edge(subj, obj, relation=pred)
    return G


def print_graph_stats(G: nx.DiGraph):
    """Print basic statistics about the graph."""
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    # Count by relation type
    rel_counts = defaultdict(int)
    for _, _, data in G.edges(data=True):
        rel_counts[data["relation"]] += 1
    print(f"  Edge types:")
    for rel, count in sorted(rel_counts.items()):
        print(f"    {rel}: {count}")


# ============================================================================
# STEP 3: Traversal patterns
# ============================================================================

def one_hop(G: nx.DiGraph, start: str, relation: str) -> List[str]:
    """
    1-hop traversal: follow a single edge type from a starting node.
    Example: "Where does Alice work?" = one_hop(G, "Alice", "worksAt")
    """
    results = []
    for _, target, data in G.edges(start, data=True):
        if data["relation"] == relation:
            results.append(target)
    return results


def one_hop_reverse(G: nx.DiGraph, target: str, relation: str) -> List[str]:
    """
    Reverse 1-hop: find all nodes that point TO a target via a relation.
    Example: "Who works at TechCorp?" = one_hop_reverse(G, "TechCorp", "worksAt")
    """
    results = []
    for source, dest, data in G.edges(data=True):
        if dest == target and data["relation"] == relation:
            results.append(source)
    return results


def two_hop(G: nx.DiGraph, start: str, rel1: str, rel2: str) -> List[Tuple[str, str]]:
    """
    2-hop traversal: follow two edge types in sequence.
    Returns (intermediate, final) pairs so you can see the path.

    Example: "What technologies does Alice's company use?"
             = two_hop(G, "Alice", "worksAt", "uses")
    """
    results = []
    intermediates = one_hop(G, start, rel1)
    for mid in intermediates:
        finals = one_hop(G, mid, rel2)
        for final in finals:
            results.append((mid, final))
    return results


def two_hop_reverse_forward(
    G: nx.DiGraph, target: str, rel1: str, rel2: str
) -> List[Tuple[str, str]]:
    """
    Mixed-direction 2-hop: reverse on first edge, forward on second.

    Example: "Who works at an organization that uses Python?"
             = two_hop_reverse_forward(G, "Python", "uses", "worksAt")
             Reads as: find orgs that --uses--> Python, then people who --worksAt--> those orgs
    """
    results = []
    # Reverse: find orgs that use the target technology
    orgs = one_hop_reverse(G, target, rel1)
    for org in orgs:
        # Forward: find people who work at those orgs
        people = one_hop_reverse(G, org, rel2)
        for person in people:
            results.append((person, org))
    return results


def find_path(G: nx.DiGraph, source: str, target: str) -> Optional[List[str]]:
    """
    Path-finding: discover if and how two nodes are connected.
    Uses BFS to find the shortest path (ignoring edge direction for discovery).
    """
    try:
        undirected = G.to_undirected()
        path = nx.shortest_path(undirected, source, target)
        return path
    except nx.NetworkXNoPath:
        return None


def describe_path(G: nx.DiGraph, path: List[str]) -> str:
    """Given a path of nodes, describe the edges between them."""
    steps = []
    undirected = G.to_undirected()
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        # Check both directions for the edge
        if G.has_edge(a, b):
            rel = G.edges[a, b]["relation"]
            steps.append(f"({a}) --{rel}--> ({b})")
        elif G.has_edge(b, a):
            rel = G.edges[b, a]["relation"]
            steps.append(f"({a}) <--{rel}-- ({b})")
        else:
            steps.append(f"({a}) --- ({b})")
    return "\n    ".join(steps)


# ============================================================================
# STEP 4: Demonstrate the three traversal patterns
# ============================================================================

def demo_one_hop(G: nx.DiGraph):
    print("=" * 65)
    print("PATTERN 1: One-Hop (Direct Lookup)")
    print("=" * 65)
    print()

    # Forward
    print('  Q: "Where does Alice work?"')
    result = one_hop(G, "Alice", "worksAt")
    print(f"  A: {result}")
    print(f"     Traversal: (Alice) --worksAt--> ({result[0]})")
    print()

    # Reverse
    print('  Q: "Who works at TechCorp?"')
    result = one_hop_reverse(G, "TechCorp", "worksAt")
    print(f"  A: {result}")
    for person in result:
        print(f"     Traversal: ({person}) --worksAt--> (TechCorp)")
    print()

    # Multiple results
    print('  Q: "What technologies does TechCorp use?"')
    result = one_hop(G, "TechCorp", "uses")
    print(f"  A: {result}")
    print()
    print("  One-hop = one edge = one fact. Simple lookups.")
    print()


def demo_two_hop(G: nx.DiGraph):
    print("=" * 65)
    print("PATTERN 2: Two-Hop (Compositional Reasoning)")
    print("=" * 65)
    print()

    # The classic: question that keyword search can't answer
    print('  Q: "Who works at an organization that uses Python?"')
    print()
    print("  This requires composing two relationships:")
    print("    Person --worksAt--> Org --uses--> Python")
    print()
    result = two_hop_reverse_forward(G, "Python", "uses", "worksAt")
    print("  Results:")
    for person, org in result:
        print(f"    {person} (via {org})")
    print()

    # Another compositional query
    print('  Q: "What city does Carol\'s organization operate in?"')
    result = two_hop(G, "Carol", "worksAt", "locatedIn")
    for org, city in result:
        print(f"  A: {city} (Carol --worksAt--> {org} --locatedIn--> {city})")
    print()

    print("  Two-hop = composing relationships. This is where structure")
    print("  beats similarity. 'Carol' and 'London' may never appear in")
    print("  the same document, but the graph connects them.")
    print()


def demo_path_finding(G: nx.DiGraph):
    print("=" * 65)
    print("PATTERN 3: Path-Finding (Discovering Connections)")
    print("=" * 65)
    print()

    # How are two distant nodes related?
    pairs = [
        ("Alice", "PyTorch"),
        ("Bob", "San Francisco"),
        ("Carol", "Dave"),
    ]

    for source, target in pairs:
        print(f'  Q: "How are {source} and {target} connected?"')
        path = find_path(G, source, target)
        if path:
            print(f"  A: Path ({len(path) - 1} hops):")
            print(f"    {describe_path(G, path)}")
        else:
            print("  A: No connection found.")
        print()

    print("  Path-finding discovers relationships you didn't ask about.")
    print("  It's exploratory: 'I don't know HOW these are connected,")
    print("  but I suspect they are.'")
    print()


# ============================================================================
# STEP 5: Bonus — type-level reasoning (preview of ontological power)
# ============================================================================

def demo_type_reasoning(G: nx.DiGraph):
    print("=" * 65)
    print("BONUS: Type-Level Reasoning (Why Ontologies Matter)")
    print("=" * 65)
    print()

    # Walk the hierarchy: what kind of role does Alice have?
    print('  Q: "What kind of role does Alice have?"')
    roles = one_hop(G, "Alice", "hasRole")
    role = roles[0]
    print(f"  Direct role: {role}")

    # Walk up the hierarchy
    chain = [role]
    current = role
    while True:
        parents = one_hop(G, current, "subClassOf")
        if not parents:
            break
        current = parents[0]
        chain.append(current)
    print(f"  Type hierarchy: {' -> '.join(chain)}")
    print()

    # Now use the hierarchy to answer a broader question
    print('  Q: "Find all Engineers in the graph"')
    print("  (Using type hierarchy, not just exact role match)")
    print()
    engineers = []
    all_people = one_hop_reverse(G, "Person", "rdf:type")
    for person in all_people:
        roles = one_hop(G, person, "hasRole")
        for r in roles:
            # Walk up the hierarchy to see if this role is a kind of Engineer
            current = r
            while current:
                if current == "Engineer":
                    engineers.append((person, r))
                    break
                parents = one_hop(G, current, "subClassOf")
                current = parents[0] if parents else None

    for person, role in engineers:
        print(f"    {person} ({role})")
    print()
    print("  Neither Alice (Software Engineer) nor Dave (DevOps Engineer)")
    print("  have 'Engineer' as their exact role. But the type hierarchy")
    print("  tells us both ARE engineers. This is the power of ontological")
    print("  structure: reasoning about categories, not just labels.")
    print()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print()
    print("THE LAYERED MIND — Part 2: Building Your First Knowledge Graph")
    print("=" * 65)
    print()

    # Build
    print("Building knowledge graph from triples...")
    G = build_graph(TRIPLES)
    print_graph_stats(G)
    print()

    # Demonstrate the three traversal patterns
    demo_one_hop(G)
    demo_two_hop(G)
    demo_path_finding(G)
    demo_type_reasoning(G)

    # Summary
    print("=" * 65)
    print("SUMMARY")
    print("=" * 65)
    print()
    print(f"  {len(TRIPLES)} triples -> {G.number_of_nodes()} nodes, "
          f"{G.number_of_edges()} edges")
    print()
    print("  1-hop:  Direct lookup (one fact)")
    print("  2-hop:  Compositional reasoning (connecting facts)")
    print("  Path:   Discovery (finding unknown connections)")
    print("  Types:  Ontological reasoning (categories, not just labels)")
    print()
    print("  Next: 02_llm_triple_extraction.py")
    print("        (using LLMs to build knowledge graphs from text)")
    print()
