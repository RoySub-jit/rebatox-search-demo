from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from app.models.research import CandidatePOD, Study
from app.schemas.limitations import GeneratedLimitation, LimitationSeverity

ROUTE_PATTERN = re.compile(
    r"\b("
    r"oral|po|intravenous|iv|subcutaneous|sc|intramuscular|im|intraperitoneal|ip|"
    r"inhal(?:ed|ation)|dermal|topical|transdermal|intranasal|nasal|ocular|ophthalmic|"
    r"rectal|sublingual|buccal"
    r")\b",
    re.IGNORECASE,
)
HUMAN_PATTERN = re.compile(
    r"\b(human|patient(?:s)?|subject(?:s)?|adult(?:s)?|pediatric|paediatric|child(?:ren)?)\b",
    re.IGNORECASE,
)
NONHUMAN_PATTERN = re.compile(
    r"\b(rat(?:s)?|mouse|mice|rabbit(?:s)?|dog(?:s)?|canine|monkey(?:s)?|macaque(?:s)?|"
    r"minipig(?:s)?|pig(?:s)?|primate(?:s)?)\b",
    re.IGNORECASE,
)
RELEVANCE_PATTERN = re.compile(
    r"\b(species relevance|human relevance|relevant to humans?|translat(?:ion|ional)|"
    r"extrapolat(?:e|ion|ing)|clinically relevant)\b",
    re.IGNORECASE,
)
POD_PATTERN = re.compile(
    r"\b(point of departure|pod|noael|loael|noel|loel|bmdl?|bmcl|benchmark dose)\b",
    re.IGNORECASE,
)
DOSE_UNIT_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mg|g|ug|mcg|ng|µg)\s*"
    r"(?:/kg(?:/day)?|/day|/person/day|/animal/day)?\b|\b\d+(?:\.\d+)?\s*(?:ppm|ppb)\b",
    re.IGNORECASE,
)
DOSE_CONTEXT_PATTERN = re.compile(
    r"\b(dose|doses|dosed|dosing|dosage|exposure|concentration|dose-response)\b",
    re.IGNORECASE,
)
LOW_CONFIDENCE_STATUS_PATTERN = re.compile(
    r"\b(low[_ -]?confidence|needs[_ -]?review|unverified|uncertain|provisional)\b",
    re.IGNORECASE,
)
ANALOG_ONLY_PATTERN = re.compile(
    r"\b(analog|analogue|read[- ]?across|bridg(?:e|ing)|surrogate|proxy|related compound|class effect)\b",
    re.IGNORECASE,
)
LOW_CONFIDENCE_THRESHOLD = Decimal("0.60")
BLOCKING_CONFIDENCE_THRESHOLD = Decimal("0.30")


@dataclass(frozen=True)
class RuleContext:
    study_text: str
    pod_text: str
    combined_text: str
    confidence_score: Decimal | None
    route_present: bool
    human_signal_present: bool
    nonhuman_signal_present: bool
    relevance_signal_present: bool
    explicit_pod_present: bool
    dose_unit_count: int
    dose_context_hits: int
    low_confidence_status_present: bool
    analog_only_signal_present: bool


