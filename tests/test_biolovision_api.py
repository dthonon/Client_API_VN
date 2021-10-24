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

# Using faune-ardeche or faune-isere site, that needs to be created first
# SITE = "ff"
# SITE = "t07"
SITE = "t38"
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
        with pytest.raises(HTTPError) as excinfo:  # noqa: F841
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
            optional_headers={
                "If-Modified-Since": datetime(2019, 2, 1).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            },
            # optional_headers={"If-Modified-Since": "Sun, 01 Sep 2019 00:00:00 GMT"},
        )
        logging.debug("Taxo_group 30 ==> {} species".format(len(species_list["data"])))
        assert SPECIES_API.transfer_errors == 0

    def test_species_list_error(self):
        """Get a list of species from taxo_group 1, limited to 1 chunk."""
        with pytest.raises(MaxChunksError) as excinfo:  # noqa: F841
            species_list = SPECIES_API_ERR.api_list(  # noqa: F841
                {"id_taxo_group": "1"}  # noqa: F841
            )  # noqa: F841


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
        """Get a territorial_units."""
        if SITE == "t38":
            territorial_unit = TERRITORIAL_UNITS_API.api_get("39")
        elif SITE == "t07":
            territorial_unit = TERRITORIAL_UNITS_API.api_get("07")
        assert TERRITORIAL_UNITS_API.transfer_errors == 0
        if SITE == "t38":
            assert territorial_unit["data"][0]["name"] == "Isère"
        elif SITE == "t07":
            assert territorial_unit["data"][0]["name"] == "Ardèche"

    def test_territorial_units_list(self):
        """Get list of territorial_units."""
        # First call, should return from API call if not called before
        start = time.perf_counter()
        territorial_units = TERRITORIAL_UNITS_API.api_list()
        took = (time.perf_counter() - start) * 1000.0
        logging.debug("territorial_units_list, call 1 took: " + str(took) + " ms")
        assert TERRITORIAL_UNITS_API.transfer_errors == 0
        assert len(territorial_units["data"]) == 1
        logging.debug(territorial_units["data"])
        if SITE == "t38":
            assert territorial_units["data"][0]["name"] == "Isère"
        elif SITE == "t07":
            assert territorial_units["data"][0]["name"] == "Ardèche"
        start = time.perf_counter()
        territorial_units = TERRITORIAL_UNITS_API.api_list()
        took = (time.perf_counter() - start) * 1000.0
        logging.debug("territorial_units_list, call 2 took: " + str(took) + " ms")
        assert TERRITORIAL_UNITS_API.transfer_errors == 0


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
        if SITE == "t38":
            a = "14693"
        elif SITE == "t07":
            a = "2096"
        else:
            assert False
        logging.debug("Getting local admin unit %s", a)
        local_admin_unit = LOCAL_ADMIN_UNITS_API.api_get(a)
        assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
        if SITE == "t38":
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
        elif SITE == "t07":
            assert local_admin_unit == {
                "data": [
                    {
                        "coord_lat": "44.888464632099",
                        "coord_lon": "4.39188200157809",
                        "id": "2096",
                        "id_canton": "7",
                        "insee": "07001",
                        "name": "Accons",
                    }
                ]
            }

    def test_local_admin_units_list_all(self):
        """Get list of all local admin units."""
        logging.debug("Getting all local admin unit")
        local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list()
        logging.debug(
            "Received %d local admin units", len(local_admin_units_list["data"])
        )
        assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
        if SITE == "t38":
            assert len(local_admin_units_list["data"]) >= 534
        elif SITE == "t07":
            assert len(local_admin_units_list["data"]) >= 340

    def test_local_admin_units_list_1(self):
        """Get a list of local_admin_units from territorial unit 39 (Isère)."""
        if SITE == "t38":
            logging.debug("Getting local admin unit from {id_canton: 39}")
            local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list(
                opt_params={"id_canton": "39"}
            )
        elif SITE == "t07":
            logging.debug("Getting local admin unit from {id_canton: 07}")
            local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list(
                opt_params={"id_canton": "07"}
            )
        logging.debug(
            "territorial unit ==> {} local admin unit ".format(
                len(local_admin_units_list["data"])
            )
        )
        assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
        if SITE == "t38":
            assert len(local_admin_units_list["data"]) >= 534
            assert local_admin_units_list["data"][0]["name"] == "Abrets (Les)"
        elif SITE == "t07":
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
        if SITE == "t38":
            p = "14693"
        elif SITE == "t07":
            p = "100694"
        else:
            assert False
        logging.debug("Getting place %s", p)
        place = PLACES_API.api_get(p)
        assert PLACES_API.transfer_errors == 0
        if SITE == "t38":
            assert place == {
                "data": [
                    {
                        "altitude": "1106",
                        "coord_lat": "44.805686318298",
                        "coord_lon": "5.8792190569144",
                        "created_by": "30",
                        "created_date": {
                            "#text": "vendredi 27 novembre 2009, 19:06:29",
                            "@ISO8601": "2009-11-27T19:06:29+01:00",
                            "@notime": "0",
                            "@offset": "3600",
                            "@timestamp": "1259345189",
                        },
                        "id": "14693",
                        "id_commune": "14966",
                        "id_region": "63",
                        "is_private": "0",
                        "last_updated_by": "30",
                        "last_updated_date": {
                            "#text": "mercredi 27 juin 2018, 04:30:24",
                            "@ISO8601": "2018-06-27T04:30:24+02:00",
                            "@notime": "0",
                            "@offset": "7200",
                            "@timestamp": "1530066624",
                        },
                        "loc_precision": "750",
                        "name": "Rochachon",
                        "place_type": "place",
                        "visible": "1",
                    }
                ]
            }
        elif SITE == "t07":
            assert place == {
                "data": [
                    {
                        "altitude": "285",
                        "coord_lat": "45.2594824523633",
                        "coord_lon": "4.7766923904419",
                        "id": "100694",
                        "id_commune": "2316",
                        "id_region": "16",
                        "is_private": "0",
                        "loc_precision": "750",
                        "name": "Ruisseau de Lantizon (ravin)",
                        "place_type": "place",
                        "visible": "1",
                    }
                ]
            }

    @pytest.mark.slow
    def test_places_list_all(self):
        """Get list of all places."""
        places_list = PLACES_API.api_list()
        logging.debug("Received %d places", len(places_list["data"]))
        assert PLACES_API.transfer_errors == 0
        if SITE == "t38":
            assert len(places_list["data"]) >= 31930
            assert places_list["data"][0]["name"] == "ESRF-synchrotron"
        elif SITE == "t07":
            assert len(places_list["data"]) >= 23566
            assert places_list["data"][0]["name"] == "Accons - sans lieu-dit défini"

    def test_places_list_diff(self):
        """Get list of all places."""
        places_list = PLACES_API.api_list(
            optional_headers={
                "If-Modified-Since": datetime(2019, 2, 1).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            }
        )
        logging.debug("Received %d places", len(places_list["data"]))
        assert PLACES_API.transfer_errors == 0

    def test_places_list_1(self):
        """Get a list of places from a single local admin unit."""
        if SITE == "t38":
            place = "14693"
        elif SITE == "t07":
            place = "2096"
        else:
            assert False
        places_list = PLACES_API.api_list({"id_commune": place})
        logging.debug(
            "local admin unit {} ==> {} place ".format(place, len(places_list["data"]))
        )
        assert PLACES_API.transfer_errors == 0
        if SITE == "t38":
            assert len(places_list["data"]) >= 164
            assert len(places_list["data"]) <= 200
            assert places_list["data"][0]["name"] == "le Repos (S)"
        elif SITE == "t07":
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
        if SITE == "t38":
            entity["data"][0]["short_name"] == "LPO ISERE"
        elif SITE == "t07":
            entity["data"][0]["short_name"] == "LPO 07"
        else:
            assert False

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
        if SITE == "t38":
            o = "33"
        elif SITE == "t07":
            o = "1084"
        else:
            assert False
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
        assert "municipality" in observer["data"][0]
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
        if SITE == "t38":
            assert len(observers_list["data"]) >= 4500
            assert observers_list["data"][0]["name"] == "Biolovision"
        elif SITE == "t07":
            assert len(observers_list["data"]) >= 2500
            assert observers_list["data"][0]["name"] == "Biolovision"

    def test_observers_list_diff(self):
        """Get list of all observers."""
        observers_list = OBSERVERS_API.api_list(
            optional_headers={
                "If-Modified-Since": datetime(2019, 2, 1).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            }
        )
        logging.debug("Received %d observers", len(observers_list["data"]))
        assert OBSERVERS_API.transfer_errors == 0
        if SITE == "t38":
            assert len(observers_list["data"]) >= 4500
            assert observers_list["data"][0]["name"] == "Biolovision"
        elif SITE == "t07":
            assert len(observers_list["data"]) >= 2500
            assert observers_list["data"][0]["name"] == "Biolovision"


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
        validation = VALIDATIONS_API.api_get("2")
        assert VALIDATIONS_API.transfer_errors == 0
        logging.debug("Validation 2:")
        logging.debug(validation)
        assert "data" in validation
        assert len(validation["data"]) == 1
        assert validation["data"][0]["id"] == "2"
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
        logging.debug("Getting updates since {}".format(since))
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
        logging.debug(
            "local test_observations_list_3_0 unit {} sightings/forms ".format(
                len(list)
            )
        )
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(list["data"]) > 1

    def test_observations_list_3_0(self):
        """Get the list of sightings, from taxo_group 1, specie 153."""
        list = OBSERVATIONS_API.api_list("1", id_species="153")
        logging.debug(
            "local test_observations_list_3_0 unit {} sightings/forms ".format(
                len(list)
            )
        )
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(list["data"]) > 1

    def test_observations_list_3_1(self):
        """Get the list of sightings, from taxo_group 1, specie 153."""
        list = OBSERVATIONS_API.api_list("1", id_species="153", short_version="1")
        logging.debug(
            "local test_observations_list_3_0 unit {} sightings/forms ".format(
                len(list)
            )
        )
        assert OBSERVATIONS_API.transfer_errors == 0
        assert len(list["data"]) > 1

    def test_observations_list_list(self):
        """Get the list of sightings, from taxo_group 1 523219."""
        list = OBSERVATIONS_API.api_list(
            "1", id_sightings_list="523219,523550", short_version="1"
        )
        logging.debug(json.dumps(list, sort_keys=True, indent=4))

    def test_observations_get(self):
        """Get a specific sighting."""
        if SITE == "t38":
            sighting = OBSERVATIONS_API.api_get("2246086")
            assert sighting["data"]["sightings"][0]["place"]["county"] == "38"
            assert sighting["data"]["sightings"][0]["place"]["insee"] == "38185"
            assert (
                sighting["data"]["sightings"][0]["place"]["municipality"] == "Grenoble"
            )
            assert sighting["data"]["sightings"][0]["place"]["country"] == ""
            assert sighting["data"]["sightings"][0]["place"]["altitude"] == "215"
            assert (
                sighting["data"]["sightings"][0]["place"]["coord_lat"]
                == "45.187677239404"
            )
            assert (
                sighting["data"]["sightings"][0]["place"]["coord_lon"]
                == "5.735372035327"
            )
            assert (
                sighting["data"]["sightings"][0]["place"]["name"]
                == "Museum (Parc du Museum)"
            )
            assert sighting["data"]["sightings"][0]["place"]["@id"] == "100197"
            assert sighting["data"]["sightings"][0]["place"]["loc_precision"] == "0"
            assert sighting["data"]["sightings"][0]["place"]["place_type"] == "place"
            assert sighting["data"]["sightings"][0]["date"]["@notime"] == "1"
            assert sighting["data"]["sightings"][0]["date"]["@offset"] == "7200"
            assert (
                sighting["data"]["sightings"][0]["date"]["@ISO8601"]
                == "2018-09-15T00:00:00+02:00"
            )
            assert (
                sighting["data"]["sightings"][0]["date"]["@timestamp"] == "1536962400"
            )
            assert (
                sighting["data"]["sightings"][0]["date"]["#text"]
                == "samedi 15 septembre 2018"
            )
            assert (
                sighting["data"]["sightings"][0]["species"]["latin_name"]
                == "Anas platyrhynchos"
            )
            assert sighting["data"]["sightings"][0]["species"]["rarity"] == "verycommon"
            assert sighting["data"]["sightings"][0]["species"]["sys_order"] == "262"
            assert (
                sighting["data"]["sightings"][0]["species"]["name"] == "Canard colvert"
            )
            assert sighting["data"]["sightings"][0]["species"]["@id"] == "86"
            assert sighting["data"]["sightings"][0]["species"]["taxonomy"] == "1"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["estimation_code"]
                == "MINIMUM"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["count"] == "15"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["id_sighting"]
                == "2246086"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["insert_date"]["#text"]
                == "samedi 15 septembre 2018, 19:45:01"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["insert_date"][
                    "@ISO8601"
                ]
                == "2018-09-15T19:45:01+02:00"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["insert_date"][
                    "@notime"
                ]
                == "0"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["insert_date"][
                    "@offset"
                ]
                == "7200"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["insert_date"][
                    "@timestamp"
                ]
                == "1537033501"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["atlas_grid_name"]
                == "E091N645"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["name"]
                == "Daniel Thonon"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "media_is_hidden"
                ]
                == "0"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "filename"
                ]
                == "3_1537024802877-15194452-5272.jpg"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["path"]
                == "https://cdnmedia3.biolovision.net/data.biolovision.net/2018-09"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "insert_date"
                ]["#text"]
                # == "jeudi 1 janvier 1970, 01:33:38"
                == "samedi 15 septembre 2018, 19:45:01"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "insert_date"
                ]["@ISO8601"]
                # == "1970-01-01T01:33:38+01:00"
                == "2018-09-15T19:45:01+02:00"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "insert_date"
                ]["@notime"]
                == "0"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "insert_date"
                ]["@offset"]
                # == "3600"
                == "7200"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "insert_date"
                ]["@timestamp"]
                # == "2018"
                == "1537033501"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "metadata"
                ]
                == ""
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["type"]
                == "PHOTO"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["@id"]
                == "49174"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["@uid"] == "11675"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["precision"]
                == "precise"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["id_universal"]
                == "65_71846872"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["traid"] == "33"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["#text"]
                == "samedi 15 septembre 2018, 17:19:00"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@ISO8601"]
                == "2018-09-15T17:19:00+02:00"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@notime"]
                == "0"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@offset"]
                == "7200"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@timestamp"]
                == "1537024740"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["altitude"] == "215"
            assert sighting["data"]["sightings"][0]["observers"][0]["source"] == "WEB"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["coord_lat"]
                == "45.18724"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["coord_lon"]
                == "5.735458"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["flight_number"] == "1"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["anonymous"] == "0"
            assert sighting["data"]["sightings"][0]["observers"][0]["@id"] == "33"
        if SITE == "t07":
            sighting = OBSERVATIONS_API.api_get("274830")
            assert sighting == {
                "data": {
                    "sightings": [
                        {
                            "date": {
                                "#text": "mercredi 29 avril 2015",
                                "@ISO8601": "2015-04-29T00:00:00+02:00",
                                "@notime": "1",
                                "@offset": "7200",
                                "@timestamp": "1430258400",
                            },
                            "observers": [
                                {
                                    "@id": "104",
                                    "@uid": "4040",
                                    "altitude": "99",
                                    "anonymous": "0",
                                    "atlas_grid_name": "E081N636",
                                    "comment": "juv",
                                    "coord_lat": "44.373198",
                                    "coord_lon": "4.428607",
                                    "count": "1",
                                    "estimation_code": "MINIMUM",
                                    "flight_number": "1",
                                    "hidden_comment": "RNNGA",
                                    "id_sighting": "274830",
                                    "id_universal": "30_274830",
                                    "insert_date": {
                                        "#text": "dimanche 1 novembre 2015, 22:30:37",
                                        "@ISO8601": "2015-11-01T22:30:37+01:00",
                                        "@notime": "0",
                                        "@offset": "3600",
                                        "@timestamp": "1446413437",
                                    },
                                    "name": "Nicolas Bazin",
                                    "precision": "precise",
                                    "source": "WEB",
                                    "timing": {
                                        "#text": "mercredi 29 avril 2015",
                                        "@ISO8601": "2015-04-29T00:00:00+02:00",
                                        "@notime": "1",
                                        "@offset": "7200",
                                        "@timestamp": "1430258400",
                                    },
                                    "traid": "104",
                                    "update_date": {
                                        "#text": "lundi 26 mars 2018, 18:01:23",
                                        "@ISO8601": "2018-03-26T18:01:23+02:00",
                                        "@notime": "0",
                                        "@offset": "7200",
                                        "@timestamp": "1522080083",
                                    },
                                }
                            ],
                            "place": {
                                "@id": "122870",
                                "altitude": "99",
                                "coord_lat": "44.371928319497",
                                "coord_lon": "4.4273367833997",
                                "country": "",
                                "county": "07",
                                "insee": "07330",
                                "loc_precision": "0",
                                "municipality": "Vallon-Pont-d'Arc",
                                "name": "Rapide des Trois Eaux",
                                "place_type": "place",
                            },
                            "species": {
                                "@id": "19703",
                                "latin_name": "Empusa pennata",
                                "name": "Empuse penn\u00e9e",
                                "rarity": "unusual",
                                "sys_order": "80",
                                "taxonomy": "18",
                            },
                        }
                    ]
                }
            }

    def test_observations_get_short(self):
        """Get a specific sighting."""
        if SITE == "t38":
            sighting = OBSERVATIONS_API.api_get("2246086", short_version="1")
            assert sighting["data"]["sightings"][0]["place"]["@id"] == "100197"
            assert (
                sighting["data"]["sightings"][0]["place"]["id_universal"] == "17_100197"
            )
            assert sighting["data"]["sightings"][0]["place"]["lat"] == "45.187677239404"
            assert sighting["data"]["sightings"][0]["place"]["lon"] == "5.735372035327"
            assert sighting["data"]["sightings"][0]["place"]["loc_precision"] == "0"
            assert (
                sighting["data"]["sightings"][0]["place"]["name"]
                == "Museum (Parc du Museum)"
            )
            assert sighting["data"]["sightings"][0]["place"]["place_type"] == "place"
            assert sighting["data"]["sightings"][0]["date"]["@notime"] == "1"
            assert sighting["data"]["sightings"][0]["date"]["@offset"] == "7200"
            assert (
                sighting["data"]["sightings"][0]["date"]["@timestamp"] == "1536962400"
            )
            assert sighting["data"]["sightings"][0]["species"]["@id"] == "86"
            assert sighting["data"]["sightings"][0]["species"]["rarity"] == "verycommon"
            assert sighting["data"]["sightings"][0]["species"]["taxonomy"] == "1"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["estimation_code"]
                == "MINIMUM"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["count"] == "15"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["id_sighting"]
                == "2246086"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["id_universal"]
                == "65_71846872"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["insert_date"]
                == "1537033501"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "media_is_hidden"
                ]
                == "0"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "filename"
                ]
                == "3_1537024802877-15194452-5272.jpg"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["path"]
                == "https://cdnmedia3.biolovision.net/data.biolovision.net/2018-09"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "insert_date"
                ]
                == "1537033501"
                # == "2018-09-15 19:45:01"
                # == "samedi 15 septembre 2018, 19:45:01"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["type"]
                == "PHOTO"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["@id"]
                == "49174"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["@uid"] == "11675"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["precision"]
                == "precise"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["id_universal"]
                == "65_71846872"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["traid"] == "33"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@notime"]
                == "0"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@offset"]
                == "7200"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@timestamp"]
                == "1537024740"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["altitude"] == "215"
            assert sighting["data"]["sightings"][0]["observers"][0]["source"] == "WEB"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["coord_lat"]
                == "45.18724"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["coord_lon"]
                == "5.735458"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["flight_number"] == "1"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["@id"] == "33"
            assert sighting["data"]["sightings"][0]["observers"][0]["version"] == "0"
        if SITE == "t07":
            sighting = OBSERVATIONS_API.api_get("274830", short_version="1")
            assert sighting == {
                "data": {
                    "sightings": [
                        {
                            "date": {
                                "@notime": "1",
                                "@offset": "7200",
                                "@timestamp": "1430258400",
                            },
                            "observers": [
                                {
                                    "@id": "104",
                                    "@uid": "4040",
                                    "altitude": "99",
                                    "comment": "juv",
                                    "coord_lat": "44.373198",
                                    "coord_lon": "4.428607",
                                    "count": "1",
                                    "estimation_code": "MINIMUM",
                                    "flight_number": "1",
                                    "hidden_comment": "RNNGA",
                                    "id_sighting": "274830",
                                    "id_universal": "30_274830",
                                    "insert_date": "1446413437",
                                    "precision": "precise",
                                    "source": "WEB",
                                    "timing": {
                                        "@notime": "1",
                                        "@offset": "7200",
                                        "@timestamp": "1430258400",
                                    },
                                    "traid": "104",
                                    "update_date": "1522080083",
                                    "version": "0",
                                }
                            ],
                            "place": {
                                "@id": "122870",
                                "id_universal": "30_274830",
                                "lat": "44.371928319497",
                                "lon": "4.4273367833997",
                                "loc_precision": "0",
                                "name": "Rapide des Trois Eaux",
                                "place_type": "place",
                            },
                            "species": {
                                "@id": "19703",
                                "rarity": "unusual",
                                "taxonomy": "18",
                            },
                        }
                    ]
                }
            }

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
            "date_to": "30.09.2017",
            "species_choice": "all",
            "taxonomic_group": "18",
        }
        list = OBSERVATIONS_API.api_search(q_param)
        assert OBSERVATIONS_API.transfer_errors == 0
        if SITE == "t38":
            assert len(list["data"]["sightings"]) >= 17
        elif SITE == "t07":
            assert len(list["data"]["sightings"]) >= 3
        else:
            assert False

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
        if SITE == "t38":
            assert len(list["data"]["sightings"]) >= 17
        elif SITE == "t07":
            assert len(list["data"]["sightings"]) >= 3
        else:
            assert False

    def test_observations_update(self):
        """Update a specific sighting."""
        if SITE == "t38":
            sighting = OBSERVATIONS_API.api_get("2246086", short_version="1")
            assert sighting["data"]["sightings"][0]["place"]["@id"] == "100197"
            assert (
                sighting["data"]["sightings"][0]["place"]["id_universal"] == "17_100197"
            )
            assert sighting["data"]["sightings"][0]["place"]["lat"] == "45.187677239404"
            assert sighting["data"]["sightings"][0]["place"]["lon"] == "5.735372035327"
            assert sighting["data"]["sightings"][0]["place"]["loc_precision"] == "0"
            assert (
                sighting["data"]["sightings"][0]["place"]["name"]
                == "Museum (Parc du Museum)"
            )
            assert sighting["data"]["sightings"][0]["place"]["place_type"] == "place"
            assert sighting["data"]["sightings"][0]["date"]["@notime"] == "1"
            assert sighting["data"]["sightings"][0]["date"]["@offset"] == "7200"
            assert (
                sighting["data"]["sightings"][0]["date"]["@timestamp"] == "1536962400"
            )
            assert sighting["data"]["sightings"][0]["species"]["@id"] == "86"
            assert sighting["data"]["sightings"][0]["species"]["rarity"] == "verycommon"
            assert sighting["data"]["sightings"][0]["species"]["taxonomy"] == "1"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["estimation_code"]
                == "MINIMUM"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["count"] == "15"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["id_sighting"]
                == "2246086"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["id_universal"]
                == "65_71846872"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["insert_date"]
                == "1537033501"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "media_is_hidden"
                ]
                == "0"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "filename"
                ]
                == "3_1537024802877-15194452-5272.jpg"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["path"]
                == "https://cdnmedia3.biolovision.net/data.biolovision.net/2018-09"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0][
                    "insert_date"
                ]
                == "1537033501"
                # == "2018-09-15 19:45:01"
                # == "samedi 15 septembre 2018, 19:45:01"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["type"]
                == "PHOTO"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["medias"][0]["@id"]
                == "49174"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["@uid"] == "11675"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["precision"]
                == "precise"
            )
            assert (
                int(sighting["data"]["sightings"][0]["observers"][0]["update_date"])
                > 1570489429
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["id_universal"]
                == "65_71846872"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["traid"] == "33"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@notime"]
                == "0"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@offset"]
                == "7200"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["timing"]["@timestamp"]
                == "1537024740"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["altitude"] == "215"
            assert sighting["data"]["sightings"][0]["observers"][0]["source"] == "WEB"
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["coord_lat"]
                == "45.18724"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["coord_lon"]
                == "5.735458"
            )
            assert (
                sighting["data"]["sightings"][0]["observers"][0]["flight_number"] == "1"
            )
            assert sighting["data"]["sightings"][0]["observers"][0]["@id"] == "33"
            assert sighting["data"]["sightings"][0]["observers"][0]["version"] == "0"
            # Update
            sighting["data"]["sightings"][0]["observers"][0][
                "hidden_comment"
            ] = "API update test"
            OBSERVATIONS_API.api_update("274830", sighting)
            # Check
            sighting = OBSERVATIONS_API.api_get("2246086", short_version="1")
            assert sighting["data"]["sightings"][0]["place"]["@id"] == "100197"
            assert (
                int(sighting["data"]["sightings"][0]["observers"][0]["update_date"])
                > 1570489429
            )
        if SITE == "t07":
            sighting = OBSERVATIONS_API.api_get("274830", short_version="1")
            assert sighting == {
                "data": {
                    "sightings": [
                        {
                            "date": {
                                "@notime": "1",
                                "@offset": "7200",
                                "@timestamp": "1430258400",
                            },
                            "observers": [
                                {
                                    "@id": "104",
                                    "@uid": "4040",
                                    "altitude": "99",
                                    "comment": "juv",
                                    "coord_lat": "44.373198",
                                    "coord_lon": "4.428607",
                                    "count": "1",
                                    "estimation_code": "MINIMUM",
                                    "flight_number": "1",
                                    "hidden_comment": "RNNGA",
                                    "id_sighting": "274830",
                                    "id_universal": "30_274830",
                                    "insert_date": "1446413437",
                                    "precision": "precise",
                                    "source": "WEB",
                                    "timing": {
                                        "@notime": "1",
                                        "@offset": "7200",
                                        "@timestamp": "1430258400",
                                    },
                                    "traid": "104",
                                    "update_date": "1522080083",
                                    "version": "0",
                                }
                            ],
                            "place": {
                                "@id": "122870",
                                "id_universal": "30_274830",
                                "lat": "44.371928319497",
                                "lon": "4.4273367833997",
                                "loc_precision": "0",
                                "name": "Rapide des Trois Eaux",
                                "place_type": "place",
                            },
                            "species": {
                                "@id": "19703",
                                "rarity": "unusual",
                                "taxonomy": "18",
                            },
                        }
                    ]
                }
            }

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

    @pytest.mark.skipif(SITE == "t07", reason="SITE t07 not supported")
    def test_observations_crud_f(self):
        """Create, read, update, delete a forms sighting."""
        data = {
            "data": {
                "forms": [
                    {
                        "time_start": "06:00:00",
                        "time_stop": "16:00:00",
                        "full_form": "1",
                        "sightings": [
                            {
                                "date": {"@timestamp": "1616753200"},
                                "species": {"@id": "408"},
                                "place": {
                                    "@id": "102004",
                                },
                                "observers": [
                                    {
                                        "@id": "38",
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
        assert (
            sighting["data"]["forms"][0]["sightings"][0]["observers"][0]["id_sighting"]
            == obs_1
        )
        assert (
            sighting["data"]["forms"][0]["sightings"][0]["observers"][0]["comment"]
            == "TEST API !!! à supprimer !!!"
        )

        # Update
        sighting["data"] = sighting["data"]["forms"][0]
        logging.debug(sighting)
        sighting["data"]["sightings"][0]["observers"][0][
            "hidden_comment"
        ] = "API update test"
        OBSERVATIONS_API.api_update(obs_1, sighting)
        # Check
        sighting = OBSERVATIONS_API.api_get(obs_1, short_version="1")
        assert (
            sighting["data"]["forms"][0]["sightings"][0]["observers"][0][
                "hidden_comment"
            ]
            == "API update test"
        )

        # Delete test observation
        id_form_universal = sighting["data"]["forms"][0]["sightings"][0]["observers"][
            0
        ]["id_form_universal"]
        res = OBSERVATIONS_API.api_delete(obs_1)
        logging.debug(res)
        res = OBSERVATIONS_API.api_delete_list(
            data={"id_form_universal": id_form_universal}
        )
        logging.debug(res)
