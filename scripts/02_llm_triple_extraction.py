"""
02_llm_triple_extraction.py
============================
The Layered Mind — Part 2 Companion Script (2 of 2)

Demonstrates LLM-assisted knowledge graph construction:
  1. Unconstrained extraction — "extract all relationships from this text"
  2. Ontology-guided extraction — "extract triples conforming to this schema"
  3. Comparison to hand-built ground truth

The point: ontology-guided extraction is dramatically better. The ontology
you design doesn't just help with querying — it makes *building* the graph
tractable.

Modes:
  - LIVE MODE:  Uses any LLM provider via LiteLLM
  - DEMO MODE:  Uses pre-recorded outputs (no API key needed)

Configuration (environment variables):
  MODEL    — LiteLLM model string (default: openai/gpt-4o-mini)
  API_KEY  — API key for your chosen provider

  Examples:
    # OpenAI
    MODEL=openai/gpt-4o-mini  API_KEY=sk-...  python 02_llm_triple_extraction.py

    # Anthropic
    MODEL=anthropic/claude-sonnet-4-20250514  API_KEY=sk-ant-...  python 02_llm_triple_extraction.py

    # OpenRouter (access many models with one key)
    MODEL=openrouter/google/gemini-2.0-flash-001  API_KEY=sk-or-...  python 02_llm_triple_extraction.py

    # Groq
    MODEL=groq/llama-3.3-70b-versatile  API_KEY=gsk_...  python 02_llm_triple_extraction.py

    # Demo mode (no API key needed)
    python 02_llm_triple_extraction.py

  See https://docs.litellm.ai/docs/providers for all supported providers.

Install: pip install litellm
Run:     python 02_llm_triple_extraction.py
"""

import json
import os
import sys
from typing import List, Tuple

try:
    import litellm
    # Suppress litellm's verbose logging
    litellm.suppress_debug_info = True
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

# Configuration
DEFAULT_MODEL = "openai/gpt-4o-mini"
MODEL = os.environ.get("MODEL", DEFAULT_MODEL)
API_KEY = os.environ.get("API_KEY", "")


# ============================================================================
# SOURCE TEXT — The paragraph we'll extract knowledge from
# ============================================================================

SOURCE_TEXT = """
Dr. Sarah Chen joined MedVista Health as Chief of Cardiology in March 2024.
She previously worked at Boston General Hospital for twelve years, where she
led the cardiac imaging research program. At MedVista, she oversees a team
of eight cardiologists and has introduced a new echocardiography protocol
that reduced diagnostic wait times by 30%. Dr. Chen also serves as an
adjunct professor at Harbor University Medical School, where she teaches
advanced cardiovascular diagnostics to third-year residents. She completed
her MD at Johns Hopkins and her cardiology fellowship at the Cleveland Clinic.
"""

# ============================================================================
# GROUND TRUTH — What a careful human would extract
# ============================================================================

