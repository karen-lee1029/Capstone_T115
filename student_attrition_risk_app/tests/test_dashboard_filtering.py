"""Offline checks of the repository dashboard definition for US-29 (Feature-006).

Interactive filtering and drill-down: dashboard-wide filters, sensitive-attribute isolation,
"Students in this view" tables and the "How to filter and drill down" panel. The contract is
specs/006-dashboard-filtering-drilldown/contracts/dashboard-interaction-contract.md. Platform
behaviour (filter propagation, cross-filtering, rendering limits) is evidenced in the workspace,
not here; see the acceptance matrix in specs/006-dashboard-filtering-drilldown/quickstart.md.
"""

import json
import subprocess
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_RELATIVE = "student_attrition_risk_app/dashboard/Student Attrition Risk Overview.lvdash.json"
DASHBOARD_PATH = APP_DIR / "dashboard" / "Student Attrition Risk Overview.lvdash.json"
BASE_COMMIT = "0409d7e"

PREDICTION = "b798cf1c"
ENROLMENT = "student_enrolment"

# (widget name, title, dataset, dimension) -- contract C-1, in order.
FILTER_CONTRACT = [
    ("filter_risk_level", "Filter by Risk Level", PREDICTION, "risk_level"),
    ("filter_faculty", "Filter by Faculty", ENROLMENT, "faculty"),
    ("filter_course_level", "Filter by Course Level", ENROLMENT, "course_level"),
    ("filter_field_of_education", "Filter by Field of Education", ENROLMENT,
     "broad_primary_field_of_education"),
    ("filter_origin", "Filter by Origin", ENROLMENT, "international_domestic"),
    ("filter_age_band", "Filter by Age Band", ENROLMENT, "age_band"),
    ("filter_study_mode", "Filter by Study Mode", ENROLMENT, "study_mode"),
    ("filter_commencing_continuing", "Filter by Commencing/Continuing", ENROLMENT,
     "commencing_continuing"),
]
FILTERED_DIMENSIONS = {dimension for _, _, _, dimension in FILTER_CONTRACT}
SENSITIVE_DIMENSIONS = {"gender", "socioeconomic_status", "first_nations", "home_language"}
# Q21 -> Q22: the only table allowed to show a sensitive field beside other data widgets.
# No ignore setting is available in the workspace; matrix row B7 checks it there.
OBSERVED_SENSITIVE_TABLES = {"drill_table_demographic"}

PAGE_ORDER = [
    "Overview", "Course Analysis", "Demographic Breakdown", "Gender Breakdown", "Student List",
    "Filters",
]

P = "student_attrition_risk_prediction__"
E = "Student_Enrolment_Details__"
COMMON_COLUMNS = [
    (P + "student_id", "Student ID (de-identified)"),
    (P + "risk_pct", "Risk %"),
    (P + "risk_level", "Risk Level"),
]
# (page, widget name) -> columns in order -- contract C-2.
DRILL_TABLES = {
    ("Overview", "drill_table_overview"): COMMON_COLUMNS + [
        (P + "risk_score_bucket", "Risk Score Range"),
    ],
    ("Course Analysis", "drill_table_course"): COMMON_COLUMNS + [
        (E + "course_level", "Course Level"),
        (E + "broad_primary_field_of_education", "Field of Education"),
    ],
    ("Demographic Breakdown", "drill_table_demographic"): COMMON_COLUMNS + [
        (E + "age_band", "Age Band"),
        (E + "gender", "Gender"),
        (E + "international_domestic", "Origin"),
    ],
}
DRILL_TITLE = "Students in this view"
DRILL_DESCRIPTION = (
    "Up to 100,000 students matching the current filters and chart selection, highest risk "
    "first. Narrow the view to see others, or find any student by ID on Student List"
)
HOW_TO_FILTER_PHRASES = [
    "How to filter and drill down", "Filters", "every page", "click a bar", "active filter bar",
    "Students in this view", "Student ID (de-identified)", "enrolment record", "100,000",
    "Gender Breakdown",
]

