"""
Test each API call of biolovision_api module.
"""

import json
import logging
import time
from datetime import datetime, timedelta

import pytest

from biolovision.api import (
    EntitiesAPI,
    FamiliesAPI,
    FieldsAPI,
    HTTPError,
    IncorrectParameter,
    LocalAdminUnitsAPI,
    MaxChunksError,
    ObservationsAPI,
    ObserversAPI,
    PlacesAPI,
    SpeciesAPI,
    TaxoGroupsAPI,
    TerritorialUnitsAPI,
    ValidationsAPI,
)
from export_vn.evnconf import EvnConf

# Using faune-france site, that needs to be defined in .evn_test.yaml
SITE = "tff"
FILE = ".evn_test.yaml"

# Get configuration for test site
CFG = EvnConf(FILE).site_list[SITE]
ENTITIES_API = EntitiesAPI(CFG)
FAMILIES_API = FamiliesAPI(CFG)
FIELDS_API = FieldsAPI(CFG)
LOCAL_ADMIN_UNITS_API = LocalAdminUnitsAPI(CFG)
OBSERVATIONS_API = ObservationsAPI(CFG)
OBSERVERS_API = ObserversAPI(CFG)
PLACES_API = PlacesAPI(CFG)
SPECIES_API = SpeciesAPI(CFG)
SPECIES_API_ERR = SpeciesAPI(CFG, max_retry=1, max_requests=1, max_chunks=1)
TAXO_GROUPS_API = TaxoGroupsAPI(CFG)
TERRITORIAL_UNITS_API = TerritorialUnitsAPI(CFG)
VALIDATIONS_API = ValidationsAPI(CFG)


# ---------------
# Various testing
# ---------------
@pytest.mark.order(index=100)
class TestVarious:
    def test_version(self):
        """Check if version is defined."""
        logging.debug("package version: %s", ENTITIES_API.version)

    def test_wrong_api(self):
        """Raise an exception."""
        with pytest.raises(HTTPError) as excinfo:
            error = PLACES_API.wrong_api()  # noqa: F841
        logging.debug("HTTPError code %s", excinfo)


# ----------------------------
# Taxo_group controler methods
# ----------------------------
@pytest.mark.order(index=110)
class TestTaxoGroups:
    def test_taxo_groups_controler(self):
        """Check controler name."""
        ctrl = TAXO_GROUPS_API.controler
        assert ctrl == "taxo_groups"

    def test_taxo_groups_get(self):
        """Get a taxo_groups."""
        taxo_group = TAXO_GROUPS_API.api_get("2")
        assert TAXO_GROUPS_API.transfer_errors == 0
        assert taxo_group["data"][0]["name"] == "Chauves-souris"

    def test_taxo_groups_list(self):
        """Get list of taxo_groups."""
        # First call, should return from API call if not called before
        start = time.perf_counter()
        taxo_groups = TAXO_GROUPS_API.api_list()
        took = (time.perf_counter() - start) * 1000.0
        logging.debug("taxo_groups_list, call 1 took: " + str(took) + " ms")
        assert TAXO_GROUPS_API.transfer_errors == 0
        assert len(taxo_groups["data"]) >= 30
        assert taxo_groups["data"][0]["name"] == "Oiseaux"
        assert taxo_groups["data"][18]["name"] == "Coléoptères"
        # Second call, must return from cache
        start = time.perf_counter()
        taxo_groups = TAXO_GROUPS_API.api_list()
        took = (time.perf_counter() - start) * 1000.0
        logging.debug("taxo_groups_list, call 2 took: " + str(took) + " ms")
        start = time.perf_counter()
        taxo_groups = TAXO_GROUPS_API.api_list()
        took = (time.perf_counter() - start) * 1000.0
        logging.debug("taxo_groups_list, call 3 took: " + str(took) + " ms")
        assert TAXO_GROUPS_API.transfer_errors == 0
        assert len(taxo_groups["data"]) >= 30
        assert taxo_groups["data"][0]["name"] == "Oiseaux"
        assert taxo_groups["data"][18]["name"] == "Coléoptères"


# --------------------------
# Families controler methods
# --------------------------
@pytest.mark.order(index=111)
class TestFamilies:
    def test_families_controler(self):
        """Check controler name."""
        ctrl = FAMILIES_API.controler
        assert ctrl == "families"

    def test_families_get(self):
        """Get a family."""
        families = FAMILIES_API.api_get("1")
        assert FAMILIES_API.transfer_errors == 0
        assert families["data"][0]["generic"] == "0"
        assert families["data"][0]["id"] == "1"

    def test_families_list(self):
        """Get list of families."""
        families = FAMILIES_API.api_list()
        assert FAMILIES_API.transfer_errors == 0
        assert len(families["data"]) >= 80
        assert families["data"][0]["id"] == "1"