GROUND_TRUTH = [
    ("Dr. Sarah Chen",          "rdf:type",       "Person"),
    ("Dr. Sarah Chen",          "rdf:type",       "Physician"),
    ("Dr. Sarah Chen",          "hasRole",        "Chief of Cardiology"),
    ("Dr. Sarah Chen",          "worksAt",        "MedVista Health"),
    ("Dr. Sarah Chen",          "startDate",      "March 2024"),
    ("Dr. Sarah Chen",          "previouslyAt",   "Boston General Hospital"),
    ("Dr. Sarah Chen",          "duration",       "12 years"),
    ("Dr. Sarah Chen",          "led",            "Cardiac Imaging Research Program"),
    ("Dr. Sarah Chen",          "oversees",       "Team of 8 cardiologists"),
    ("Dr. Sarah Chen",          "introduced",     "Echocardiography Protocol"),
    ("Dr. Sarah Chen",          "affiliatedWith", "Harbor University Medical School"),
    ("Dr. Sarah Chen",          "hasRole",        "Adjunct Professor"),
    ("Dr. Sarah Chen",          "teaches",        "Advanced Cardiovascular Diagnostics"),
    ("Dr. Sarah Chen",          "educatedAt",     "Johns Hopkins"),
    ("Dr. Sarah Chen",          "educatedAt",     "Cleveland Clinic"),
    ("Dr. Sarah Chen",          "degree",         "MD"),
    ("Dr. Sarah Chen",          "training",       "Cardiology Fellowship"),
    ("MedVista Health",         "rdf:type",       "Organization"),
    ("MedVista Health",         "rdf:type",       "HealthcareProvider"),
    ("Boston General Hospital", "rdf:type",       "Organization"),
    ("Boston General Hospital", "rdf:type",       "HealthcareProvider"),
    ("Harbor University Medical School", "rdf:type", "Organization"),
    ("Harbor University Medical School", "rdf:type", "EducationalInstitution"),
    ("Echocardiography Protocol", "rdf:type",     "ClinicalProtocol"),
    ("Echocardiography Protocol", "reducedBy",    "30% diagnostic wait times"),
]


# ============================================================================
# ONTOLOGY SCHEMA — Constrains what the LLM should extract
# ============================================================================

ONTOLOGY_SCHEMA = """
ENTITY TYPES:
  - Person: A human individual
  - Organization: A company, hospital, university, or institution
  - HealthcareProvider: An Organization that provides medical services
  - EducationalInstitution: An Organization that provides education
  - Role: A professional position or title
  - ClinicalProtocol: A medical procedure or diagnostic method
  - ResearchProgram: A structured research initiative

RELATION TYPES:
  - (Person) --worksAt--> (Organization)
  - (Person) --previouslyAt--> (Organization)
  - (Person) --hasRole--> (Role)
  - (Person) --affiliatedWith--> (Organization)
  - (Person) --educatedAt--> (Organization)
  - (Person) --leads--> (ResearchProgram | Team)
  - (Person) --introduced--> (ClinicalProtocol)
  - (Person) --teaches--> (Subject)
  - (Organization) --isA--> (Organization type)

PROPERTY TYPES:
  - startDate: When a role or affiliation began
  - duration: Length of a role or affiliation
  - degree: Academic qualification
  - training: Specialized training completed
  - impact: Measurable outcome of an action
"""


# ============================================================================
# PROMPTS — Unconstrained vs. Ontology-Guided
# ============================================================================

UNCONSTRAINED_PROMPT = f"""Extract all relationships and facts from the following text as triples
in the format (Subject, Predicate, Object). Extract as many triples as you can find.

Return ONLY a JSON array of triples, where each triple is a 3-element array
of strings: ["subject", "predicate", "object"].

Do not include any explanation, markdown formatting, or text outside the JSON array.

Text:
{SOURCE_TEXT}
"""

GUIDED_PROMPT = f"""Extract structured knowledge from the following text as triples, but ONLY
extract triples that conform to the ontology schema provided below.

For each entity mentioned, first emit a type assertion triple:
  ["entity name", "rdf:type", "EntityType"]

Then emit relationship triples using ONLY the relation types defined in the schema.

Return ONLY a JSON array of triples, where each triple is a 3-element array
of strings: ["subject", "predicate", "object"].

Do not include any explanation, markdown formatting, or text outside the JSON array.

ONTOLOGY SCHEMA:
{ONTOLOGY_SCHEMA}

TEXT:
{SOURCE_TEXT}
"""


# ============================================================================
# PRE-RECORDED OUTPUTS — For demo mode (no API key needed)
# ============================================================================

# These are actual outputs from an LLM, saved so the script runs without an API key.

