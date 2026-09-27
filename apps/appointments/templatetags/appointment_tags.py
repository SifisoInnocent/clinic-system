from django import template

register = template.Library()


@register.filter
def status_color(status):
    """Return Bootstrap color class for appointment status"""
    colors = {
        'pending': 'warning',
        'confirmed': 'primary',
        'completed': 'success',
        'cancelled': 'secondary',
        'no_show': 'danger'
    }
    return colors.get(status, 'secondary')


@register.filter
def status_icon(status):
    """Return icon class for appointment status"""
    icons = {
        'pending': 'clock',
        'confirmed': 'check-circle',
        'completed': 'user-check',
        'cancelled': 'times-circle',
        'no_show': 'user-slash'
    }
    return icons.get(status, 'circle')


@register.filter
def action_icon(action):
    """Return icon class for appointment action"""
    icons = {
        'created': 'plus',
        'cancelled': 'times',
        'rescheduled': 'calendar-alt',
        'completed': 'check',
        'no_show': 'user-slash',
        'status_updated': 'edit',
        'marked_no_show': 'user-slash'
    }
    return icons.get(action, 'circle')


@register.filter
def action_title(action):
    """Return formatted title for appointment action"""
    titles = {
        'created': 'Created',
        'cancelled': 'Cancelled',
        'rescheduled': 'Rescheduled',
        'completed': 'Completed',
        'no_show': 'Marked as No-Show',
        'status_updated': 'Status Updated',
        'marked_no_show': 'Marked as No-Show'
    }
    return titles.get(action, action.replace('_', ' ').title())