# -------------------------
# Species controler methods
# -------------------------
@pytest.mark.order(index=112)
class TestSpecies:
    def test_species_controler(self):
        """Check controler name."""
        ctrl = SPECIES_API.controler
        assert ctrl == "species"

    def test_species_get(self):
        """Get a single specie."""
        logging.debug("Getting species from taxo_group %s", "2")
        specie = SPECIES_API.api_get("2")
        assert SPECIES_API.transfer_errors == 0
        assert specie["data"][0]["french_name"] == "Plongeon arctique"

    @pytest.mark.slow
    def test_species_list_all(self):
        """Get list of all species."""
        species_list = SPECIES_API.api_list()
        logging.debug("Received %d species", len(species_list["data"]))
        assert SPECIES_API.transfer_errors == 0
        assert len(species_list["data"]) >= 38820

    def test_species_list_1(self):
        """Get a list of species from taxo_group 1."""
        species_list = SPECIES_API.api_list({"id_taxo_group": "1"})
        logging.debug("Taxo_group 1 ==> {} species".format(len(species_list["data"])))
        assert SPECIES_API.transfer_errors == 0
        assert len(species_list["data"]) >= 11150
        assert species_list["data"][0]["french_name"] == "Plongeon catmarin"

    def test_species_list_30(self):
        """Get a list of species from taxo_group 30."""
        species_list = SPECIES_API.api_list({"id_taxo_group": "30"})
        logging.debug("Taxo_group 30 ==> {} species".format(len(species_list["data"])))
        assert SPECIES_API.transfer_errors == 0
        assert species_list["data"][0]["french_name"] == "Aucune espèce"

    def test_species_list_30_diff(self):
        """Get a list of updated species from taxo_group 30."""
        species_list = SPECIES_API.api_list(
            {"id_taxo_group": "30"},
            optional_headers={"If-Modified-Since": datetime(2019, 2, 1).strftime("%a, %d %b %Y %H:%M:%S GMT")},
            # optional_headers={"If-Modified-Since": "Sun, 01 Sep 2019 00:00:00 GMT"},
        )
        logging.debug("Taxo_group 30 ==> {} species".format(len(species_list["data"])))
        assert SPECIES_API.transfer_errors == 0

    def test_species_list_error(self):
        """Get a list of species from taxo_group 1, limited to 1 chunk."""
        with pytest.raises(MaxChunksError) as excinfo:  # noqa: F841
            species_list = SPECIES_API_ERR.api_list(  # noqa: F841
                {"id_taxo_group": "1"}
            )


# -----------------------------------
# Territorial_units controler methods
# -----------------------------------
@pytest.mark.order(index=120)
class TestTerritorialUnits:
    def test_territorial_units_controler(self):
        """Check controler name."""
        ctrl = TERRITORIAL_UNITS_API.controler
        assert ctrl == "territorial_units"

    def test_territorial_units_get(self):
        """Get territorial_units."""
        territorial_unit = TERRITORIAL_UNITS_API.api_get("39")
        assert TERRITORIAL_UNITS_API.transfer_errors == 0
        assert territorial_unit["data"][0]["name"] == "Isère"
        territorial_unit = TERRITORIAL_UNITS_API.api_get("07")
        assert TERRITORIAL_UNITS_API.transfer_errors == 0
        assert territorial_unit["data"][0]["name"] == "Ardèche"

    def test_territorial_units_list(self):
        """Get list of territorial_units."""
        # First call, should return from API call if not called before
        start = time.perf_counter()
        territorial_units = TERRITORIAL_UNITS_API.api_list()
        took1 = (time.perf_counter() - start) * 1000.0
        logging.debug("territorial_units_list, call 1 took: " + str(took1) + " ms")
        assert TERRITORIAL_UNITS_API.transfer_errors == 0
        assert len(territorial_units["data"]) > 100
        logging.debug(territorial_units["data"])
        assert territorial_units["data"][6]["name"] == "Ardèche"
        assert territorial_units["data"][38]["name"] == "Isère"
        start = time.perf_counter()
        territorial_units = TERRITORIAL_UNITS_API.api_list()
        took2 = (time.perf_counter() - start) * 1000.0
        logging.debug("territorial_units_list, call 2 took: " + str(took2) + " ms")
        assert TERRITORIAL_UNITS_API.transfer_errors == 0
        assert took2 < took1


# ------------------------------------
#  Local admin units controler methods
# ------------------------------------
@pytest.mark.order(index=121)
class TestLocalAdminUnits:
    def test_local_admin_units_controler(self):
        """Check controler name."""
        ctrl = LOCAL_ADMIN_UNITS_API.controler
        assert ctrl == "local_admin_units"

    def test_local_admin_units_get(self):
        """Get a single local admin unit."""
        a = "14693"
        logging.debug("Getting local admin unit %s", a)
        local_admin_unit = LOCAL_ADMIN_UNITS_API.api_get(a)
        assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
        assert local_admin_unit == {
            "data": [
                {
                    "name": "Allevard",
                    "coord_lon": "6.11353081638029",
                    "id_canton": "39",
                    "coord_lat": "45.3801954314357",
                    "id": "14693",
                    "insee": "38006",
                }
            ]
        }

    def test_local_admin_units_list_all(self):
        """Get list of all local admin units."""
        logging.debug("Getting all local admin unit")
        local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list()
        logging.debug("Received %d local admin units", len(local_admin_units_list["data"]))
        assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
        assert len(local_admin_units_list["data"]) >= 35000

    def test_local_admin_units_list_1(self):
        """Get a list of local_admin_units from territorial units."""
        # 39 (Isère)
        logging.debug("Getting local admin unit from {id_canton: 39}")
        local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list(opt_params={"id_canton": "39"})
        logging.debug("territorial unit ==> {} local admin unit ".format(len(local_admin_units_list["data"])))
        assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
        assert len(local_admin_units_list["data"]) >= 534
        assert local_admin_units_list["data"][0]["name"] == "Abrets (Les)"
        # 07 (Ardèche)
        logging.debug("Getting local admin unit from {id_canton: 07}")
        local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list(opt_params={"id_canton": "07"})
        logging.debug("territorial unit ==> {} local admin unit ".format(len(local_admin_units_list["data"])))
        assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
        assert len(local_admin_units_list["data"]) >= 340
        assert local_admin_units_list["data"][0]["name"] == "Accons"


