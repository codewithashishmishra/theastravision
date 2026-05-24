from datetime import date

from .models import TaxAiTipUsage
from .tax_ai_constants import TAX_AI_MONTHLY_LIMIT


def current_period() -> str:
    today = date.today()
    return f'{today.year}-{today.month:02d}'


def get_credit_status(employee) -> dict:
    period = current_period()
    used = TaxAiTipUsage.objects.filter(employee=employee, period=period).count()
    remaining = max(0, TAX_AI_MONTHLY_LIMIT - used)
    last = (
        TaxAiTipUsage.objects.filter(employee=employee, period=period)
        .order_by('-created_at')
        .first()
    )
    return {
        'used': used,
        'limit': TAX_AI_MONTHLY_LIMIT,
        'remaining': remaining,
        'period': period,
        'last_tips': last.response_snapshot if last else None,
    }


def can_consume_credit(employee) -> bool:
    return get_credit_status(employee)['remaining'] > 0
