# In core/filters.py
import datetime
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

class TodayDateFieldListFilter(admin.SimpleListFilter):
    title = _('Date')
    parameter_name = 'route__route_date'

    def lookups(self, request, model_admin):
        return (
            ('today', _('Today')),
            ('all', _('All Dates')),
        )

    def queryset(self, request, queryset):
        # Apply the filter if a value is in the URL, otherwise default to 'today'
        filter_value = self.value() or 'today'

        if filter_value == 'today':
            return queryset.filter(route__route_date=datetime.date.today())
        
        if filter_value == 'all':
            return queryset
            
        return queryset

    def choices(self, changelist):
        # This method is overridden to set a default value in the UI
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup if self.value() is not None else lookup == 'today',
                "query_string": changelist.get_query_string({self.parameter_name: lookup}),
                "display": title,
            }

class RouteTodayDateFieldListFilter(admin.SimpleListFilter):
    # This is a new filter specifically for the Route model
    title = _('Date')
    parameter_name = 'route_date'

    def lookups(self, request, model_admin):
        return (('today', _('Today')), ('all', _('All Dates')),)

    def queryset(self, request, queryset):
        filter_value = self.value() or 'today'
        if filter_value == 'today':
            return queryset.filter(route_date=datetime.date.today())
        if filter_value == 'all':
            return queryset
        return queryset

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup if self.value() is not None else lookup == 'today',
                "query_string": changelist.get_query_string({self.parameter_name: lookup}),
                "display": title,
            }