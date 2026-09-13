import os
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.db import engine, Base, SessionLocal
from backend.app.models import Question

def seed_database():
    print("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    
    db: SessionLocal = SessionLocal()
    try:
        # Clear existing questions to avoid duplicates on re-run
        print("Clearing existing questions...")
        db.query(Question).delete()
        db.commit()

        # Seed default rubric
        default_rubric = {
            "dimensions": [
                {
                    "name": "clarifying_questions",
                    "weight": 0.20,
                    "description": "Did the candidate ask relevant clarifying questions before jumping to a solution?"
                },
                {
                    "name": "iteration_quality",
                    "weight": 0.25,
                    "description": "Did the candidate refine their prompts/approach based on AI responses rather than accepting the first output?"
                },
                {
                    "name": "hallucination_catching",
                    "weight": 0.25,
                    "description": "Did the candidate identify and correct incorrect or fabricated AI outputs?"
                },
                {
                    "name": "final_answer_quality",
                    "weight": 0.30,
                    "description": "Is the final recommendation correct, well-justified, and grounded in the given case data?"
                }
            ]
        }

        questions = [
            Question(
                title="Sudden Churn Spike",
                category="data_diagnosis",
                difficulty="medium",
                prompt_text=(
                    "Our SaaS product's monthly churn jumped from 4% to 9% last month. "
                    "You have access to an AI assistant and the dataset below (customer cancellation survey responses + usage log summary). "
                    "Diagnose the likely cause and recommend one action."
                ),
                context_data=(
                    "--- Survey Responses (Sample of Churned Users) ---\n"
                    "1. 'Pricing is too high for what we get now.'\n"
                    "2. 'Where did the custom reporting feature go? We used it daily!'\n"
                    "3. 'Product is too expensive.'\n"
                    "4. 'You removed the advanced search tool. I can't do my job.'\n"
                    "5. 'Support was slow, and pricing is not competitive.'\n"
                    "6. 'We migrated to a competitor because they have custom reporting.'\n"
                    "7. 'Loved the product, but feature cuts made us leave.'\n"
                    "8. 'Why pay the same price when you took away the reporting dashboard?'\n"
                    "\n"
                    "--- Usage Log Summary ---\n"
                    "- Active hours per user: Down 12% overall.\n"
                    "- Support tickets: 15% increase in pricing complaints, 85% increase in feature-removal complaints.\n"
                    "- Feature usage: Custom reports module used by 70% of high-value accounts prior to deprecation."
                ),
                ground_truth_notes=(
                    "The real cause of the churn spike is the removal/deprecation of the custom reporting feature, "
                    "not the pricing itself. The pricing complaints are a secondary reaction (red herring) because users "
                    "feel they are paying the same price for a degraded product. "
                    "A strong answer identifies this feature-removal correlation and recommends either reinstating "
                    "the custom reporting tool or providing a migration path/replacement dashboard."
                ),
                rubric_json=default_rubric
            ),
            Question(
                title="New Market Entry",
                category="strategy_generation",
                difficulty="hard",
                prompt_text=(
                    "Our mid-size B2B SaaS company is considering expanding into either the German or Brazilian market next year. "
                    "You have market size, competitor, and regulatory context below. Recommend one market and justify it."
                ),
                context_data=(
                    "--- German Market Context ---\n"
                    "- Total Market Size (TAM): $450M annually.\n"
                    "- Current Competitors: 2 highly entrenched European giants (holding 85% market share).\n"
                    "- Regulatory: GDPR compliance required, strict server localization rules.\n"
                    "- Sales Cycles: 9-12 months average.\n"
                    "\n"
                    "--- Brazilian Market Context ---\n"
                    "- Total Market Size (TAM): $180M annually (growing at 30% YoY).\n"
                    "- Current Competitors: 12 small local players (no single player holds > 10% share).\n"
                    "- Regulatory: Standard business registration, data protection rules in transition.\n"
                    "- Sales Cycles: 3-5 months average."
                ),
                ground_truth_notes=(
                    "Germany has a larger headline market size ($450M), but is highly consolidated and dominated by "
                    "two entrenched players holding 85% market share, with very long sales cycles. "
                    "Brazil is the stronger pick because it has low competitive saturation, faster sales cycles (3-5 months), "
                    "and rapid YoY growth (30%). A strong answer catches that Germany is a trap (red herring) and "
                    "recommends entering Brazil due to low competitive concentration and faster time-to-market."
                ),
                rubric_json=default_rubric
            ),
            Question(
                title="Angry Customer Escalation",
                category="customer_reasoning",
                difficulty="easy",
                prompt_text=(
                    "A high-value customer ($50k ARR) is threatening to cancel after a billing error charged them twice. "
                    "Use the AI assistant to draft a resolution plan and a response to the customer."
                ),
                context_data=(
                    "--- Customer Account Details ---\n"
                    "- Name: Acme Corporation (CEO Jane Miller).\n"
                    "- Customer lifetime: 3 years.\n"
                    "- Prior issues: None (mostly positive check-ins).\n"
                    "- Billing error: Charged twice on invoice #9482 ($8,333 instead of $4,166)."
                ),
                ground_truth_notes=(
                    "A strong answer must propose: "
                    "1. An immediate refund or credit of the overcharged amount ($4,166).\n"
                    "2. A personal apology email addressing the CEO directly.\n"
                    "3. A concrete process fix (e.g. implementing automated double-billing checks in the billing processor) "
                    "rather than just an apology, ensuring this never happens again."
                ),
                rubric_json=default_rubric
            ),
            Question(
                title="Sales Decline Diagnosis",
                category="data_diagnosis",
                difficulty="medium",
                prompt_text=(
                    "Our e-commerce store's sales declined by 15% in Q3. "
                    "Analyse the conversion rates, traffic channels, and catalog views to explain the decline and suggest a fix."
                ),
                context_data=(
                    "--- Analytics Overview ---\n"
                    "- Desktop conversion rate: 2.8% (unchanged).\n"
                    "- Mobile conversion rate: Dropped from 2.5% to 0.6%.\n"
                    "- Total search queries: Stable YoY.\n"
                    "- Empty search results pages: Increased by 400% on mobile browsers.\n"
                    "- Traffic source: Paid Ads traffic is up 10%; organic search is down 5%."
                ),
                ground_truth_notes=(
                    "The decline is driven entirely by a failure in the mobile search experience. "
                    "While desktop conversion is stable, mobile conversion collapsed because empty search results "
                    "pages skyrocketed by 400%. The root cause is a broken search bar rendering engine on mobile layout. "
                    "A strong answer identifies the mobile search bug as the root cause, rejecting marketing redirects "
                    "or pricing adjustments, and proposes a fix to the mobile layout search scripts."
                ),
                rubric_json=default_rubric
            ),
            Question(
                title="Product Launch Strategy",
                category="strategy_generation",
                difficulty="hard",
                prompt_text=(
                    "We are launching a new AI-driven analytics feature. "
                    "Help us draft the pricing structure, launch timeline, and target customer segments."
                ),
                context_data=(
                    "--- Feature Specifications ---\n"
                    "- Development: Feature is 90% complete, requires security compliance audits for Enterprise customers.\n"
                    "- Target segments: Mid-market SaaS ($10k-$100k ARR) and Enterprise ($100k+ ARR).\n"
                    "- Competitor pricing: Competitors charge a flat $200/mo add-on or 10% of base fee."
                ),
                ground_truth_notes=(
                    "Since the feature lacks Enterprise security compliance certifications, the launch strategy "
                    "should target mid-market SaaS customers first. The pricing model should be a value-based or tiered add-on "
                    "rather than flat pricing. The timeline must include a 1-month closed beta with selected mid-market users "
                    "while compliance audits are completed, followed by a general release to mid-market, "
                    "postponing the Enterprise launch until certification is obtained."
                ),
                rubric_json=default_rubric
            )
        ]

        print("Seeding questions...")
        db.add_all(questions)
        db.commit()
        print("Database seeded successfully with 5 questions!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
