import numpy as np
import xarray as xr
from flask import flash, jsonify, redirect, render_template, request, url_for
from forms.wrf_standard_emission_form import WRFStandardEmissionForm
from repositories.wrf_standard_emission_repository import WRFStandardEmissionRepository
from repositories.wrfchemi_blobs import MinioRepository


class WRFStandardEmissionView:
    def __init__(
        self,
        vehicle_emissions_repository: WRFStandardEmissionRepository,
        wrfchemi_blobs_repository: MinioRepository,
    ):
        self.__inventory = vehicle_emissions_repository
        self.__wrfchemi = wrfchemi_blobs_repository

    def render_inventory_page(self):
        vehicle_emissions = self.__inventory.list_emissions()

        return render_template(
            "index.html",
            emission_data=vehicle_emissions,
            form=WRFStandardEmissionForm(),
        )

    def add_vehicle_emission(self):
        vasques_form: WRFStandardEmissionForm = WRFStandardEmissionForm()

        if vasques_form.validate_on_submit():
            vehicle_form_data = vasques_form.vehicle

            self.__inventory.save_vehicle_emission(vehicle_form_data)

        return redirect(url_for("wrf_standard.render_inventory_page"))

    def delete_vehicle_emission(self, emission_id: int):
        # TODO: return a status value that will be passed to the template
        try:
            self.__inventory.delete_data_by_id(emission_id)
        except Exception:
            flash(f"Emission with ID {emission_id} not found.", "error")

        return redirect(url_for("wrf_standard.render_inventory_page"))

    # TODO: move this method to a dedicated class
    def visualize(self):
        from django.shortcuts import render

        return render(request, "render_plot.html")

    # TODO: move this method to a dedicated class, same as visualize
    def get_netcdf_data(
        self, data_variable: str | None = None, altitude: int | None = None
    ):
        data_variable = request.args.get("data_variable")
        if not data_variable:
            # data_variable = "CO2_BIO"
            data_variable = "number"

        altitude = request.args.get("altitude", type=int)
        if not altitude:
            altitude = 0

        # nc_file = self.__wrfchemi.read_file(prefix="round_1")
        nc_file = self.__wrfchemi.read_file(prefix="test.nc")

        # dataset = xr.open_dataset(nc_file, engine="scipy")
        dataset = xr.open_dataset(nc_file, engine="netcdf4")

        # --- Altitudes ---
        # Parece que você queria só um eixo vertical da grade
        # alts = dataset["west_east"].isel(south_north=0, west_east=0).values
        # alts_length = alts.size

        # --- Latitudes e longitudes ---
        # XLAT e XLONG geralmente têm dims (time, south_north, west_east)
        # Selecionando slice na dimensão altitude (ou time se for o caso)
        
        # lats = dataset["south_north"].values
        # lons = dataset["west_east"].values
        lats = dataset["latitude"].values
        lons = dataset["longitude"].values

        # Handle MaskedArrays
        if isinstance(lats, np.ma.MaskedArray):
            lats = lats.filled(np.nan)  # Replace masked values with NaN
        if isinstance(lons, np.ma.MaskedArray):
            lons = lons.filled(np.nan)  # Replace masked values with NaN

        # Extract time and CO2_ANT data
        # times = dataset["Time"].values
        times = dataset["valid_time"].values

        # Get all variable names
        variable_names = dataset.variables.keys()

        # Filter the ones containing XTIME, XLAT, and XLONG
        target_vars = [var for var in variable_names if len(dataset.variables[var].dims) >= 3]
        variable = dataset.variables[data_variable]

        description = getattr(variable, "description", "N/A")
        units = getattr(variable, "units", "N/A")

        variable_values = variable.values  # Convert to NumPy array
        # print(f"target_vars: {target_vars}")

        zmin = float(np.nanmin(variable_values))
        zmax = float(np.nanmax(variable_values))

        # Handle MaskedArrays for CO2_ANT
        if isinstance(variable_values, np.ma.MaskedArray):
            variable_values = variable_values.filled(
                np.nan
            )  # Replace masked values with NaN

        variable_frames = []

        for t_idx in range(variable.sizes["valid_time"]):  # iterando sobre a dimensão tempo
            # isel seleciona por índice
            frame = variable.isel(valid_time=t_idx).values  # np.ndarray 2D
            variable_frames.append(frame.tolist())

        # Close the dataset
        dataset.close()
    
        # Prepare and return JSON response
        return jsonify(
            {
                "lats": lats.tolist(),
                "lons": lons.tolist(),
                "time": times.tolist(),  # Match variable name to the JS code
                "frames": variable_frames,
                "target_vars": target_vars,
                "description": description,
                "units": units,
                "zmin": zmin,
                "zmax": zmax,
                "alts_length": 0,
            }
        )