def _join_text(*parts: str | None) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _normalize_confidence_score(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None

    if value > Decimal("1"):
        return value / Decimal("100")

    return value


def _build_context(*, study: Study, candidate_pod: CandidatePOD) -> RuleContext:
    study_text = _join_text(
        study.title,
        study.objective,
        study.study_design,
        study.population,
        study.status,
    )
    pod_text = _join_text(
        candidate_pod.title,
        candidate_pod.claim_text,
        candidate_pod.rationale,
        candidate_pod.status,
    )
    combined_text = _join_text(study_text, pod_text)

    return RuleContext(
        study_text=study_text,
        pod_text=pod_text,
        combined_text=combined_text,
        confidence_score=_normalize_confidence_score(candidate_pod.confidence_score),
        route_present=bool(ROUTE_PATTERN.search(combined_text)),
        human_signal_present=bool(HUMAN_PATTERN.search(combined_text)),
        nonhuman_signal_present=bool(NONHUMAN_PATTERN.search(combined_text)),
        relevance_signal_present=bool(RELEVANCE_PATTERN.search(combined_text)),
        explicit_pod_present=bool(POD_PATTERN.search(pod_text)),
        dose_unit_count=len(DOSE_UNIT_PATTERN.findall(combined_text)),
        dose_context_hits=len(DOSE_CONTEXT_PATTERN.findall(combined_text)),
        low_confidence_status_present=bool(
            LOW_CONFIDENCE_STATUS_PATTERN.search(candidate_pod.status or "")
        ),
        analog_only_signal_present=bool(ANALOG_ONLY_PATTERN.search(combined_text)),
    )


class RuleBasedLimitationGenerator:
    def generate(
        self,
        *,
        study: Study | None,
        candidate_pod: CandidatePOD | None,
    ) -> list[GeneratedLimitation]:
        if study is None or candidate_pod is None:
            return []

        context = _build_context(study=study, candidate_pod=candidate_pod)
        limitations: list[GeneratedLimitation] = []

        if not context.route_present:
            limitations.append(
                GeneratedLimitation(
                    limitation_type="missing_route",
                    title="Missing route",
                    description=(
                        "Route of administration is not explicit across the study and candidate POD fields."
                    ),
                    severity="medium",
                    why_it_matters=(
                        "Route changes exposure comparability and can materially alter how a study result supports a product-specific POD."
                    ),
                    resolution_suggestion=(
                        "Add the route of administration to the study summary or candidate POD rationale and confirm downstream calculations use the same route basis."
                    ),
                    is_blocking=False,
                )
            )

        if self._is_missing_species_relevance(context):
            limitations.append(
                GeneratedLimitation(
                    limitation_type="missing_species_relevance",
                    title="Missing species relevance",
                    description=(
                        "Species relevance is not explicit in the study or candidate POD justification."
                    ),
                    severity="high",
                    why_it_matters=(
                        "Without a clear human population or a species-to-human relevance rationale, extrapolation of the evidence is hard to defend."
                    ),
                    resolution_suggestion=(
                        "State the study species or human population directly and add a short explanation for why that evidence is relevant to the target decision context."
                    ),
                    is_blocking=True,
                )
            )

        if not context.explicit_pod_present:
            limitations.append(
                GeneratedLimitation(
                    limitation_type="no_explicit_pod",
                    title="No explicit POD",
                    description=(
                        "The candidate POD text does not name an explicit point of departure."
                    ),
                    severity="high",
                    why_it_matters=(
                        "Downstream calculations and review narratives need a clearly named POD such as a NOAEL, LOAEL, or benchmark dose."
                    ),
                    resolution_suggestion=(
                        "Update the candidate POD title or rationale to name the selected POD and the basis for selection."
                    ),
                    is_blocking=True,
                )
            )

        if self._has_sparse_dose_context(context):
            limitations.append(
                GeneratedLimitation(
                    limitation_type="sparse_dose_context",
                    title="Sparse dose context",
                    description=(
                        "Dose context is too thin to confidently interpret the candidate POD."
                    ),
                    severity="medium",
                    why_it_matters=(
                        "A POD is difficult to evaluate when the supporting text does not clearly anchor dose level or exposure context."
                    ),
                    resolution_suggestion=(
                        "Add dose levels or exposure units to the study summary and candidate POD rationale so reviewers can trace the quantitative basis."
                    ),
                    is_blocking=True,
                )
            )

        low_confidence_limitation = self._build_low_confidence_limitation(context)
        if low_confidence_limitation is not None:
            limitations.append(low_confidence_limitation)

        if context.analog_only_signal_present:
            limitations.append(
                GeneratedLimitation(
                    limitation_type="analog_only_evidence",
                    title="Analog-only evidence",
                    description=(
                        "The current support appears to rely on analog, bridge, or read-across evidence."
                    ),
                    severity="high",
                    why_it_matters=(
                        "Analog-only support can weaken traceability to the indexed product and may require stronger caveats or corroborating evidence."
                    ),
                    resolution_suggestion=(
                        "Add direct product-specific evidence if available, or document why the analog or bridge evidence is sufficient for the decision."
                    ),
                    is_blocking=False,
                )
            )

        return limitations

    @staticmethod
    def _is_missing_species_relevance(context: RuleContext) -> bool:
        if context.human_signal_present:
            return False

        if context.nonhuman_signal_present and context.relevance_signal_present:
            return False

        return True

    @staticmethod
    def _has_sparse_dose_context(context: RuleContext) -> bool:
        if context.dose_unit_count == 0:
            return True

        if context.dose_unit_count == 1 and context.dose_context_hits < 2:
            return True

        return False

    @staticmethod
    def _build_low_confidence_limitation(
        context: RuleContext,
    ) -> GeneratedLimitation | None:
        score = context.confidence_score

        if score is None:
            if not context.low_confidence_status_present:
                return None

            severity: LimitationSeverity = "medium"
            is_blocking = False
        elif score < BLOCKING_CONFIDENCE_THRESHOLD:
            severity = "high"
            is_blocking = True
        elif score < LOW_CONFIDENCE_THRESHOLD:
            severity = "medium"
            is_blocking = False
        else:
            return None

        return GeneratedLimitation(
            limitation_type="low_confidence_extraction",
            title="Low extraction confidence",
            description=(
                "The candidate POD extraction confidence is low enough to warrant explicit review."
            ),
            severity=severity,
            why_it_matters=(
                "Low-confidence extraction increases the chance that the selected POD or its supporting context was captured incorrectly or incompletely."
            ),
            resolution_suggestion=(
                "Re-review the source text, confirm the extracted POD wording, and raise the confidence score only after verification."
            ),
            is_blocking=is_blocking,
        )


def generate_rule_based_limitations(
    *,
    study: Study | None,
    candidate_pod: CandidatePOD | None,
) -> list[GeneratedLimitation]:
    return RuleBasedLimitationGenerator().generate(
        study=study,
        candidate_pod=candidate_pod,
    )
