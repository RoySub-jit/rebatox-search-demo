from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_session_factory
from app.models.catalog import Comparator, Product
from app.models.document import CitationSpan, DocumentChunk, SourceDocument
from app.models.research import (
    CalculationRun,
    CandidatePOD,
    ExpertReview,
    Finding,
    Limitation,
    Recommendation,
    Study,
)


def _reset_database(db) -> None:
    bind = db.get_bind()
    if bind is None:
        raise RuntimeError("Database bind is unavailable.")

    dialect = bind.dialect.name
    table_names = [table.name for table in Base.metadata.sorted_tables]

    if dialect == "postgresql":
        joined_names = ", ".join(table_names)
        db.execute(text(f"TRUNCATE TABLE {joined_names} RESTART IDENTITY CASCADE"))
        db.commit()
        return

    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())

    if dialect == "sqlite":
        try:
            db.execute(text("DELETE FROM sqlite_sequence"))
        except OperationalError:
            pass

    db.commit()


def seed_demo_report(db) -> dict[str, int]:
    product = Product(
        name="Cardiovex XR",
        slug="cardiovex-xr",
        manufacturer="Example Labs",
        description=(
            "Extended-release safety assessment candidate for RebaTox "
            "reviewer workflow demos."
        ),
    )
    comparator = Comparator(
        name="Legacy IR comparator",
        slug="legacy-ir-comparator",
        category="active_control",
        description=(
            "Immediate-release comparator used in adherence framing and "
            "bridge review."
        ),
    )
    source_document = SourceDocument(
        title="CSR CVX-301",
        document_type="clinical_study_report",
        source_uri="https://example.test/cvx-301",
    )

    chunk_content = (
        "Patients received oral dosing for 12 weeks. "
        "Systemic exposure remained within the maintenance band and supported "
        "the NOAEL selection."
    )
    document_chunk = DocumentChunk(
        source_document=source_document,
        chunk_index=0,
        content=chunk_content,
        page_number_start=21,
        page_number_end=22,
    )
    study = Study(
        product=product,
        comparator=comparator,
        source_document=source_document,
        title="CVX-301 maintenance study",
        objective="Evaluate oral maintenance dosing and exposure stability.",
        study_design="Randomized clinical trial",
        population="Adult patients",
        status="complete",
        published_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
    )
    finding = Finding(
        study=study,
        title="Exposure stability",
        summary="Systemic exposure remained stable during the maintenance period.",
        finding_type="safety",
        evidence_direction="supportive",
        effect_estimate=Decimal("0.85"),
    )

    quoted_text = (
        "Systemic exposure remained within the maintenance band and supported "
        "the NOAEL selection."
    )
    start_offset = chunk_content.index("Systemic exposure")
    end_offset = start_offset + len(quoted_text)
    citation_span = CitationSpan(
        finding=finding,
        document_chunk=document_chunk,
        start_offset=start_offset,
        end_offset=end_offset,
        quoted_text=quoted_text,
        label="exposure_support",
    )
    candidate_pod = CandidatePOD(
        product=product,
        comparator=comparator,
        finding=finding,
        title="Lead NOAEL candidate",
        claim_text="NOAEL of 5 mg/kg/day retained for the current report.",
        rationale=(
            "Oral route, clinical exposure context, and quantitative screening "
            "all align."
        ),
        status="active",
        confidence_score=Decimal("0.85"),
    )
    limitation = Limitation(
        study=study,
        finding=finding,
        description="Duration bridge remains limited for long-term extrapolation.",
        severity="medium",
    )
    recommendation = Recommendation(
        candidate_pod=candidate_pod,
        study=study,
        finding=finding,
        recommendation_type="next_experiment",
        recommendation_text=(
            "Run a longer-duration oral bridging study to extend the "
            "maintenance exposure narrative."
        ),
        priority="high",
        status="open",
    )
    calculation_run = CalculationRun(
        product=product,
        comparator=comparator,
        study=study,
        candidate_pod=candidate_pod,
        run_type="margin_of_exposure",
        status="ok",
        parameters_json={
            "point_of_departure": "100",
            "exposure": "2",
            "basis": "mg/kg/day",
        },
        result_json={
            "calculator": "margin_of_exposure",
            "formula": "MOE = POD / Exposure",
            "formula_version": "1.0",
            "inputs": {
                "point_of_departure": "100",
                "exposure": "2",
                "basis": "mg/kg/day",
            },
            "assumptions": [
                "Point of departure and exposure share the same dose basis."
            ],
            "result": {
                "value": "50.0",
                "unit": "ratio",
            },
            "warnings": [],
            "status": "ok",
        },
        started_at=datetime(2024, 4, 1, 12, 0, tzinfo=timezone.utc),
        completed_at=datetime(2024, 4, 1, 12, 0, tzinfo=timezone.utc),
    )
    expert_review = ExpertReview(
        candidate_pod=candidate_pod,
        finding=finding,
        calculation_run=calculation_run,
        reviewer_name="Dr. Ada Review",
        reviewer_email="ada@example.test",
        verdict="revise",
        score=Decimal("4.0"),
        accepted_current_assessment=False,
        expert_review_required_resolved=False,
        override_support_category=None,
        override_support_score=None,
        notes="Needs longer-duration confirmation before final recommendation freeze.",
        reviewed_at=datetime(2024, 3, 1, tzinfo=timezone.utc),
    )

    db.add_all(
        [
            product,
            comparator,
            source_document,
            document_chunk,
            study,
            finding,
            citation_span,
            candidate_pod,
            limitation,
            recommendation,
            calculation_run,
            expert_review,
        ]
    )
    db.commit()

    db.refresh(product)
    db.refresh(comparator)
    db.refresh(source_document)
    db.refresh(study)
    db.refresh(finding)
    db.refresh(candidate_pod)
    db.refresh(calculation_run)
    db.refresh(expert_review)

    return {
        "product_id": product.id,
        "comparator_id": comparator.id,
        "source_document_id": source_document.id,
        "study_id": study.id,
        "finding_id": finding.id,
        "candidate_pod_id": candidate_pod.id,
        "calculation_run_id": calculation_run.id,
        "expert_review_id": expert_review.id,
    }


def main() -> None:
    session_factory = get_session_factory()

    try:
        with session_factory() as db:
            _reset_database(db)
            seeded_ids = seed_demo_report(db)
    except OperationalError as exc:
        print("Unable to connect to the configured database.", file=sys.stderr)
        print(
            "Check apps/backend/.env or DATABASE_URL and make sure the local "
            "PostgreSQL credentials match the configured user/database.",
            file=sys.stderr,
        )
        print(f"Original error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print("Seed complete.")
    for label, value in seeded_ids.items():
        print(f"{label}={value}")

    print("")
    print("Frontend demo URLs:")
    print("http://localhost:3000/report?productId=1")
    print("http://localhost:3000/calculations")
    print("http://localhost:3000/product-overview")


if __name__ == "__main__":
    main()
