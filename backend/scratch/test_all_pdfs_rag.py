import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

import rag

queries_per_pdf = [
    (
        "Agriculture_Contingency_Plan_Raigad.pdf",
        "Raigad soil rainfall climate contingency",
    ),
    ("All_India_Crop_Calendar.pdf", "crop calendar sowing harvesting state wise"),
    ("Crop_Production_Guide_TN.pdf", "rice crop production Tamil Nadu management"),
    (
        "Farmers_Handbook_Basic_Agriculture.pdf",
        "basic agriculture principles seed soil fertilizer",
    ),
    (
        "Organic_Farming_Training_Manual.pdf",
        "organic farming compost vermicompost biofertilizer",
    ),
    (
        "PKVY_Scheme_Guidelines.pdf",
        "Paramparagat Krishi Vikas Yojana PKVY scheme cluster",
    ),
    (
        "PMFBY_Operational_Guidelines.pdf",
        "Pradhan Mantri Fasal Bima Yojana claim premium sum insured",
    ),
    ("PMFBY_Scheme_Features.pdf", "crop insurance coverage risk post harvest"),
    (
        "PM_KISAN_Guidelines_English.pdf",
        "PM Kisan installment eligibility landholding bank account",
    ),
    (
        "Package_of_Practices_Organic_HP.pdf",
        "organic farming Himachal Pradesh apples vegetables",
    ),
    (
        "Package_of_Practices_Rabi_Punjab.pdf",
        "wheat varieties Rabi Punjab sowing time fertilizer",
    ),
]

print("================ RAG RETRIEVAL TEST ACROSS ALL 11 PDFs ================\n")

passed = 0
for pdf_name, query in queries_per_pdf:
    result = rag.search_knowledge_base(query, top_k=2)
    found = pdf_name.replace(".pdf", "") in result or any(
        w.lower() in result.lower() for w in query.split()[:2]
    )
    status = "SUCCESS" if found and len(result) > 100 else "FAILED"
    if status == "SUCCESS":
        passed += 1
    print(f"PDF: {pdf_name}")
    print(f"Query: '{query}'")
    print(f"Status: {status}")
    print(f"Result Snippet: {result[:180].replace(chr(10), ' ')}...")
    print("-" * 70)

print(
    f"\nSummary: {passed}/{len(queries_per_pdf)} PDF document retrieval tests PASSED!"
)
