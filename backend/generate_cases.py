import os
import sys
import json
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal
from pypdf import PdfReader

# Load environment variables
backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(backend_dir)
sys.path.insert(0, root_dir)

env_path = os.path.join(backend_dir, ".env")
load_dotenv(env_path)
load_dotenv()

from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in backend/.env!")

client = genai.Client(api_key=GEMINI_API_KEY)


class CaseStudySchema(BaseModel):
    title: str = Field(description="Clear, professional title of the case study")
    category: Literal["data_diagnosis", "strategy_generation", "customer_reasoning"] = Field(
        description="Core skill category: data_diagnosis, strategy_generation, or customer_reasoning"
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(
        description="Difficulty level of the case: easy, medium, or hard"
    )
    prompt_text: str = Field(
        description="2-4 sentences presenting the dilemma to the candidate, instructing them to use the data and AI assistant"
    )
    context_data: str = Field(
        description="6-10 realistic metrics/quotes/facts with exactly 1 subtle red herring distractor"
    )
    ground_truth_notes: str = Field(
        description="Detailed notes explaining root cause, why the red herring is a trap, and required action"
    )


# 15 Authentic Real-World Company Case Seeds modeled on classic MIT Sloan / business school cases
REAL_WORLD_CASE_SEEDS = [
    {
        "company": "Nike",
        "topic": "North American Inventory Glut and Supply Chain Bullwhip Effect",
        "category": "data_diagnosis",
        "difficulty": "medium",
        "core_issue": "Excess inventory surged 44% in North America after severe supply chain transit delays (80+ days vs 40 standard) suddenly cleared simultaneously, landing at warehouses just as consumer discretionary spending cooled.",
        "red_herring": "Declining marketing engagement scores and controversy surrounding recent celebrity athlete campaigns, tempting analysts to blame brand heat rather than the supply-chain transit lag.",
        "action": "Liquidate off-price inventory through wholesale outlet partners, scale back forward production orders by 20%, and implement dynamic transit-visibility forecasting."
    },
    {
        "company": "Toyota",
        "topic": "The Rapid Global Expansion Quality Dilemma and Supplier Auditing",
        "category": "data_diagnosis",
        "difficulty": "hard",
        "core_issue": "Rapid aggressive growth targeting 15% global market share strained Toyota's legendary Just-In-Time and TPS oversight, leading to tier-2 supplier quality slips and delayed defect escalations across regional plants.",
        "red_herring": "Floor mat pedal entrapment complaints dominating headlines, deflecting attention from underlying structural supplier auditing shortcuts and centralized Tokyo engineering sign-off delays.",
        "action": "Decentralize safety reporting to regional quality task forces, pause capacity expansions to retrain tier-1/2 suppliers on TPS standards, and institute redundant mechanical brake-override logic."
    },
    {
        "company": "Netflix",
        "topic": "The Qwikster Unbundling and Subscription Churn Crisis",
        "category": "customer_reasoning",
        "difficulty": "easy",
        "core_issue": "Splitting DVD-by-mail and streaming into two separate services and websites with independent billing created an uncoordinated 60% effective price hike and massive user friction, causing 800,000 subscriber cancellations.",
        "red_herring": "The rapid expansion of Hulu and Amazon Prime Video catalog sizes cited in media reports as competitive pressure.",
        "action": "Acknowledge the mistake immediately, scrap the separate Qwikster brand and separate billing system, keep DVD and streaming access under a single unified login, and offer loyalty credits to impacted users."
    },
    {
        "company": "Intel",
        "topic": "Missing the Mobile Architecture Shift (The Original iPhone Chip Decision)",
        "category": "strategy_generation",
        "difficulty": "hard",
        "core_issue": "Intel rejected Steve Jobs' offer to design and produce the original iPhone processor because Intel's internal financial forecasting model severely underestimated smartphone volume (projecting only 2M units vs actual tens of millions), deciding the offered price per chip would dilute Intel's 60% gross margins.",
        "red_herring": "Thermal dissipation challenges of the x86 architecture and micro-architecture power draw cited by engineering managers.",
        "action": "Establish a dedicated low-power mobility division exempted from corporate 60% margin hurdle rates, secure the volume manufacturing contract with Apple to achieve scale economies, and adapt x86 for low-power mobile workloads."
    },
    {
        "company": "Starbucks",
        "topic": "Store Cannibalization and Brand Dilution During Rapid Expansion",
        "category": "data_diagnosis",
        "difficulty": "medium",
        "core_issue": "Opening hundreds of new stores within blocks of existing locations created severe internal foot-traffic cannibalization (up to 30% of sales drawn from neighboring stores), while automated Mastrena espresso machines and flavor-sealed bags stripped away barista craft and coffee aroma.",
        "red_herring": "The 2008 macroeconomic recession and rising consumer inflation cited as the sole culprit for falling same-store transactions.",
        "action": "Close 600 underperforming and cannibalizing stores, halt rapid unit expansion, retrain 135,000 baristas during a nationwide store shutdown, and reintroduce sensory coffee experiences in-store."
    },
    {
        "company": "Olist",
        "topic": "Brazilian Marketplace Logistics Bottleneck and Merchant Churn",
        "category": "data_diagnosis",
        "difficulty": "medium",
        "core_issue": "Marketplace aggregator seller churn skyrocketed to 18% monthly due to long shipping delivery windows and frequent transit delays via national postal carriers across inter-state corridors, resulting in 1-star seller ratings and withheld marketplace payouts.",
        "red_herring": "High merchant complaints about the 19% take-rate marketplace commission and platform subscription fees.",
        "action": "Partner with regional private courier networks (3PLs) to bypass centralized postal bottlenecks, establish decentralized fulfillment micro-hubs in São Paulo and Rio, and institute automatic SLA dispute forgiveness for courier-caused delivery delays."
    },
    {
        "company": "Uber",
        "topic": "The China Market Battle and Didi Chuxing War of Attrition",
        "category": "strategy_generation",
        "difficulty": "hard",
        "core_issue": "Uber was burning over $1 billion annually subsidizing both drivers and riders in China in a zero-sum price war against Didi Chuxing, which held 87% market share, enjoyed backing from both Tencent (WeChat ecosystem) and Alibaba, and had superior local regulatory relationships.",
        "red_herring": "Western media focusing on Uber's app GPS mapping glitches and payment translation issues as the primary operational impediment.",
        "action": "Negotiate a strategic exit by selling Uber China's operations to Didi in exchange for a substantial 17.7% equity stake in Didi Chuxing, eliminating the billion-dollar annual cash drain while maintaining upside in China's ride-hailing market."
    },
    {
        "company": "DHL",
        "topic": "Global Forwarding SAP ERP System Implementation Meltdown",
        "category": "strategy_generation",
        "difficulty": "hard",
        "core_issue": "DHL's 'New Forwarding Environment' (NFE) IT transformation was forced as a rigid top-down big-bang replacement across global freight forwarding, attempting to automate paperless customs without integrating local regulatory compliance nuances, causing €345M in software write-offs and operational chaos.",
        "red_herring": "Software bugs in SAP code and third-party systems integration consultants cited by project managers.",
        "action": "Abandon the monolithic big-bang software rollout, write down the unworkable software asset, revert to stabilized modular systems, and involve frontline local customs and freight handlers in phased, regional pilot rollouts."
    },
    {
        "company": "Zoom",
        "topic": "Post-Pandemic SMB Churn and Enterprise Platform Transition",
        "category": "customer_reasoning",
        "difficulty": "medium",
        "core_issue": "As pandemic remote-work mandates relaxed, monthly churn among SMB and individual online customers jumped to 4.2%, while Microsoft was aggressively bundling Teams into existing Office 365 enterprise licenses for zero perceived incremental cost.",
        "red_herring": "End-user complaints regarding Zoom's web interface changes and security password requirement prompts.",
        "action": "Shift go-to-market resources from transactional online acquisitions toward enterprise multi-product expansion (Zoom Phone, Zoom Rooms, and AI Contact Center) with sticky multi-year enterprise contracts."
    },
    {
        "company": "Apple",
        "topic": "Geographic Supply Chain Concentration and Foxconn Zhengzhou Risks",
        "category": "strategy_generation",
        "difficulty": "hard",
        "core_issue": "Over 70% of global iPhone Pro manufacturing was concentrated at a single mega-factory campus in Zhengzhou ('iPhone City'), leaving Apple vulnerable to localized lockdowns, regional power grid curtails, and severe worker shortages that caused millions of units in backlogged holiday sales.",
        "red_herring": "Component supplier delays for 3nm mobile processors and camera image sensors.",
        "action": "Accelerate the 'China Plus One' diversification strategy by expanding production capacity in India and Vietnam to account for at least 25% of global iPhone assembly within 3 years, and redesign chassis tooling for dual-site modular manufacturing."
    },
    {
        "company": "Inditex / Zara",
        "topic": "E-Commerce Return Rates and Omni-Channel Inventory Allocation",
        "category": "data_diagnosis",
        "difficulty": "medium",
        "core_issue": "Online apparel return rates climbed from 14% to 28%, choking centralized return distribution warehouses and destroying seasonal margins due to inventory remaining in transit during peak demand windows.",
        "red_herring": "Consumer complaints about subtle sizing discrepancies in newer fast-fashion lines.",
        "action": "Incentivize store drop-off returns with instant store credits, utilize local retail stores as micro-logistics hubs to restock returned items within 2 hours, and institute nominal return fees for third-party courier home pick-ups."
    },
    {
        "company": "Boeing",
        "topic": "Commercial Aircraft Development Outsourcing and Safety Redundancy",
        "category": "data_diagnosis",
        "difficulty": "hard",
        "core_issue": "To avoid costly simulator retraining requirements and match competitor fuel efficiency quickly, flight-control software (MCAS) was designed to rely on a single Angle of Attack (AoA) sensor without cross-comparison redundancy, driven by siloed outsourced engineering contracts and schedule pressures.",
        "red_herring": "Foreign airline pilot training standards and maintenance log reporting inconsistencies highlighted in initial press briefings.",
        "action": "Mandate dual AoA sensor data cross-verification for automated flight control actuation, update pilot flight manuals with explicit disengage overrides, and mandate simulator training for all flight crews prior to return-to-service."
    },
    {
        "company": "Peloton",
        "topic": "Post-Pandemic Demand Reversion and Connected Hardware Inventory Write-Down",
        "category": "data_diagnosis",
        "difficulty": "medium",
        "core_issue": "Peloton treated peak-lockdown sales spikes (+250% YoY) as a permanent structural shift, acquiring manufacturing facilities and ordering $400M in hardware inventory with 9-month supplier lead times just as gym reopenings caused connected-fitness demand to plummet.",
        "red_herring": "Negative customer press following an accidental treadmill safety recall cited as the reason for slowing sales.",
        "action": "Halt internal manufacturing expansion, transition to third-party contract manufacturing, discount hardware to clear warehouse holding costs, and pivot the business model toward high-margin digital fitness subscriptions."
    },
    {
        "company": "Target",
        "topic": "The Canadian Retail Expansion Logistics Failure",
        "category": "strategy_generation",
        "difficulty": "hard",
        "core_issue": "Opening 124 stores in 10 months forced Target to rush a brand-new SAP and warehouse management implementation without data cleanup, resulting in corrupt product dimensions, barcode mismatches, and distribution centers overflowing with goods while store shelves remained visibly empty.",
        "red_herring": "Pundits arguing that Canadian consumers had different shopping preferences and cross-border shopping loyalties compared to US consumers.",
        "action": "Slow down store openings, conduct a full physical inventory and barcode audit across the Canadian distribution network, and re-establish real-time point-of-sale data synchronization between store shelves and regional distribution centers."
    },
    {
        "company": "Spotify",
        "topic": "Exclusive Podcast Investments vs Algorithmic Music Discovery ROI",
        "category": "strategy_generation",
        "difficulty": "medium",
        "core_issue": "Spending hundreds of millions of dollars on exclusive celebrity podcast licensing agreements failed to meaningfully lift overall premium subscriber conversion or gross margins, while locked-in multi-year minimum guarantee contracts squeezed operating profitability.",
        "red_herring": "Total podcast listening hours per user increasing, creating the illusion of business model success while ignoring content amortization costs.",
        "action": "Pivoting away from expensive exclusive licensing agreements toward wide distribution on an ad-supported programmatic network (Spotify Audience Network), while re-investing in core algorithmic personalization features (AI DJ, Discover Weekly) that drive 80%+ of subscriber retention."
    }
]


def extract_text_from_pdf(pdf_path: str, max_pages: int = 12, max_chars: int = 16000) -> str:
    """Extract clean text from a PDF file up to max_pages / max_chars."""
    reader = PdfReader(pdf_path)
    extracted = []
    total_chars = 0
    for idx, page in enumerate(reader.pages[:max_pages]):
        text = page.extract_text() or ""
        cleaned = " ".join(text.split())
        if cleaned:
            extracted.append(f"--- Page {idx + 1} ---\n{cleaned}")
            total_chars += len(cleaned)
            if total_chars >= max_chars:
                break
    return "\n\n".join(extracted)[:max_chars]


def convert_pdf_to_case_study(pdf_path: str) -> Optional[Dict[str, Any]]:
    """Convert an MIT Sloan PDF into a structured PromptBench case study JSON object."""
    filename = os.path.basename(pdf_path)
    print(f"[*] Extracting text from PDF: {filename}...")
    try:
        pdf_text = extract_text_from_pdf(pdf_path)
        if len(pdf_text.strip()) < 200:
            print(f"[-] Warning: {filename} contains insufficient text. Skipping.")
            return None
    except Exception as e:
        print(f"[-] Error reading {filename}: {e}")
        return None

    prompt = f"""You are an elite business school professor and case author for PromptBench.
PromptBench evaluates AI agents and human candidates on diagnosing and solving complex business case studies.

Convert the provided MIT Sloan case study text into a structured PromptBench case study JSON object.

CRITICAL REQUIREMENTS:
- title: A clear, memorable, professional title indicating the company and dilemma (e.g. "Amazon vs Walmart: Omnichannel Fulfillment War").
- category: Exactly one of: "data_diagnosis", "strategy_generation", "customer_reasoning".
- difficulty: Exactly one of: "easy", "medium", "hard".
- prompt_text: 2 to 4 sentences framing the business dilemma faced by leadership, explicitly instructing the candidate to use the provided data and their AI assistant to analyze the situation and recommend a concrete decision/fix.
- context_data: A markdown string containing 6 to 10 realistic bullet points, metrics, customer quotes, or financial data points directly drawn from the case facts.
  IMPORTANT: You MUST include exactly ONE subtle RED HERRING distractor - a plausible-sounding metric, trend, or complaint that seems critical on the surface but is actually a secondary symptom or coincidental correlation, distracting from the genuine root cause.
- ground_truth_notes: A thorough, definitive benchmark answer structured as:
  1. True Root Cause / Core Strategic Decision: The authentic underlying reality supported by the facts.
  2. The Red Herring Trap: Explicitly identify which metric/quote is the red herring, explain why candidates falsely latch onto it, and why it is misleading.
  3. Required Action: Concrete, operational recommendations leadership must execute to succeed.

Case Text:
{pdf_text}
"""

    # Retry loop with exponential backoff
    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CaseStudySchema,
                    temperature=0.2,
                )
            )
            data = json.loads(response.text)
            print(f"[+] Successfully generated case from {filename}: '{data.get('title')}'")
            return data
        except Exception as e:
            print(f"[-] Attempt {attempt} failed for {filename}: {e}")
            time.sleep(2 * attempt)

    print(f"[!] Failed to generate case for {filename} after 3 attempts.")
    return None