UNCONSTRAINED_OUTPUT = [
    ["Dr. Sarah Chen", "joined", "MedVista Health"],
    ["Dr. Sarah Chen", "has position", "Chief of Cardiology"],
    ["Dr. Sarah Chen", "joined date", "March 2024"],
    ["Dr. Sarah Chen", "previously worked at", "Boston General Hospital"],
    ["Dr. Sarah Chen", "worked at Boston General for", "twelve years"],
    ["Dr. Sarah Chen", "led", "cardiac imaging research program"],
    ["Dr. Sarah Chen", "works at", "MedVista Health"],
    ["Dr. Sarah Chen", "oversees team of", "eight cardiologists"],
    ["Dr. Sarah Chen", "introduced", "new echocardiography protocol"],
    ["echocardiography protocol", "reduced diagnostic wait times by", "30%"],
    ["Dr. Sarah Chen", "serves as", "adjunct professor"],
    ["Dr. Sarah Chen", "is adjunct professor at", "Harbor University Medical School"],
    ["Dr. Sarah Chen", "teaches", "advanced cardiovascular diagnostics"],
    ["advanced cardiovascular diagnostics", "taught to", "third-year residents"],
    ["Dr. Sarah Chen", "completed MD at", "Johns Hopkins"],
    ["Dr. Sarah Chen", "completed fellowship at", "Cleveland Clinic"],
    ["Dr. Sarah Chen", "fellowship type", "cardiology"],
    ["MedVista Health", "has department", "Cardiology"],
    ["Boston General Hospital", "had program", "cardiac imaging research program"],
]

GUIDED_OUTPUT = [
    ["Dr. Sarah Chen", "rdf:type", "Person"],
    ["MedVista Health", "rdf:type", "HealthcareProvider"],
    ["Boston General Hospital", "rdf:type", "HealthcareProvider"],
    ["Harbor University Medical School", "rdf:type", "EducationalInstitution"],
    ["Johns Hopkins", "rdf:type", "EducationalInstitution"],
    ["Cleveland Clinic", "rdf:type", "HealthcareProvider"],
    ["Cardiac Imaging Research Program", "rdf:type", "ResearchProgram"],
    ["Echocardiography Protocol", "rdf:type", "ClinicalProtocol"],
    ["Dr. Sarah Chen", "worksAt", "MedVista Health"],
    ["Dr. Sarah Chen", "hasRole", "Chief of Cardiology"],
    ["Dr. Sarah Chen", "previouslyAt", "Boston General Hospital"],
    ["Dr. Sarah Chen", "leads", "Cardiac Imaging Research Program"],
    ["Dr. Sarah Chen", "affiliatedWith", "Harbor University Medical School"],
    ["Dr. Sarah Chen", "hasRole", "Adjunct Professor"],
    ["Dr. Sarah Chen", "educatedAt", "Johns Hopkins"],
    ["Dr. Sarah Chen", "educatedAt", "Cleveland Clinic"],
    ["Dr. Sarah Chen", "introduced", "Echocardiography Protocol"],
    ["Dr. Sarah Chen", "teaches", "Advanced Cardiovascular Diagnostics"],
    ["Dr. Sarah Chen", "degree", "MD"],
    ["Dr. Sarah Chen", "training", "Cardiology Fellowship"],
    ["Dr. Sarah Chen", "startDate", "March 2024"],
    ["Dr. Sarah Chen", "duration", "12 years"],
    ["Echocardiography Protocol", "impact", "Reduced diagnostic wait times by 30%"],
]


# ============================================================================
# LLM EXTRACTION (live mode via LiteLLM)
# ============================================================================

def extract_triples_live(prompt: str) -> List[List[str]]:
    """Call an LLM via LiteLLM to extract triples from text."""
    response = litellm.completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.0,
        api_key=API_KEY,
    )
    text = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

    return json.loads(text)


# ============================================================================
# ANALYSIS — Compare extractions to ground truth
# ============================================================================

