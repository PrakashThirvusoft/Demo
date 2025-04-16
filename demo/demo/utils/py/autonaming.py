import frappe
from frappe.model.naming import make_autoname, revert_series_if_last
from erpnext.accounts.utils import get_fiscal_year

def naming_series_creation(doc, action):
    if not doc.company or doc.company != "DIMA TECHIND PRIVATE LTD.":
        return

    # Use appropriate date field
    date_field = doc.transaction_date if doc.doctype == "Purchase Order" else doc.posting_date
    fy = get_fiscal_year(date_field, as_dict=True) if date_field else None

    if fy:
        fiscal_suffix = f"{str(fy['year_start_date'].year)[-2:]}{str(fy['year_end_date'].year)[-2:]}"
        series_map = {
            "Purchase Order": f"PO-{fiscal_suffix}-.####",
            "Purchase Invoice": f"PI-{fiscal_suffix}-.####"
        }

        if doc.doctype in series_map:
            doc.name = make_autoname(series_map[doc.doctype])

def revert_naming(doc, action):
    if not doc.company or doc.company != "DIMA TECHIND PRIVATE LTD.":
        return

    date_field = doc.transaction_date if doc.doctype == "Purchase Order" else doc.posting_date
    fy = get_fiscal_year(date_field, as_dict=True) if date_field else None

    if fy:
        fiscal_suffix = f"{str(fy['year_start_date'].year)[-2:]}{str(fy['year_end_date'].year)[-2:]}"
        series_map = {
            "Purchase Order": f"PO-{fiscal_suffix}-.####",
            "Purchase Invoice": f"PI-{fiscal_suffix}-.####"
        }

        if doc.doctype in series_map:
            revert_series_if_last(series_map[doc.doctype], doc.name)
