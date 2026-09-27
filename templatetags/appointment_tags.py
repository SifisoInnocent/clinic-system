from django import template

register = template.Library()

@register.filter
def filter_status(queryset, status):
    """Filter appointments by status"""
    return queryset.filter(status=status)

@register.filter
def status_color(status):
    """Return Bootstrap color class based on appointment status"""
    colors = {
        'pending': 'warning',
        'confirmed': 'info',
        'completed': 'success',
        'cancelled': 'secondary',
        'no_show': 'danger'
    }
    return colors.get(status, 'secondary')