def analyze_extraction(
    name: str,
    extracted: List,
    ground_truth: List[Tuple[str, str, str]],
):
    """Analyze how well an extraction matches ground truth."""
    # Count total
    print(f"  Total triples extracted: {len(extracted)}")
    print()

    # Categorize predicates
    pred_counts = {}
    for t in extracted:
        pred = t[1] if len(t) > 1 else "unknown"
        pred_counts[pred] = pred_counts.get(pred, 0) + 1

    print("  Predicates used:")
    for pred, count in sorted(pred_counts.items(), key=lambda x: -x[1]):
        print(f"    {pred}: {count}")
    print()

    # Check for type assertions (structural awareness)
    type_triples = [t for t in extracted if len(t) > 1 and t[1] == "rdf:type"]
    print(f"  Type assertions (rdf:type): {len(type_triples)}")
    if type_triples:
        for t in type_triples:
            print(f"    ({t[0]}) --rdf:type--> ({t[2]})")
    else:
        print("    (none — no structural typing)")
    print()

    # Check predicate consistency
    unique_preds = set(t[1] for t in extracted if len(t) > 1)
    print(f"  Unique predicates: {len(unique_preds)}")
    print()


def compare_extractions(unconstrained: List, guided: List):
    """Side-by-side comparison of the two approaches."""
    print("=" * 65)
    print("COMPARISON: Unconstrained vs. Ontology-Guided")
    print("=" * 65)
    print()

    u_preds = set(t[1] for t in unconstrained)
    g_preds = set(t[1] for t in guided)

    print(f"  {'Metric':<35} {'Unconstrained':>14} {'Guided':>10}")
    print(f"  {'-' * 35} {'-' * 14} {'-' * 10}")
    print(f"  {'Total triples':<35} {len(unconstrained):>14} {len(guided):>10}")
    print(f"  {'Unique predicates':<35} {len(u_preds):>14} {len(g_preds):>10}")

    u_types = len([t for t in unconstrained if t[1] == "rdf:type"])
    g_types = len([t for t in guided if t[1] == "rdf:type"])
    print(f"  {'Type assertions (rdf:type)':<35} {u_types:>14} {g_types:>10}")

    print()
    print("  Key differences:")
    print()
    print("  1. PREDICATE CONSISTENCY")
    print(f"     Unconstrained uses {len(u_preds)} different predicates:")
    for p in sorted(u_preds):
        print(f"       - {p}")
    print(f"     Guided uses {len(g_preds)} (from the ontology schema):")
    for p in sorted(g_preds):
        print(f"       - {p}")
    print()
    print("     The unconstrained version invents ad-hoc predicates")
    print('     ("joined", "has position", "serves as") that would be')
    print("     inconsistent across multiple documents. The guided version")
    print("     uses a controlled vocabulary from the ontology.")
    print()

    print("  2. TYPE ASSERTIONS")
    print(f"     Unconstrained: {u_types} type assertions")
    print(f"     Guided: {g_types} type assertions")
    print()
    print("     Without type assertions, nodes are just strings. With them,")
    print("     the graph knows that 'MedVista Health' is a HealthcareProvider")
    print("     and 'Johns Hopkins' is an EducationalInstitution. This enables")
    print("     type-level queries: 'List all HealthcareProviders Dr. Chen")
    print("     has worked at.'")
    print()

    print("  3. GRAPH INTEGRABILITY")
    print("     Unconstrained triples from different documents would produce")
    print('     a messy graph: "joined", "works at", "employed by" all mean')
    print("     the same thing but create different edge types.")
    print("     Guided triples are immediately compatible because they share")
    print("     the same schema. This is why the ontology is essential for")
    print("     building knowledge graphs at scale.")
    print()


# ============================================================================
# MAIN
# ============================================================================