# -------------------------
#  Places controler methods
# -------------------------
@pytest.mark.order(index=122)
class TestPlaces:
    def test_places_controler(self):
        """Check controler name."""
        ctrl = PLACES_API.controler
        assert ctrl == "places"

    def test_places_get(self):
        """Get a single place."""
        p = "930144"
        logging.debug("Getting place %s", p)
        place = PLACES_API.api_get(p)
        assert PLACES_API.transfer_errors == 0
        assert place == {
            "data": [
                {
                    "altitude": "1106",
                    "coord_lat": "44.805686318298",
                    "coord_lon": "5.8792190569144",
                    "created_by": "30",
                    "created_date": {
                        "#text": "samedi, 24. juin 2017, 04:34:53",
                        "@ISO8601": "2017-06-24T04:34:53+02:00",
                        "@notime": "0",
                        "@offset": "7200",
                        "@timestamp": "1498271693",
                    },
                    "id": "930144",
                    "id_commune": "14966",
                    "id_region": "63",
                    "is_private": "0",
                    "last_updated_by": "30",
                    "last_updated_date": {
                        "#text": "mercredi, 27. juin 2018, 04:24:34",
                        "@ISO8601": "2018-06-27T04:24:34+02:00",
                        "@notime": "0",
                        "@offset": "7200",
                        "@timestamp": "1530066274",
                    },
                    "loc_precision": "750",
                    "name": "Rochachon",
                    "place_type": "place",
                    "visible": "1",
                    "wkt": "",
                }
            ]
        }
        p = "1300754"
        logging.debug("Getting place %s", p)
        place = PLACES_API.api_get(p)
        assert PLACES_API.transfer_errors == 0
        assert place == {
            "data": [
                {
                    "altitude": "342",
                    "coord_lat": "45.262426292659",
                    "coord_lon": "4.7715669855908",
                    "created_by": "30",
                    "created_date": {
                        "#text": "samedi, 24. juin 2017, 04:35:37",
                        "@ISO8601": "2017-06-24T04:35:37+02:00",
                        "@notime": "0",
                        "@offset": "7200",
                        "@timestamp": "1498271737",
                    },
                    "id": "1300754",
                    "id_commune": "2316",
                    "id_region": "10",
                    "is_private": "0",
                    "last_updated_by": "30",
                    "last_updated_date": {
                        "#text": "mercredi, 27. juin 2018, 04:24:34",
                        "@ISO8601": "2018-06-27T04:24:34+02:00",
                        "@notime": "0",
                        "@offset": "7200",
                        "@timestamp": "1530066274",
                    },
                    "loc_precision": "750",
                    "name": "Ruisseau de Lantizon",
                    "place_type": "place",
                    "visible": "1",
                    "wkt": "",
                }
            ]
        }

    @pytest.mark.slow
    def test_places_list_all(self):
        """Get list of all places."""
        places_list = PLACES_API.api_list()
        logging.debug("Received %d places", len(places_list["data"]))
        assert PLACES_API.transfer_errors == 0
        assert len(places_list["data"]) >= 1900000
        assert places_list["data"][1000]["name"] == "Passy-en-Valois - sans lieu-dit défini"

    def test_places_diff(self):
        """Get list of all places."""
        # places_list = PLACES_API.api_list(
        #     optional_headers={
        #         "If-Modified-Since": datetime(2019, 2, 1).strftime(
        #             "%a, %d %b %Y %H:%M:%S GMT"
        #         )
        #     }
        # )
        since = (datetime.now() - timedelta(days=1)).strftime("%H:%M:%S %d.%m.%Y")
        logging.debug(f"Getting updates since {since}")
        places_list = PLACES_API.api_diff(since)
        logging.debug("Received %d places", len(places_list))
        assert PLACES_API.transfer_errors == 0

    def test_places_list_1(self):
        """Get a list of places from a single local admin unit."""
        # Isère
        place = "14693"
        places_list = PLACES_API.api_list({"id_commune": place})
        logging.debug("local admin unit {} ==> {} place ".format(place, len(places_list["data"])))
        assert PLACES_API.transfer_errors == 0
        assert len(places_list["data"]) >= 164
        assert len(places_list["data"]) <= 200
        assert places_list["data"][0]["name"] == "Allevard - sans lieu-dit défini"
        # Ardèche
        place = "2096"
        places_list = PLACES_API.api_list({"id_commune": place})
        logging.debug("local admin unit {} ==> {} place ".format(place, len(places_list["data"])))
        assert PLACES_API.transfer_errors == 0
        assert len(places_list["data"]) >= 38
        assert len(places_list["data"]) <= 50
        assert places_list["data"][0]["name"] == "Accons - sans lieu-dit défini"