def generate_company_case(seed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generate an authentic company case study based on real-world business case seeds."""
    company = seed["company"]
    print(f"[*] Generating real-world case study for: {company}...")

    prompt = f"""You are an elite business school professor and case author for PromptBench.
Generate an authentic, highly detailed, real-world company case study modeled on classic MIT Sloan / Harvard Business School cases.

Company: {company}
Topic: {seed["topic"]}
Target Category: {seed["category"]}
Target Difficulty: {seed["difficulty"]}

Core Background & Root Reality:
{seed["core_issue"]}

Intended Red Herring Distractor:
{seed["red_herring"]}

Required Corrective Action:
{seed["action"]}

CRITICAL REQUIREMENTS:
- title: A professional, authentic business case title (e.g. "{company}: {seed['topic']}").
- category: Must be '{seed["category"]}'.
- difficulty: Must be '{seed["difficulty"]}'.
- prompt_text: 2 to 4 sentences presenting the leadership dilemma to the candidate, instructing them to evaluate the scenario using the context data and their AI assistant to formulate their findings.
- context_data: A markdown string with 6 to 10 realistic bullet points, metrics, customer quotes, and operational data points. Exactly ONE subtle RED HERRING distractor ({seed['red_herring']}) must be woven seamlessly into the data points.
- ground_truth_notes: Detailed notes explicitly breaking down:
  1. True Root Cause / Strategic Driver: Explaining what is genuinely happening.
  2. The Red Herring Trap: Naming the distractor and explaining why surface-level analyses falsely conclude it is the primary factor.
  3. Required Action: The exact strategic/operational measures required.
"""

    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CaseStudySchema,
                    temperature=0.2,
                )
            )
            data = json.loads(response.text)
            print(f"[+] Successfully generated company case: '{data.get('title')}'")
            return data
        except Exception as e:
            print(f"[-] Attempt {attempt} failed for {company}: {e}")
            time.sleep(2 * attempt)

    print(f"[!] Failed to generate company case for {company} after 3 attempts.")
    return None


def main():
    print("=" * 60)
    print("       PromptBench - Case Study Dataset Generator")
    print("=" * 60)
    print(f"Model: {GEMINI_MODEL}")
    
    pdf_dir = os.path.join(backend_dir, "pdfs")
    output_path = os.path.join(backend_dir, "generated_questions.json")

    pdf_files = []
    if os.path.exists(pdf_dir):
        pdf_files = [
            os.path.join(pdf_dir, f)
            for f in os.listdir(pdf_dir)
            if f.lower().endswith(".pdf")
        ]
    
    print(f"Found {len(pdf_files)} PDF file(s) in {pdf_dir}.")
    print(f"Found {len(REAL_WORLD_CASE_SEEDS)} authentic company case study seed(s).")
    print(f"Targeting total dataset scale: {len(pdf_files) + len(REAL_WORLD_CASE_SEEDS)}+ cases.")

    generated_cases: List[Dict[str, Any]] = []

    # 1. Process PDF cases concurrently (max_workers=3 to avoid rate limits)
    print("\n--- 1. Processing MIT Sloan PDF Cases ---")
    if pdf_files:
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_pdf = {
                executor.submit(convert_pdf_to_case_study, pdf): pdf
                for pdf in pdf_files
            }
            for future in as_completed(future_to_pdf):
                res = future.result()
                if res and isinstance(res, dict):
                    generated_cases.append(res)
    else:
        print("No PDFs found to process.")

    # 2. Process authentic company case studies concurrently
    print("\n--- 2. Generating Authentic Real-World Company Cases ---")
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_seed = {
            executor.submit(generate_company_case, seed): seed
            for seed in REAL_WORLD_CASE_SEEDS
        }
        for future in as_completed(future_to_seed):
            res = future.result()
            if res and isinstance(res, dict):
                generated_cases.append(res)

    print(f"\nTotal cases successfully generated: {len(generated_cases)}")

    # Deduplicate by title just in case
    unique_cases = []
    seen_titles = set()
    for case in generated_cases:
        title = case.get("title", "").strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_cases.append(case)

    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_cases, f, indent=2, ensure_ascii=False)

    print(f"[+] Saved {len(unique_cases)} unique case studies to: {output_path}")

    # Print summary statistics
    cat_counts: Dict[str, int] = {}
    diff_counts: Dict[str, int] = {}
    for c in unique_cases:
        cat = c.get("category", "unknown")
        diff = c.get("difficulty", "unknown")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        diff_counts[diff] = diff_counts.get(diff, 0) + 1

    print("\n--- Generation Summary ---")
    print("Categories:")
    for cat, count in cat_counts.items():
        print(f"  - {cat}: {count}")
    print("Difficulties:")
    for diff, count in diff_counts.items():
        print(f"  - {diff}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()