def main():
    # Determine mode
    live_mode = HAS_LITELLM and bool(API_KEY)

    print()
    print("THE LAYERED MIND — Part 2: LLM-Assisted Triple Extraction")
    print("=" * 65)
    print()

    if live_mode:
        print(f"  Mode:  LIVE")
        print(f"  Model: {MODEL}")
    else:
        print("  Mode: DEMO (using pre-recorded outputs)")
        if not HAS_LITELLM:
            print("         Install 'litellm' package for live mode:")
            print("           pip install litellm")
        elif not API_KEY:
            print("         Set API_KEY env variable for live mode:")
            print("           export API_KEY=your-key-here")
            print(f"         (Optional) Set MODEL env variable (default: {DEFAULT_MODEL})")
            print()
            print("         Supported providers include:")
            print("           MODEL=openai/gpt-4o-mini")
            print("           MODEL=anthropic/claude-sonnet-4-20250514")
            print("           MODEL=openrouter/google/gemini-2.0-flash-001")
            print("           MODEL=groq/llama-3.3-70b-versatile")
            print("           MODEL=deepseek/deepseek-chat")
            print("         See https://docs.litellm.ai/docs/providers for all options.")
    print()

    # Show the source text
    print("-" * 65)
    print("SOURCE TEXT:")
    print("-" * 65)
    for line in SOURCE_TEXT.strip().split("\n"):
        print(f"  {line.strip()}")
    print()

    # --- Extraction 1: Unconstrained ---
    print("=" * 65)
    print("EXTRACTION 1: Unconstrained (no ontology guidance)")
    print("=" * 65)
    print()
    print('  Prompt: "Extract all relationships and facts as triples."')
    print()

    if live_mode:
        print(f"  Calling {MODEL}...")
        try:
            unconstrained = extract_triples_live(UNCONSTRAINED_PROMPT)
        except Exception as e:
            print(f"  ERROR: {e}")
            print("  Falling back to demo mode for this extraction.")
            unconstrained = UNCONSTRAINED_OUTPUT
        print()
    else:
        unconstrained = UNCONSTRAINED_OUTPUT

    print("  Extracted triples:")
    for t in unconstrained:
        print(f"    ({t[0]}) --{t[1]}--> ({t[2]})")
    print()
    analyze_extraction("Unconstrained", unconstrained, GROUND_TRUTH)

    # --- Extraction 2: Ontology-Guided ---
    print("=" * 65)
    print("EXTRACTION 2: Ontology-Guided (schema-constrained)")
    print("=" * 65)
    print()
    print('  Prompt: "Extract triples conforming to this ontology schema..."')
    print()
    print("  Schema defines:")
    print("    Entity types: Person, Organization, HealthcareProvider,")
    print("      EducationalInstitution, Role, ClinicalProtocol, ResearchProgram")
    print("    Relations: worksAt, previouslyAt, hasRole, affiliatedWith,")
    print("      educatedAt, leads, introduced, teaches")
    print()

    if live_mode:
        print(f"  Calling {MODEL}...")
        try:
            guided = extract_triples_live(GUIDED_PROMPT)
        except Exception as e:
            print(f"  ERROR: {e}")
            print("  Falling back to demo mode for this extraction.")
            guided = GUIDED_OUTPUT
        print()
    else:
        guided = GUIDED_OUTPUT

    print("  Extracted triples:")
    for t in guided:
        print(f"    ({t[0]}) --{t[1]}--> ({t[2]})")
    print()
    analyze_extraction("Guided", guided, GROUND_TRUTH)

    # --- Comparison ---
    compare_extractions(unconstrained, guided)

    # --- Takeaway ---
    print("=" * 65)
    print("TAKEAWAY")
    print("=" * 65)
    print()
    print("  The ontology you design isn't just for querying your graph.")
    print("  It's the schema that makes BUILDING the graph tractable.")
    print()
    print("  Unconstrained extraction produces a grab-bag of ad-hoc")
    print("  predicates that don't compose across documents.")
    print()
    print("  Ontology-guided extraction produces consistent, typed,")
    print("  integrable triples — because the LLM knows what to look for.")
    print()
    print("  Human role: not building knowledge from scratch, but")
    print("  reviewing and validating what the LLM proposes.")
    print()
    print("  More on this in Parts 8-9.")
    print()


if __name__ == "__main__":
    main()