# ------------------------
# Fields controler methods
# ------------------------
@pytest.mark.order(index=130)
class TestFields:
    def test_fields_controler(self):
        """Check controler name."""
        ctrl = FIELDS_API.controler
        assert ctrl == "fields"

    def test_fields_get(self):
        """Get a field."""
        field = FIELDS_API.api_get("0")
        assert FIELDS_API.transfer_errors == 0
        assert field["data"] == []

    def test_fields_list(self):
        """Get list of fields."""
        fields = FIELDS_API.api_list()
        assert FIELDS_API.transfer_errors == 0
        assert len(fields["data"]) >= 8
        assert fields["data"][0]["id"] == "3"


# --------------------------
# Entities controler methods
# --------------------------
@pytest.mark.order(index=131)
class TestEntities:
    def test_entities_controler(self):
        """Check controler name."""
        ctrl = ENTITIES_API.controler
        assert ctrl == "entities"

    def test_entities_get(self):
        """Get an entity."""
        entity = ENTITIES_API.api_get("2")
        assert ENTITIES_API.transfer_errors == 0
        entity["data"][0]["short_name"] == "LPO ISERE"

    def test_entities_list(self):
        """Get list of entities."""
        entities = ENTITIES_API.api_list()
        assert ENTITIES_API.transfer_errors == 0
        assert len(entities["data"]) >= 8
        assert entities["data"][0]["short_name"] == "-"


# ----------------------------
#  Observers controler methods
# ----------------------------
@pytest.mark.order(index=132)
class TestObservers:
    def test_observers_controler(self):
        """Check controler name."""
        ctrl = OBSERVERS_API.controler
        assert ctrl == "observers"

    def test_observers_get(self):
        """Get a single observer."""
        o = "8583"
        logging.debug("Getting observer %s", o)
        observer = OBSERVERS_API.api_get(o)
        assert OBSERVERS_API.transfer_errors == 0
        assert "data" in observer
        assert observer["data"][0]["id_universal"] == "11675"
        assert observer["data"][0]["email"] == "d.thonon9@gmail.com"
        assert "anonymous" in observer["data"][0]
        assert "archive_account" in observer["data"][0]
        assert "atlas_list" in observer["data"][0]
        assert "birth_year" in observer["data"][0]
        assert "bypass_purchase" in observer["data"][0]
        assert "collectif" in observer["data"][0]
        assert "debug_file_upload" in observer["data"][0]
        assert "default_hidden" in observer["data"][0]
        assert "display_order" in observer["data"][0]
        assert "email" in observer["data"][0]
        assert "external_id" in observer["data"][0]
        assert "has_search_access" in observer["data"][0]
        assert "hide_email" in observer["data"][0]
        assert "id" in observer["data"][0]
        assert "id_entity" in observer["data"][0]
        assert "id_universal" in observer["data"][0]
        assert "item_per_page_gallery" in observer["data"][0]
        assert "item_per_page_obs" in observer["data"][0]
        assert "langu" in observer["data"][0]
        assert "last_inserted_data" in observer["data"][0]
        assert "last_login" in observer["data"][0]
        assert "lat" in observer["data"][0]
        assert "lon" in observer["data"][0]
        assert "mobile_phone" in observer["data"][0]
        assert "mobile_use_form" in observer["data"][0]
        assert "mobile_use_mortality" in observer["data"][0]
        assert "mobile_use_protocol" in observer["data"][0]
        assert "mobile_use_trace" in observer["data"][0]
        assert "name" in observer["data"][0]
        assert "number" in observer["data"][0]
        assert "photo" in observer["data"][0]
        assert "postcode" in observer["data"][0]
        assert "presentation" in observer["data"][0]
        assert "private_phone" in observer["data"][0]
        assert "private_website" in observer["data"][0]
        assert "registration_date" in observer["data"][0]
        assert "show_precise" in observer["data"][0]
        assert "species_order" in observer["data"][0]
        assert "street" in observer["data"][0]
        assert "surname" in observer["data"][0]
        assert "use_latin_search" in observer["data"][0]
        assert "work_phone" in observer["data"][0]

    @pytest.mark.slow
    def test_observers_list_all(self):
        """Get list of all observers."""
        observers_list = OBSERVERS_API.api_list()
        logging.debug("Received %d observers", len(observers_list["data"]))
        assert OBSERVERS_API.transfer_errors == 0
        assert len(observers_list["data"]) >= 190000
        assert observers_list["data"][0]["name"] == "Biolovision"

    # @pytest.mark.slow
    # def test_observers_list_diff(self):
    #     """Get list of all observers: skip as optional_headers not used by server"""
    #     observers_list = OBSERVERS_API.api_list(
    #         optional_headers={
    #             "If-Modified-Since": (datetime.today() - timedelta(days=30)).strftime(
    #                 "%a, %d %b %Y %H:%M:%S GMT"
    #             )
    #         }
    #     )
    #     logging.debug("Received %d observers", len(observers_list["data"]))
    #     assert OBSERVERS_API.transfer_errors == 0
    #     assert len(observers_list["data"]) >= 4500
    #     assert observers_list["data"][0]["name"] == "Biolovision"