# Base widgets that Feature-006 moves or edits (contract C-4); compared without their position.
REPOSITIONED = {
    "3158dd73", "98aa39b6", "100b44c5", "3edf02b6", "41477a60", "0d5ba328", "c2d55445",
    "292bc630", "52cb0fd3",
}
REMOVED = {"310fbbb0"}
TEXT_EDITED = {"521bf497"}


def _load() -> dict:
    return json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))


def _load_base() -> dict:
    try:
        raw = subprocess.run(
            ["git", "show", f"{BASE_COMMIT}:{DASHBOARD_RELATIVE}"],
            cwd=APP_DIR, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip(f"Base commit {BASE_COMMIT} is not available from git")
    return json.loads(raw.decode("utf-8"))


def _page(dash: dict, display_name: str) -> dict:
    for page in dash["pages"]:
        if page["displayName"] == display_name:
            return page
    raise AssertionError(f"Page {display_name!r} not found")


def _widgets(page: dict) -> list[dict]:
    return [item["widget"] for item in page.get("layout", [])]


def _all_widgets(dash: dict) -> list[tuple[dict, dict]]:
    return [(page, widget) for page in dash["pages"] for widget in _widgets(page)]


def _widget(dash: dict, name: str) -> dict:
    for _, widget in _all_widgets(dash):
        if widget["name"] == name:
            return widget
    raise AssertionError(f"Widget {name!r} not found")


def _position(dash: dict, name: str) -> dict:
    for page in dash["pages"]:
        for item in page.get("layout", []):
            if item["widget"]["name"] == name:
                return item["position"]
    raise AssertionError(f"Widget {name!r} not found")


def _widget_type(widget: dict) -> str:
    return widget.get("spec", {}).get("widgetType", "")


def _title(widget: dict) -> str | None:
    return widget.get("spec", {}).get("frame", {}).get("title", {}).get("value")


def _is_filter(widget: dict) -> bool:
    return _widget_type(widget).startswith("filter")


def _is_data_widget(widget: dict) -> bool:
    return bool(widget.get("queries")) and not _is_filter(widget)


def _expressions(widget: dict) -> list[str]:
    return [f.get("expression", "") for q in widget.get("queries", []) for f in q["query"]["fields"]]


def _uses_dimension(widget: dict, dimension: str) -> bool:
    return any(expr.endswith(f"`{dimension}`") for expr in _expressions(widget))


def _filter_dimensions(widget: dict) -> set[str]:
    """Dimensions a filter is bound to, read from both its field aliases and its expressions."""
    found = set()
    for query in widget.get("queries", []):
        for field in query["query"]["fields"]:
            if field["name"].endswith("_associativity"):
                continue
            found.add(field["name"])
            found.add(field["expression"].strip("`"))
    for field in widget.get("spec", {}).get("encodings", {}).get("fields", []):
        found.add(field.get("fieldName"))
    return found


def _dataset_dimensions(dash: dict, dataset_name: str) -> set[str]:
    dataset = next(d for d in dash["datasets"] if d["name"] == dataset_name)
    return {dim.get("name") for dim in dataset["config"].get("dimensions", [])}


def _table_sort(widget: dict) -> list[tuple[str, str]]:
    """(expression, direction) pairs of a table's default sort, from the query's ``orders`` (R-3)."""
    orders = widget["queries"][0]["query"].get("orders", [])
    return [(order["expression"], order["direction"]) for order in orders]


# ---------------------------------------------------------------------------
# US1 -- dashboard-wide filters (FR-001 - FR-007)
# ---------------------------------------------------------------------------

class TestDashboardWideFilters:
    def test_page_order(self):
        assert [p["displayName"] for p in _load()["pages"]] == PAGE_ORDER

    def test_single_global_filters_page(self):
        pages = [p for p in _load()["pages"] if p.get("pageType") == "PAGE_TYPE_GLOBAL_FILTERS"]
        assert len(pages) == 1
        assert pages[0]["name"] == "global_filters"
        assert pages[0]["displayName"] == "Filters"

    def test_global_filters_match_contract(self):
        widgets = _widgets(_page(_load(), "Filters"))
        actual = [(w["name"], _title(w), _widget_type(w)) for w in widgets]
        expected = [(name, title, "filter-multi-select") for name, title, _, _ in FILTER_CONTRACT]
        assert actual == expected

    @pytest.mark.parametrize("name,title,dataset,dimension", FILTER_CONTRACT)
    def test_filter_fields_resolve_to_dataset_dimensions(self, name, title, dataset, dimension):
        dash = _load()
        widget = _widget(dash, name)
        assert [q["query"]["datasetName"] for q in widget["queries"]] == [dataset]
        assert _filter_dimensions(widget) == {dimension}
        assert dimension in _dataset_dimensions(dash, dataset)

    @pytest.mark.parametrize("name,title,dataset,dimension", FILTER_CONTRACT)
    def test_filter_binding_is_complete(self, name, title, dataset, dimension):
        # Query fields, query name and encoding must bind the control to one dimension together.
        widget = _widget(_load(), name)
        [query] = widget["queries"]
        assert query["query"]["fields"] == [
            {"name": dimension, "expression": f"`{dimension}`"},
            {"name": f"{dimension}_associativity",
             "expression": "COUNT_IF(`associative_filter_predicate_group`)"},
        ]
        assert query["query"]["disaggregated"] is False
        assert widget["spec"]["encodings"]["fields"] == [
            {"fieldName": dimension, "queryName": query["name"]},
        ]

    def test_no_filter_on_sensitive_attributes(self):
        for _, widget in _all_widgets(_load()):
            if _is_filter(widget):
                assert not _filter_dimensions(widget) & SENSITIVE_DIMENSIONS, widget["name"]

    def test_no_fixed_filter_conflicts_with_global_filters(self):
        for _, widget in _all_widgets(_load()):
            for query in widget.get("queries", []):
                for flt in query["query"].get("filters", []):
                    expr = flt["expression"]
                    if widget["name"] in {"counter_high", "counter_low"}:
                        assert "`risk_level`" in expr
                        continue
                    hits = [d for d in FILTERED_DIMENSIONS if f"`{d}`" in expr]
                    assert not hits, f"{widget['name']} fixes {hits}"

    def test_student_list_risk_filter_replaced(self):
        dash = _load()
        names = {w["name"] for _, w in _all_widgets(dash)}
        assert not names & REMOVED
        search = _widget(dash, "c2d55445")
        assert _title(search) == "Search Student"
        assert search in _widgets(_page(dash, "Student List"))
        assert _position(dash, "c2d55445")["width"] == 12

    def test_filters_apply_immediately(self):
        assert _load()["uiSettings"]["applyModeEnabled"] is False


# ---------------------------------------------------------------------------
# US2 -- click-to-focus and sensitive isolation (FR-004(b), FR-008)
# ---------------------------------------------------------------------------

class TestChartSelection:
    def test_page_widgets_share_relationship_graph(self):
        for page in _load()["pages"]:
            if page.get("pageType") != "PAGE_TYPE_CANVAS":
                continue
            for widget in _widgets(page):
                if _is_data_widget(widget):
                    for query in widget["queries"]:
                        assert "datasetName" not in query["query"], widget["name"]

    def test_sensitive_charts_are_isolated(self):
        for page in _load()["pages"]:
            data = [w for w in _widgets(page) if _is_data_widget(w)]
            for widget in data:
                if widget["name"] in OBSERVED_SENSITIVE_TABLES:
                    continue
                if any(_uses_dimension(widget, d) for d in SENSITIVE_DIMENSIONS):
                    assert data == [widget], (
                        f"{widget['name']} selects on a sensitive field but shares "
                        f"{page['displayName']!r} with other data widgets"
                    )

    def test_gender_chart_is_on_gender_breakdown(self):
        page = _page(_load(), "Gender Breakdown")
        assert page.get("pageType") == "PAGE_TYPE_CANVAS"
        assert "52cb0fd3" in {w["name"] for w in _widgets(page)}


# ---------------------------------------------------------------------------
# US3 -- Students in this view tables (FR-010 - FR-013)
# ---------------------------------------------------------------------------

class TestDrillTables:
    @pytest.mark.parametrize("page_name", ["Overview", "Course Analysis", "Demographic Breakdown"])
    def test_each_analysis_page_has_one_drill_table(self, page_name):
        tables = [
            w for w in _widgets(_page(_load(), page_name))
            if _widget_type(w) == "table" and _title(w) == DRILL_TITLE
        ]
        assert len(tables) == 1

    @pytest.mark.parametrize("key", sorted(DRILL_TABLES))
    def test_drill_table_columns_match_contract(self, key):
        page_name, name = key
        dash = _load()
        widget = _widget(dash, name)
        assert widget in _widgets(_page(dash, page_name))
        columns = [(c["fieldName"], c["displayName"]) for c in widget["spec"]["encodings"]["columns"]]
        assert columns == DRILL_TABLES[key]
        # Each column is bound to the dimension its alias names, not only labelled with it.
        expected_fields = []
        for alias, _ in columns:
            source, dimension = alias.split("__")
            expected_fields.append({"name": alias, "expression": f"`{source}`.`{dimension}`"})
        assert widget["queries"][0]["query"]["fields"] == expected_fields

    @pytest.mark.parametrize("key", sorted(DRILL_TABLES))
    def test_drill_table_sorted_by_risk_desc_with_boundary_text(self, key):
        widget = _widget(_load(), key[1])
        query = widget["queries"][0]["query"]
        assert query["disaggregated"] is True
        assert not query.get("filters")
        assert "limit" not in json.dumps(query).lower()
        assert _table_sort(widget) == [("`student_attrition_risk_prediction`.`risk_pct`", "DESC")]
        frame = widget["spec"]["frame"]
        assert frame["showDescription"] is True
        assert frame["description"]["value"] == DRILL_DESCRIPTION

    @pytest.mark.parametrize("key", sorted(DRILL_TABLES))
    def test_drill_table_uses_student_id_dimension(self, key):
        widget = _widget(_load(), key[1])
        fields = widget["queries"][0]["query"]["fields"]
        assert fields[0] == {
            "name": P + "student_id",
            "expression": "`student_attrition_risk_prediction`.`student_id`",
        }
        assert widget["spec"]["encodings"]["columns"][0].get("useForSearch") is True


# ---------------------------------------------------------------------------
# US4 -- explanation and preservation (FR-014 - FR-016)
# ---------------------------------------------------------------------------

class TestExplanationAndPreservation:
    def test_how_to_filter_panel_content(self):
        dash = _load()
        widget = _widget(dash, "how_to_filter")
        assert widget in _widgets(_page(dash, "Overview"))
        text = "".join(widget["multilineTextboxSpec"]["lines"])
        for phrase in HOW_TO_FILTER_PHRASES:
            assert phrase.lower() in text.lower(), f"how_to_filter is missing {phrase!r}"

    def test_preserved_parts_match_base(self):
        base, current = _load_base(), _load()
        for key in ("datasets", "relationshipGraphs", "uiSettings"):
            assert current[key] == base[key], key
        current_widgets = {w["name"]: w for _, w in _all_widgets(current)}
        for _, widget in _all_widgets(base):
            name = widget["name"]
            if name in REMOVED:
                continue
            if name in TEXT_EDITED:
                assert set(current_widgets[name]) == set(widget)
                continue
            assert current_widgets[name] == widget, name
        for page in base["pages"]:
            now = _page(current, page["displayName"])
            assert (now["name"], now.get("pageType")) == (page["name"], page.get("pageType"))
        for name in REPOSITIONED:
            assert name in current_widgets
