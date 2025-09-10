from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView
from unfold.views import UnfoldModelAdminViewMixin
from .forms import CollectionForm, FailedStopForm
from .models import Stop, Collection

def index(request):
    return render(request, 'core/index.html')

class StopCollectionView(UnfoldModelAdminViewMixin, FormView):
    # We set the main form_class to our new FailedStopForm
    form_class = FailedStopForm
    template_name = "admin/stop_collection_form.html"

    permission_required = ('core.view_stop', 'core.change_stop')

    title = "Failed stop"
    
    def get_success_url(self):
        return reverse_lazy("admin:core_route_driver_dashboard")
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stop'] = self.stop
        context['collection_form'] = CollectionForm()
        context['complete_button'] = {
            "title": "Complete Stop",
            "class": "w-full p-6 text-lg",
            "attrs": {
                "@click": "view = 'complete'",
                "type": "button",
            }
        }
        context['failed_button'] = {
            "title": "Failed Stop",
            "class": "w-full p-6 text-lg bg-red-600 hover:bg-red-700 mb-8",
            "attrs": {
                "@click": "view = 'failed'",
                "type": "button",
            }
        }
        context['back_button'] = {
            "title": "Back",
            "class": "w-full p-6 my-3",
            "variant": "secondary",
            "attrs": {
                "@click.prevent": "view = 'options'",
                "type": "button",
            }
        }
        context["back_to_list_button"] = {
            "title": "Back to Driver Dashboard",
            "href": reverse_lazy("admin:core_route_driver_dashboard"), 
            "class": "mt-4",
            "variant": "secondary",
        }
        return context
        
    def form_valid(self, form):
        # We now check which button was pressed
        if 'submit_failed' in self.request.POST:
            self.stop.status = Stop.Status.FAILED
            self.stop.failure_reason = form.cleaned_data.get('failure_reason')
        
        # We will add the logic for the 'submit_complete' button next
        
        self.stop.save()
        messages.success(self.request, "Stop record updated successfully.")
        return redirect(self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        self.stop = get_object_or_404(Stop, pk=self.kwargs["object_id"])
        return super().dispatch(request, *args, **kwargs)