# -----------------------------
# Validations controler methods
# -----------------------------
@pytest.mark.order(index=133)
class TestValidations:
    def test_validations_controler(self):
        """Check controler name."""
        ctrl = VALIDATIONS_API.controler
        assert ctrl == "validations"

    def test_validations_get(self):
        """Get a validation."""
        validation = VALIDATIONS_API.api_get("3")
        assert VALIDATIONS_API.transfer_errors == 0
        logging.debug("Validation 3:")
        logging.debug(validation)
        assert "data" in validation
        assert len(validation["data"]) == 1
        assert validation["data"][0]["id"] == "3"
        assert isinstance(validation["data"][0]["committee"], str)
        assert int(validation["data"][0]["date_start"]) >= 1
        assert int(validation["data"][0]["date_start"]) <= 366
        assert int(validation["data"][0]["date_stop"]) >= 1
        assert int(validation["data"][0]["date_stop"]) <= 366
        assert int(validation["data"][0]["id_species"]) >= 1

    def test_validations_list(self):
        """Get list of validations."""
        # Validations for the last days
        validations = VALIDATIONS_API.api_list()
        assert VALIDATIONS_API.transfer_errors == 0
        assert len(validations["data"]) >= 1
        logging.debug(f"Number of validations : {len(validations['data'])}")


