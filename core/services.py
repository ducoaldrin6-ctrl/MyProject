from dataclasses import dataclass
from math import log1p

from django.db.models import Count, Q


@dataclass
class RiskAssessment:
    scholar: object
    score: int
    level: str
    confidence: str
    method: str
    factors: list
    recommendations: list
    attendance_rate: int | None
    attendance_count: int


def _scholar_data(queryset):
    return list(
        queryset.annotate(
            risk_attendance_count=Count('attendance_records', distinct=True),
            risk_absent_count=Count(
                'attendance_records',
                filter=Q(attendance_records__status='absent'),
                distinct=True,
            ),
            risk_late_count=Count(
                'attendance_records',
                filter=Q(attendance_records__status='late'),
                distinct=True,
            ),
            risk_application_count=Count('applications', distinct=True),
            risk_rejected_count=Count(
                'applications',
                filter=Q(applications__status='rejected'),
                distinct=True,
            ),
        ).order_by('last_name', 'first_name')
    )


def _features(scholar):
    attendance_count = scholar.risk_attendance_count
    application_count = scholar.risk_application_count
    return [
        scholar.risk_absent_count / attendance_count if attendance_count else 0,
        scholar.risk_late_count / attendance_count if attendance_count else 0,
        log1p(attendance_count),
        scholar.risk_rejected_count / application_count if application_count else 0,
        int(scholar.year_level),
    ]


def _baseline_score(scholar, features):
    absence_rate, late_rate, _, rejected_rate, _ = features
    score = 8 + min(36, absence_rate * 72) + min(18, late_rate * 36) + min(18, rejected_rate * 24)
    if scholar.status == 'probation':
        score += 20
    elif scholar.status == 'inactive':
        score += 34
    return min(95, round(score))


def _explanation(scholar, features):
    absence_rate, late_rate, _, rejected_rate, _ = features
    factors = []
    recommendations = []

    if scholar.risk_attendance_count < 3:
        factors.append('Limited attendance history; confidence is reduced.')
        recommendations.append('Record regular attendance to improve the assessment.')
    if absence_rate >= 0.2:
        factors.append(f'{absence_rate:.0%} of recorded attendance is absent.')
        recommendations.append('Schedule an attendance check-in with the scholar.')
    if late_rate >= 0.2:
        factors.append(f'{late_rate:.0%} of recorded attendance is late.')
        recommendations.append('Discuss schedule or transportation barriers.')
    if rejected_rate:
        factors.append('Application history includes a rejected submission.')
        recommendations.append('Review the rejection reason and required documents.')
    if scholar.status == 'probation':
        factors.append('The scholar is currently marked as on probation.')
    elif scholar.status == 'inactive':
        factors.append('The scholar is currently marked as inactive.')
    if not factors:
        factors.append('No material concern is visible in the available records.')
    if not recommendations:
        recommendations.append('Continue routine monitoring and attendance recording.')
    return factors, recommendations


def assess_scholar_risk(queryset):
    """Return explainable retention-support estimates, never eligibility decisions."""
    scholars = _scholar_data(queryset)
    feature_rows = [_features(scholar) for scholar in scholars]
    labels = [int(scholar.status != 'active') for scholar in scholars]
    probabilities = None
    method = 'Guided baseline'

    # Logistic regression is used only when enough local outcomes exist for both classes.
    if len(scholars) >= 20 and min(labels.count(0), labels.count(1)) >= 5:
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler

            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(class_weight='balanced', max_iter=500, random_state=42),
            )
            model.fit(feature_rows, labels)
            probabilities = model.predict_proba(feature_rows)[:, 1]
            method = 'Local logistic regression'
        except (ImportError, ValueError):
            probabilities = None

    assessments = []
    for index, (scholar, features) in enumerate(zip(scholars, feature_rows)):
        score = round(probabilities[index] * 100) if probabilities is not None else _baseline_score(scholar, features)
        level = 'high' if score >= 60 else 'medium' if score >= 35 else 'low'
        confidence = 'high' if scholar.risk_attendance_count >= 10 else 'medium' if scholar.risk_attendance_count >= 3 else 'low'
        factors, recommendations = _explanation(scholar, features)
        attendance_rate = None
        if scholar.risk_attendance_count:
            attended = scholar.risk_attendance_count - scholar.risk_absent_count
            attendance_rate = round(attended / scholar.risk_attendance_count * 100)
        assessments.append(RiskAssessment(
            scholar=scholar,
            score=score,
            level=level,
            confidence=confidence,
            method=method,
            factors=factors,
            recommendations=recommendations,
            attendance_rate=attendance_rate,
            attendance_count=scholar.risk_attendance_count,
        ))
    return assessments
