from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Fieldset, Layout, Row
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView
from unfold.forms import AuthenticationForm
from unfold.layout import Submit
from unfold.widgets import (
    UnfoldAdminCheckboxSelectMultiple,
    UnfoldAdminDateWidget,
    UnfoldAdminEmailInputWidget,
    UnfoldAdminExpandableTextareaWidget,
    UnfoldAdminFileFieldWidget,
    UnfoldAdminImageFieldWidget,
    UnfoldAdminIntegerFieldWidget,
    UnfoldAdminRadioSelectWidget,
    UnfoldAdminSelect2Widget,
    UnfoldAdminSplitDateTimeWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminTextInputWidget,
    UnfoldAdminTimeWidget,
    UnfoldAdminURLInputWidget,
    UnfoldBooleanSwitchWidget,
)
from .models import Collection, Stop

class CollectionForm(forms.ModelForm):

    class Meta:
        model = Collection
        fields = [
            'waste_oil_quantity', 'payment_made', 'docket_number', 
            'fresh_oil_total_litres', 'payment_received', 'docket_image',
        ]
        widgets = {
            "waste_oil_quantity": UnfoldAdminIntegerFieldWidget(),
            "payment_made": UnfoldAdminIntegerFieldWidget(),
            "docket_number": UnfoldAdminTextInputWidget(),
            "fresh_oil_total_litres": UnfoldAdminIntegerFieldWidget(),
            "payment_received": UnfoldAdminIntegerFieldWidget(),
            "docket_image": UnfoldAdminImageFieldWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))
        self.helper.form_class = "form-horizontal"
        self.helper.layout = Layout(
            Row(
                Fieldset(
                _("Waste Oil"),
                    "waste_oil_quantity",
                    "payment_made",
                    "docket_number",
                    "docket_image",  
                ),
                Fieldset(
                    _("Fresh Oil"),
                    "fresh_oil_total_litres",
                    "payment_received",
                ), css_class="gap-5 mb-8"
            )
        )

class FailedStopForm(forms.ModelForm):

    failure_reason = forms.ChoiceField(
        choices=Stop.FailureReason.choices,
        initial=Stop.FailureReason.NO_COLLECTION,
        label="Failure Reason",
        widget=UnfoldAdminRadioSelectWidget()
    )

    class Meta:
        model = Stop
        fields = [
            'failure_reason', 'notes',
        ]
        widgets = {
            "notes": UnfoldAdminTextareaWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        initial_reason = self.initial.get('failure_reason', 'NO_COLLECTION')
        if initial_reason is None:
            initial_reason = ''
        self.helper.attrs = {'x-data': f"{{ reason: '{initial_reason}' }}"}
        self.fields['failure_reason'].widget.attrs['x-model'] = 'reason'

        self.helper.add_input(Submit('submit_failed', 'Save Failure'))
        self.helper.form_class = "form-horizontal"
        self.helper.layout = Layout(
            Row(
                Fieldset(
                    _("Failure"),
                    "failure_reason",
                    Div(
                        "notes",
                        **{'x-show': "reason === 'OTHER'"}
                    ), 
                ), css_class="mb-8"
            )
        )