# ------------------------------
# Observations controler methods
# ------------------------------
@pytest.mark.order(index=140)
class TestObservations:
    def test_observations_controler(self):
        """Check controler name."""
        ctrl = OBSERVATIONS_API.controler
        assert ctrl == "observations"

    def test_observations_diff(self):
        """Get list of diffs from last day."""
        since = (datetime.now() - timedelta(days=1)).strftime("%H:%M:%S %d.%m.%Y")
        logging.debug(f"Getting updates since {since}")
        diff = OBSERVATIONS_API.api_diff("1", since)
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(diff) > 0
        diff = OBSERVATIONS_API.api_diff("1", since, "only_modified")
        assert OBSERVATIONS_API.transfer_errors == 0
        diff = OBSERVATIONS_API.api_diff("1", since, "only_deleted")
        assert OBSERVATIONS_API.transfer_errors == 0

    def test_observations_list_1(self):
        """Get the list of sightings, from taxo_group 18: Mantodea."""
        list = OBSERVATIONS_API.api_list("18")
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(list) > 0

    @pytest.mark.slow
    def test_observations_list_2_1(self):
        """Get the list of sightings, from taxo_group 1, specie 218."""
        list = OBSERVATIONS_API.api_list("1", id_species="218", short_version="1")
        logging.debug(f"local test_observations_list_3_0 unit {len(list)} sightings/forms ")
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(list["data"]) > 1

    def test_observations_list_3_0(self):
        """Get the list of sightings, from taxo_group 1, specie 153."""
        list = OBSERVATIONS_API.api_list("1", id_species="153")
        logging.debug(f"local test_observations_list_3_0 unit {len(list)} sightings/forms ")
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(list["data"]) > 1

    def test_observations_list_3_1(self):
        """Get the list of sightings, from taxo_group 1, specie 153."""
        list = OBSERVATIONS_API.api_list("1", id_species="153", short_version="1")
        logging.debug(f"local test_observations_list_3_0 unit {len(list)} sightings/forms ")
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(list["data"]) > 1

    def test_observations_list_list(self):
        """Get the list of sightings, from taxo_group 1 523219."""
        list = OBSERVATIONS_API.api_list("1", id_sightings_list="523219,523550", short_version="1")
        logging.debug(json.dumps(list, sort_keys=True, indent=4))

    def test_observations_get(self):
        """Get a specific sighting."""
        sighting = OBSERVATIONS_API.api_get("71846872")
        assert sighting["data"]["sightings"][0]["place"]["county"] == "38"
        assert sighting["data"]["sightings"][0]["place"]["insee"] == "38185"
        assert sighting["data"]["sightings"][0]["place"]["municipality"] == "Grenoble"
        assert sighting["data"]["sightings"][0]["place"]["country"] == ""
        assert sighting["data"]["sightings"][0]["place"]["altitude"] == "215"
        assert sighting["data"]["sightings"][0]["place"]["coord_lat"] == "45.187677239404"
        assert sighting["data"]["sightings"][0]["place"]["coord_lon"] == "5.735372035327"
        assert sighting["data"]["sightings"][0]["place"]["name"] == "Museum (Parc du Museum)"
        assert sighting["data"]["sightings"][0]["place"]["@id"] == "927830"
        assert sighting["data"]["sightings"][0]["place"]["loc_precision"] == "750"
        assert sighting["data"]["sightings"][0]["place"]["place_type"] == "place"
        assert sighting["data"]["sightings"][0]["date"]["@notime"] == "1"
        assert sighting["data"]["sightings"][0]["date"]["@offset"] == "7200"
        assert sighting["data"]["sightings"][0]["date"]["@ISO8601"] == "2018-09-15T00:00:00+02:00"
        assert sighting["data"]["sightings"][0]["date"]["@timestamp"] == "1536962400"
        assert sighting["data"]["sightings"][0]["date"]["#text"] == "samedi, 15. septembre 2018"
        assert sighting["data"]["sightings"][0]["species"]["latin_name"] == "Anas platyrhynchos"
        assert sighting["data"]["sightings"][0]["species"]["rarity"] == "verycommon"
        assert sighting["data"]["sightings"][0]["species"]["sys_order"] == "262"
        assert sighting["data"]["sightings"][0]["species"]["name"] == "Canard colvert"
        assert sighting["data"]["sightings"][0]["species"]["@id"] == "86"
        assert sighting["data"]["sightings"][0]["species"]["taxonomy"] == "1"
        assert sighting["data"]["sightings"][0]["observers"][0]["estimation_code"] == "MINIMUM"
        assert sighting["data"]["sightings"][0]["observers"][0]["count"] == "15"
        assert sighting["data"]["sightings"][0]["observers"][0]["id_sighting"] == "71846872"
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["insert_date"]["#text"]
            == "samedi, 15. septembre 2018, 19:44:58"
        )
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["insert_date"]["@ISO8601"] == "2018-09-15T19:44:58+02:00"
        )
        assert sighting["data"]["sightings"][0]["observers"][0]["insert_date"]["@notime"] == "0"
        assert sighting["data"]["sightings"][0]["observers"][0]["insert_date"]["@offset"] == "7200"
        assert sighting["data"]["sightings"][0]["observers"][0]["insert_date"]["@timestamp"] == "1537033498"
        assert sighting["data"]["sightings"][0]["observers"][0]["atlas_grid_name"] == "E091N645"
        assert sighting["data"]["sightings"][0]["observers"][0]["name"] == "Daniel Thonon"
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["media_is_hidden"] == "0"
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["filename"]
            == "3_1537024802877-15194452-5272.jpg"
        )
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["path"]
            == "https://cdnmedia3.biolovision.net/data.biolovision.net/2018-09"
        )
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["insert_date"]["#text"]
            == "lundi, 12. décembre 2022, 00:24:50"
        )
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["insert_date"]["@ISO8601"]
            == "2022-12-12T00:24:50+01:00"
        )
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["insert_date"]["@notime"] == "0"
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["insert_date"]["@offset"] == "3600"
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["insert_date"]["@timestamp"] == "1670801090"
        )
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["metadata"] == ""
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["type"] == "PHOTO"
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["@id"] == "7537102"
        assert sighting["data"]["sightings"][0]["observers"][0]["@uid"] == "11675"
        assert sighting["data"]["sightings"][0]["observers"][0]["precision"] == "precise"
        assert sighting["data"]["sightings"][0]["observers"][0]["id_universal"] == "65_71846872"
        assert sighting["data"]["sightings"][0]["observers"][0]["traid"] == "8583"
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["timing"]["#text"]
            == "samedi, 15. septembre 2018, 17:19:00"
        )
        assert sighting["data"]["sightings"][0]["observers"][0]["timing"]["@ISO8601"] == "2018-09-15T17:19:00+02:00"
        assert sighting["data"]["sightings"][0]["observers"][0]["timing"]["@notime"] == "0"
        assert sighting["data"]["sightings"][0]["observers"][0]["timing"]["@offset"] == "7200"
        assert sighting["data"]["sightings"][0]["observers"][0]["timing"]["@timestamp"] == "1537024740"
        assert sighting["data"]["sightings"][0]["observers"][0]["altitude"] == "215"
        assert sighting["data"]["sightings"][0]["observers"][0]["source"] == "WEB"
        assert sighting["data"]["sightings"][0]["observers"][0]["coord_lat"] == "45.18724"
        assert sighting["data"]["sightings"][0]["observers"][0]["coord_lon"] == "5.735458"
        assert sighting["data"]["sightings"][0]["observers"][0]["flight_number"] == "1"
        assert sighting["data"]["sightings"][0]["observers"][0]["anonymous"] == "0"
        assert sighting["data"]["sightings"][0]["observers"][0]["@id"] == "8583"

    def test_observations_get_short(self):
        """Get a specific sighting."""
        sighting = OBSERVATIONS_API.api_get("71846872", short_version="1")
        assert sighting["data"]["sightings"][0]["place"]["@id"] == "927830"
        assert sighting["data"]["sightings"][0]["place"]["id_universal"] == "17_100197"
        assert sighting["data"]["sightings"][0]["place"]["lat"] == "45.187677239404"
        assert sighting["data"]["sightings"][0]["place"]["lon"] == "5.735372035327"
        assert sighting["data"]["sightings"][0]["place"]["loc_precision"] == "750"
        assert sighting["data"]["sightings"][0]["place"]["name"] == "Museum (Parc du Museum)"
        assert sighting["data"]["sightings"][0]["place"]["place_type"] == "place"
        assert sighting["data"]["sightings"][0]["date"]["@notime"] == "1"
        assert sighting["data"]["sightings"][0]["date"]["@offset"] == "7200"
        assert sighting["data"]["sightings"][0]["date"]["@timestamp"] == "1536962400"
        assert sighting["data"]["sightings"][0]["species"]["@id"] == "86"
        assert sighting["data"]["sightings"][0]["species"]["rarity"] == "verycommon"
        assert sighting["data"]["sightings"][0]["species"]["taxonomy"] == "1"
        assert sighting["data"]["sightings"][0]["observers"][0]["estimation_code"] == "MINIMUM"
        assert sighting["data"]["sightings"][0]["observers"][0]["count"] == "15"
        assert sighting["data"]["sightings"][0]["observers"][0]["id_sighting"] == "71846872"
        assert sighting["data"]["sightings"][0]["observers"][0]["id_universal"] == "65_71846872"
        assert sighting["data"]["sightings"][0]["observers"][0]["insert_date"] == "1537033498"
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["media_is_hidden"] == "0"
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["filename"]
            == "3_1537024802877-15194452-5272.jpg"
        )
        assert (
            sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["path"]
            == "https://cdnmedia3.biolovision.net/data.biolovision.net/2018-09"
        )
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["insert_date"] == "1670801090"
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["type"] == "PHOTO"
        assert sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["@id"] == "7537102"
        assert sighting["data"]["sightings"][0]["observers"][0]["@uid"] == "11675"
        assert sighting["data"]["sightings"][0]["observers"][0]["precision"] == "precise"
        assert sighting["data"]["sightings"][0]["observers"][0]["id_universal"] == "65_71846872"
        assert sighting["data"]["sightings"][0]["observers"][0]["traid"] == "8583"
        assert sighting["data"]["sightings"][0]["observers"][0]["timing"]["@notime"] == "0"
        assert sighting["data"]["sightings"][0]["observers"][0]["timing"]["@offset"] == "7200"
        assert sighting["data"]["sightings"][0]["observers"][0]["timing"]["@timestamp"] == "1537024740"
        assert sighting["data"]["sightings"][0]["observers"][0]["altitude"] == "215"
        assert sighting["data"]["sightings"][0]["observers"][0]["source"] == "WEB"
        assert sighting["data"]["sightings"][0]["observers"][0]["coord_lat"] == "45.18724"
        assert sighting["data"]["sightings"][0]["observers"][0]["coord_lon"] == "5.735458"
        assert sighting["data"]["sightings"][0]["observers"][0]["flight_number"] == "1"
        assert sighting["data"]["sightings"][0]["observers"][0]["@id"] == "8583"
        assert sighting["data"]["sightings"][0]["observers"][0]["version"] == "0"

    def test_observations_search_1(self):
        """Query sightings, from taxo_group 18: Mantodea and date range."""
        # Testing incorrect parameter
        q_param = None
        with pytest.raises(IncorrectParameter) as excinfo:  # noqa: F841
            list = OBSERVATIONS_API.api_search(q_param)
        # Testing real search
        q_param = {
            "period_choice": "range",
            "date_from": "01.09.2017",
            "date_to": "15.09.2017",
            "species_choice": "all",
            "taxonomic_group": "18",
        }
        list = OBSERVATIONS_API.api_search(q_param)
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(list["data"]["sightings"]) >= 500

    def test_observations_search_2(self):
        """Query sightings, from taxo_group 18: Mantodea and date range."""
        q_param = {
            "period_choice": "range",
            "date_from": "01.09.2017",
            "date_to": "30.09.2017",
            "species_choice": "all",
            "taxonomic_group": "18",
        }
        list = OBSERVATIONS_API.api_search(q_param, short_version="1")
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(list["data"]["sightings"]) >= 500

    def test_observations_update(self):
        """Update a specific sighting."""
        obs = "138181516"
        sighting = OBSERVATIONS_API.api_get(obs, short_version="1")
        assert OBSERVATIONS_API.transfer_errors == 0
        assert sighting["data"]["sightings"][0]["observers"][0]["id_sighting"] == obs
        assert sighting["data"]["sightings"][0]["observers"][0]["id_universal"] == "65_138181516"
        # Update
        sighting["data"]["sightings"][0]["observers"][0]["hidden_comment"] = "API update test"
        OBSERVATIONS_API.api_update(obs, sighting)
        assert OBSERVATIONS_API.transfer_errors == 0
        # Check
        sighting = OBSERVATIONS_API.api_get(obs, short_version="1")
        assert OBSERVATIONS_API.transfer_errors == 0
        assert sighting["data"]["sightings"][0]["observers"][0]["id_sighting"] == obs
        assert sighting["data"]["sightings"][0]["observers"][0]["id_universal"] == "65_138181516"
        assert int(sighting["data"]["sightings"][0]["observers"][0]["update_date"]) > time.time() - 60

    # @pytest.mark.skipif(SITE == "t07", reason="SITE t07 not supported")
    # def test_observations_crud_s(self):
    #     """Create, read, update, delete a standalone sighting."""
    #     data = {
    #         "data": {
    #             "sightings": [
    #                 {
    #                     "date": {"@timestamp": "1616753200"},  # 26/03/2021 - 11:06:40
    #                     "species": {"@id": "408"},  # Merle noir
    #                     "observers": [
    #                         {
    #                             "@id": "38",
    #                             "altitude": "230",
    #                             "comment": "TEST API !!! à supprimer !!!",
    #                             "coord_lat": "45.188302192726",
    #                             "coord_lon": "5.7364289068356",
    #                             "precision": "precise",
    #                             "count": "1",
    #                             "estimation_code": "MINIMUM",
    #                         }
    #                     ],
    #                 }
    #             ]
    #         }
    #     }
    #     # First creation should succeed
    #     sighting = OBSERVATIONS_API.api_create(data)
    #     logging.debug(sighting)
    #     assert sighting["status"] == "saved"
    #     obs_1 = sighting["id"][0]
    #     assert isinstance(obs_1, int)
    #     obs_1 = str(obs_1)

    #     # Second creation should fail
    #     with pytest.raises(HTTPError):
    #         sighting = OBSERVATIONS_API.api_create(data)
    #         logging.debug(sighting)

    #     # Read created observation
    #     sighting = OBSERVATIONS_API.api_get(obs_1, short_version="1")
    #     assert sighting["data"]["sightings"][0]["observers"][0]["id_sighting"] == obs_1
    #     assert (
    #         sighting["data"]["sightings"][0]["observers"][0]["comment"]
    #         == "TEST API !!! à supprimer !!!"
    #     )

    #     # Update
    #     sighting["data"]["sightings"][0]["observers"][0][
    #         "hidden_comment"
    #     ] = "API update test"
    #     OBSERVATIONS_API.api_update(obs_1, sighting)
    #     # Check
    #     sighting = OBSERVATIONS_API.api_get(obs_1, short_version="1")
    #     assert (
    #         sighting["data"]["sightings"][0]["observers"][0]["hidden_comment"]
    #         == "API update test"
    #     )

    #     # Delete test observation and form
    #     logging.debug(sighting)
    #     id_form_universal = sighting["data"]["sightings"][0]["observers"][0][
    #         "id_form_universal"
    #     ]
    #     res = OBSERVATIONS_API.api_delete(obs_1)
    #     logging.debug(res)
    #     res = OBSERVATIONS_API.api_delete_list(id=id_form_universal)
    #     logging.debug(res)

    def test_observations_crud_f(self):
        """Create, read, update, delete a forms sighting."""
        data = {
            "data": {
                "forms": [
                    {
                        "time_start": "06:45:00",
                        "time_stop": "07:00:00",
                        "full_form": "1",
                        "sightings": [
                            {
                                "date": {"@timestamp": str(int(time.time()))},
                                "species": {"@id": "408"},
                                "place": {
                                    "@id": "917071",
                                },
                                "observers": [
                                    {
                                        "@id": "11675",
                                        "timing": {
                                            "@timestamp": "1616753200",
                                            "@notime": "0",
                                        },
                                        "altitude": "230",
                                        "comment": "TEST API !!! à supprimer !!!",
                                        "coord_lat": "45.18724",
                                        "coord_lon": "5.735458",
                                        "precision": "precise",
                                        "count": "1",
                                        "estimation_code": "MINIMUM",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        }
        # First creation should succeed
        sighting = OBSERVATIONS_API.api_create(data)
        logging.debug(sighting)
        assert sighting["status"] == "saved"
        obs_1 = sighting["id"][0]
        assert isinstance(obs_1, int)
        obs_1 = str(obs_1)

        # Second creation should fail
        with pytest.raises(HTTPError):
            sighting = OBSERVATIONS_API.api_create(data)

        # Read created observation
        sighting = OBSERVATIONS_API.api_get(obs_1, short_version="1")
        assert sighting["data"]["forms"][0]["sightings"][0]["observers"][0]["id_sighting"] == obs_1
        assert sighting["data"]["forms"][0]["sightings"][0]["observers"][0]["comment"] == "TEST API !!! à supprimer !!!"

        # Update
        sighting["data"] = sighting["data"]["forms"][0]
        logging.debug(sighting)
        sighting["data"]["sightings"][0]["observers"][0]["hidden_comment"] = "API update test"
        OBSERVATIONS_API.api_update(obs_1, sighting)
        # Check
        sighting = OBSERVATIONS_API.api_get(obs_1, short_version="1")
        assert sighting["data"]["forms"][0]["sightings"][0]["observers"][0]["hidden_comment"] == "API update test"

        # Delete test observation
        id_form_universal = sighting["data"]["forms"][0]["sightings"][0]["observers"][0]["id_form_universal"]
        res = OBSERVATIONS_API.api_delete(obs_1)
        logging.debug(res)
        res = OBSERVATIONS_API.api_delete_list(data={"id_form_universal": id_form_universal})
        logging.debug(res)
