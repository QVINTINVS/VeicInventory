from django import forms
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

import django_rq

from .models import WRFStandardEmission


class WRFStandardEmissionForm(forms.ModelForm):
    class Meta:
        model = WRFStandardEmission
        fields = "__all__"
        widgets = {
            "fuel": forms.Select(attrs={"class": "form-control"}),
            "fraction": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Ex: 15 (%)"}
            ),
            "mileage": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Ex: 12.5 (km/L)"}
            ),
            "note": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Observação ou nota"}
            ),
            "subcategory": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "note": "Nota do veículo",
            "fraction": "Fração do Veículo na frota",
            "mileage": "Autonomia do Veículo (km/L ou km/kWh)",
            "fuel": "Combustível",
            "subcategory": "Subcategoria",
        }


class WRFStandardEmissionListView(ListView):
    model = WRFStandardEmission
    template_name = "wrf_standard_list.html"



class _WRFStandardEmissionFormMixin:
    """Shared configuration for the add/edit views.

    Provides template selection (normal vs. modal) and guarantees that the
    rendered form carries an ``action`` URL so that JavaScript does not need to
    guess where to post.
    """

    model = WRFStandardEmission
    form_class = WRFStandardEmissionForm
    template_name = "wrf_standard_form.html"
    success_url = reverse_lazy("wrf-standard")

    def get_template_names(self):
        if self.request.GET.get("modal"):
            return ["wrf_standard_form_modal.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # ``request.path`` excludes querystring (so ?modal=1 is dropped)
        ctx["form_action"] = self.request.path
        return ctx

    def form_valid(self, form):
        # subclasses should override to add a message, but keep the common
        # success behaviour.
        return super().form_valid(form)


class WRFStandardEmissionCreateView(_WRFStandardEmissionFormMixin, CreateView):
    def form_valid(self, form):
        messages.success(self.request, "Emissão adicionada com sucesso.")
        return super().form_valid(form)


class WRFStandardEmissionUpdateView(_WRFStandardEmissionFormMixin, UpdateView):
    def form_valid(self, form):
        messages.success(self.request, "Emissão atualizada com sucesso.")
        return super().form_valid(form)


class WRFStandardEmissionDeleteView(DeleteView):
    model = WRFStandardEmission
    success_url = reverse_lazy("wrf-standard")

    def get(self, request, *args, **kwargs):
        # avoid rendering the built-in confirmation page; the UI uses a
        # POST form directly. Redirect to list instead of requiring a template.
        return redirect(self.success_url)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        pk = obj.pk
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Emissão com ID {pk} removida.")
        return response

from django.http import JsonResponse
from django.views.generic import TemplateView

import numpy as np
import xarray as xr
import os
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin

# decorator to allow xframe iframe
@method_decorator(xframe_options_sameorigin, name='dispatch') 
class WRFStandardVisualizeView(TemplateView):
    """Lightweight page used inside the visualization modal.

    The iframe inside the modal will hit this view, which currently only
    renders a placeholder template. Later on we can add javascript,
    context data, or other helpers to actually plot the NetCDF files.
    """

    template_name = "render_plot.html"


def get_netcdf_data(request):
    # data_variable = request.GET.get("data_variable", "CO2_BIO")
    data_variable = request.GET.get("data_variable", "DUCMASS")
    altitude = int(request.GET.get("altitude", 0))

    # Path to the test.nc file
    # nc_file_path = os.path.join(settings.BASE_DIR.parent, 'test', 'test.nc')
    nc_file_path = "/app/services/web/test/test.nc"

    dataset = xr.open_dataset(nc_file_path, engine="netcdf4")

    # Latitudes and longitudes
    # lats = dataset["south_north"].values
    # lons = dataset["west_east"].values
    lats = dataset["lat"].values
    lons = dataset["lon"].values

    # Handle MaskedArrays
    if isinstance(lats, np.ma.MaskedArray):
        lats = lats.filled(np.nan)
    if isinstance(lons, np.ma.MaskedArray):
        lons = lons.filled(np.nan)

    # Get all variable names
    variable_names = dataset.variables.keys()
    target_vars = [var for var in variable_names if len(dataset.variables[var].dims) == 3]

    variable = dataset.variables[data_variable]
    # description = getattr(variable, "description", "N/A")
    description = getattr(variable, "long_name", "N/A")
    units = getattr(variable, "units", "N/A")

    variable_values = variable.values
    zmin = float(np.nanmin(variable_values))
    zmax = float(np.nanmax(variable_values))

    if isinstance(variable_values, np.ma.MaskedArray):
        variable_values = variable_values.filled(np.nan)

    variable_frames = []
    # for t_idx in range(variable.sizes["Time"]):
    print(f"variable.sizes: {variable.sizes}")
    
    for t_idx in range(variable.sizes["time"]):
        frame = variable.isel(time=t_idx).values
        # frame = variable.isel(valid_time=t_idx).values
        # frame = variable.isel(valid_time=t_idx, pressure_level=altitude).values
        variable_frames.append(frame.tolist())

    dataset.close()

    return JsonResponse({
        "lats": lats.tolist(),
        "lons": lons.tolist(),
        "time": [],  # Not used in JS
        "frames": variable_frames,
        "target_vars": target_vars,
        "description": description,
        "units": units,
        "zmin": zmin,
        "zmax": zmax,
        "alts_length": 0,
    })

def process_emission(request):
    if request.method == 'POST':
        print("Processar button clicked - backend interaction test")

        queue = django_rq.get_queue("emission_queue")
        payload = request.body.decode("utf-8") if request.body else "{}"
        queue.enqueue("tasks.process_emission", payload)

        return JsonResponse({'status': 'success', 'message': 'Processing started'})
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})
