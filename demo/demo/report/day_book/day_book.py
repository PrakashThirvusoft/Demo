import frappe
from frappe import _
from erpnext import get_company_currency, get_default_company


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    invoice_count = get_invoice_count(filters)
    purchase_count = get_purchase_count(filters)
    payment_count = get_payment_count(filters)
    journal_count = get_journal_count(filters)
    total, outstanding = get_billed_amount(filters)
    purchase_total, to_pay = get_purchase_bill_amount(filters)
    paid_amount = get_payment_paid(filters)
    receive_amount = get_payment_received(filters)
    expense_amount = get_journal_expense(filters)

    invoice_count_html = f"""
            <div style="display: flex; justify-content: space-around; align-items: flex-start; background-color: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px solid #ddd; font-family: Arial, sans-serif;">

            <div style="width: 22%; height: 250px;padding: 40px; text-align: center; border-radius: 18px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); background-color: #ffe6e6; color: red;">
                <p style="font-weight: bold; font-size: 18px;">Sales Invoice</p>
                <p style="font-size: 14px;">{invoice_count}</p>
                <p style="font-size: 14px;">Sales Amount: {float(total if total is not None else '0.0') - float(outstanding if outstanding is not None else '0.0')}</p>
                <p style="font-size: 14px;">Debit Note:{outstanding if outstanding is not None else '0.0'}</p>
            </div>

            <div style="width: 22%;height: 250px; padding: 40px; text-align: center; border-radius: 18px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); background-color: #e6ffe6; color: green;">
                <p style="font-weight: bold; font-size: 18px;">Purchase Invoice</p>
                <p style="font-size: 14px;">{purchase_count}</p>
                <p style="font-size: 14px;">Purchased Amount: {float(purchase_total if purchase_total is not None else '0.0') - float(to_pay if to_pay is not None else '0.0')}</p>
                <p style="font-size: 14px;">Credit Note:{to_pay if to_pay is not None else '0.0'}</p>
            </div>

            <div style="width: 22%;height: 250px; padding: 40px; text-align: center; border-radius: 18px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); background-color: #e6f3ff; color: blue;">
                <p style="font-weight: bold; font-size: 18px;">Payment Entry</p>
                <p style="font-size: 14px;">{payment_count}</p>
                <p style="font-size: 14px;">Paid Amount: {paid_amount if paid_amount is not None else '0.0'}</p>
                <p style="font-size: 14px;">Received Amount: {receive_amount if receive_amount is not None else '0.0'}</p>
            </div>

            <div style="width: 22%;height: 250px; padding: 40px; text-align: center; border-radius: 18px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); background-color: #ffe6e6; color: red;">
                <p style="font-weight: bold; font-size: 18px;">Journal Entry</p>
                <p style="font-size: 14px;">{journal_count}</p>
                <br>
                <br>
                <br>
                <p style="font-size: 14px;">Total Expenses: {expense_amount if expense_amount is not None else '0.0'}</p>
            </div>

            </div>

    """

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date must be before To Date"))

    return columns, data, invoice_count_html


def get_columns(filters={}):
    if filters.get("company"):
        currency = get_company_currency(filters["company"])
    else:
        company = get_default_company()
        currency = get_company_currency(company)
    columns = [
		{
			"label": _("GL Entry"),
			"fieldname": "gl_entry",
			"fieldtype": "Link",
			"options": "GL Entry",
			"hidden": 1,
		},
         {"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 150},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 150},

        {
            "label": _("Voucher No"),
            "fieldname": "voucher_no",
            "fieldtype": "Dynamic Link",
            "options": "doc_type",
            "width": 180,
        },
             {
            "label": _("Party Type"),
            "fieldname": "party_type",
            "fieldtype": "Link",
            "options": "Party Type",
            "width": 180,
            "hidden":1
        },
        {
            "label": _("Party"),
            "fieldname": "party",
            "fieldtype": "Dynamic Link",
            "options": "party_type",
            "width": 180,
        },
        {
            "label": _("Account Head"),
            "fieldname": "account_head",
            "fieldtype": "Data",
            "width": 180,
        },
		{
			"label": _("Debit ({0})").format(currency),
			"fieldname": "debit",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("Credit ({0})").format(currency),
			"fieldname": "credit",
			"fieldtype": "Float",
			"width": 150,
		},
	]
    return columns


def get_invoice_count(filters):
    conditions = []

    conditions.append("docstatus = 1")

    if filters.get('company'):
        conditions.append("company = %(company)s")

    if(filters.get('voucher_no')):
        conditions.append("name = %(voucher_no)s")

    if filters.get("customer"):
        conditions.append("customer = %(customer)s")

    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(f"posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}'")


    where_clause = " AND ".join(conditions)

    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            COUNT(*) as invoice_count
        FROM
            `tabSales Invoice`
        {where_clause}
    """
    result = frappe.db.sql(query, filters, as_dict=True)
    return result[0].invoice_count if result else 0


def get_billed_amount(filters):
    conditions = []

    conditions.append("docstatus = 1")

    if filters.get('company'):
        conditions.append("company = %(company)s")

    if(filters.get('voucher_no')):
        conditions.append("name = %(voucher_no)s")

    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(f"posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}'")

    where_clause = " AND ".join(conditions)

    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            SUM(ABS(rounded_total)) as total
        FROM
            `tabSales Invoice`
        {where_clause}
        and
            status != 'return';
    """

    sales = f"""
        SELECT
            SUM(ABS(grand_total)) as outstanding
        FROM
            `tabSales Invoice`
        {where_clause}
        AND
            status='return';
    """
    result = frappe.db.sql(query, filters, as_dict=True)
    sale_return = frappe.db.sql(sales, filters, as_dict=True)
    return (result[0].total, sale_return[0].outstanding) if result else (0, 0)


def get_purchase_count(filters):
    conditions = []

    conditions.append("docstatus = 1")

    if filters.get('company'):
        conditions.append("company = %(company)s")

    if(filters.get('voucher_no')):
        conditions.append("name = %(voucher_no)s")

    if filters.get("from_date"):
        conditions.append(f"posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}'")

    where_clause = " AND ".join(conditions)

    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            COUNT(*) as invoice_count
        FROM
            `tabPurchase Invoice`
        {where_clause}
    """
    result = frappe.db.sql(query, filters, as_dict=True)
    return result[0].invoice_count if result else 0


def get_purchase_bill_amount(filters):
    conditions = []

    conditions.append("docstatus = 1")

    if filters.get('company'):
        conditions.append("company = %(company)s")

    if(filters.get('voucher_no')):
        conditions.append("name = %(voucher_no)s")

    if filters.get("from_date"):
        conditions.append(f"posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}'")

    where_clause = " AND ".join(conditions)

    if where_clause:
        where_clause = "WHERE " + where_clause


    bill_amount = f"""
        SELECT
            SUM(CASE WHEN rounded_total > 0 THEN rounded_total ELSE 0 END) as purchase_total
        FROM
            `tabPurchase Invoice`
        {where_clause}
        AND
            status !='return';
    """

    return_amount = f"""
        SELECT
            ABS(SUM(grand_total)) as to_pay
        FROM
            `tabPurchase Invoice`
        {where_clause}
        AND
            status='return';
    """

    result = frappe.db.sql(bill_amount, filters, as_dict=True)
    return_result = frappe.db.sql(return_amount, filters, as_dict = True)
    return (result[0].purchase_total, return_result[0].to_pay) if result else (0, 0)

def get_payment_count(filters):
    conditions = []
    
    conditions.append("docstatus = 1")

    if filters.get('company'):
        conditions.append("company = %(company)s")

    if filters.get("payment_type"):
        conditions.append("payment_type = %(payment_type)s")

    if(filters.get('voucher_no')):
        conditions.append("name = %(voucher_no)s")

    if filters.get("from_date"):
        conditions.append(f"posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}'")

    where_clause = " AND ".join(conditions)

    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            COUNT(*) as payment_count
        FROM
            `tabPayment Entry`
        {where_clause}
    """
    result = frappe.db.sql(query, filters, as_dict=True)
    return result[0].payment_count if result else 0


def get_payment_paid(filters):
    conditions = []

    conditions.append("docstatus = 1")

    if filters.get('company'):
        conditions.append("company = %(company)s")

    if(filters.get('voucher_no')):
        conditions.append("name = %(voucher_no)s")

    if filters.get("from_date"):
        conditions.append(f"posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}'")
    
    conditions.append("payment_type = 'Pay' ")
    conditions.append("docstatus = 1")

    where_clause = " AND ".join(conditions)

    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            SUM(paid_amount) as paid_amount
        FROM
            `tabPayment Entry`
        {where_clause}
    """
    result = frappe.db.sql(query, filters, as_dict=True)
    return result[0].paid_amount if result else 0


def get_payment_received(filters):
    conditions = []

    conditions.append("docstatus = 1")

    if filters.get('company'):
        conditions.append("company = %(company)s")

    if(filters.get('voucher_no')):
        conditions.append("name = %(voucher_no)s")

    if(filters.get('from_date')):
        conditions.append(f"posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}'")

    conditions.append("payment_type = 'Receive' ")
    conditions.append("docstatus = 1")

    where_clause = " AND ".join(conditions)

    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            SUM(paid_amount) as receive_amount
        FROM
            `tabPayment Entry`
        {where_clause}
    """
    result = frappe.db.sql(query, filters, as_dict=True)
    return result[0].receive_amount if result else 0


def get_journal_count(filters):
    conditions = f'''gl.voucher_type = 'Journal Entry'  and gl.is_cancelled = 0 and al.root_type in ("Expense", "Income", "Asset", "Liability") '''
    abr = frappe.get_value('Company', filters.get('company'), 'abbr')
    if(filters.get('company')):
        company_name = filters.get('company')
    accounts = frappe.get_all('Account', filters={'root_type': 'Expense','company': company_name, 'is_group':'0'}, fields=['name', 'is_group', 'parent_account', 'company'])
    names = []
    for i in accounts:
        if(i.parent_account != 'Stock Expenses - {0}'.format(abr)):
            if i.parent_account and i.name:
                names.append(i.name)
    inputacc = "', '".join(names)

    conditions += f" AND gl.account IN ('{inputacc}')"

    if(filters.get('company')):
        conditions += f''' and gl.company = '{filters['company']}' '''
    if(filters.get('party')):
        conditions += f''' and gl.party in ('{"', '".join(filters['party'])}') '''
    if(filters.get('voucher_no')):
        conditions += f''' and  gl.voucher_no like '%{filters['voucher_no']}%' '''

    if filters.get('from_date') and filters.get('to_date'):
        conditions += f''' and gl.posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}' '''

    query = f"""
        SELECT COUNT(*) AS journal_count
        FROM `tabGL Entry` gl
        LEFT JOIN `tabAccount` al ON al.name = gl.account
        WHERE {conditions} ;
    """

    # params = {}
    # if from_date and to_date:
    #     query += " AND gl.posting_date BETWEEN %(from_date)s AND %(to_date)s"
    #     params['from_date'] = from_date
    #     params['to_date'] = to_date

    # if voucher_no:
    #     query += " AND gl.voucher_no = %(voucher_no)s"
    #     params['voucher_no'] = voucher_no

    result = frappe.db.sql(query, as_dict=True)

    return result[0].journal_count if result else 0


def get_journal_expense(filters):

    conditions = f'''gl.voucher_type = 'Journal Entry'  and gl.is_cancelled = 0 and al.root_type in ("Expense", "Income", "Asset", "Liability") '''
    abr = frappe.get_value('Company', filters.get('company'), 'abbr')
    if(filters.get('company')):
        company_name = filters.get('company')
    accounts = frappe.get_all('Account', filters={'root_type': 'Expense','company': company_name, 'is_group':'0'}, fields=['name', 'is_group', 'parent_account', 'company'])
    names = []
    for i in accounts:
        if(i.parent_account != 'Stock Expenses - {0}'.format(abr)):
            if i.parent_account and i.name:
                names.append(i.name)
    inputacc = "', '".join(names)

    conditions += f" AND gl.account IN ('{inputacc}')"

    if(filters.get('company')):
        conditions += f''' and gl.company = '{filters['company']}' '''
    if(filters.get('party')):
        conditions += f''' and gl.party in ('{"', '".join(filters['party'])}') '''
    if(filters.get('voucher_no')):
        conditions += f''' and  gl.voucher_no like '%{filters['voucher_no']}%' '''

    if filters.get('from_date') and filters.get('to_date'):
        conditions += f''' and gl.posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}' '''


    query = f"""
        SELECT SUM(debit) AS expense_amount
        FROM `tabGL Entry` gl
        LEFT JOIN `tabAccount` al ON al.name = gl.account
        WHERE {conditions};
    """

    result = frappe.db.sql(query, as_dict=True)

    return result[0].expense_amount if result else 0


def get_data(filters={}):
    si_data = []
    pi_data = []
    pe_data = []
    je_data = []
    final_data = []
    if(filters.get('party_type')):
        if(filters.get('party_type') == 'Customer'):
            si_data = get_sales_invoice_data(filters)
    else:
        si_data = get_sales_invoice_data(filters)

    if(filters.get('party_type')):
        if(filters.get('party_type') == 'Supplier'):
            pi_data = get_purchase_invoice_data(filters)
    else:
        pi_data = get_purchase_invoice_data(filters)

    pe_data = get_payment_entry_data(filters)
    je_data = display_journal_entry(filters) 

    final_data = si_data + pi_data + pe_data + je_data
    return final_data



def get_sales_invoice_data(filters={}):
    conditions = f'''gl.is_cancelled = 0 '''
    conditions += f''' and gl.voucher_type = 'Sales Invoice' '''

    if(filters.get('company')):
        conditions += f''' and gl.company = '{filters['company']}' '''
    if(filters.get('voucher_no')):
        conditions += f''' and  gl.voucher_no like '%{filters['voucher_no']}' '''    

    if filters.get('from_date') and filters.get('to_date'):
        conditions += f''' and si.posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}' '''


    sales_invoices = frappe.db.sql(f"""
		SELECT
            voucher_type as doc_type,
			si.posting_date,
			gl.voucher_no as voucher_no,
            gl.party_type,
			gl.party as party,
			si.outstanding_amount AS credit,
			(si.rounded_total - si.outstanding_amount) AS debit
		FROM
			`tabGL Entry` gl
		JOIN
			`tabSales Invoice` si ON gl.against_voucher = si.name
        WHERE
            {conditions}
        ORDER BY
            si.posting_date;
    """, as_dict = 1)

    for i in sales_invoices:
        i['indent'] = 1
    d = 0
    c = 0
    for m in sales_invoices:
        d=d+m.debit
        c=c+m.credit
    if(len(sales_invoices) == 0):
        sales_invoices = [{'voucher_no':'No record found', 'indent':1}]
    return [{'indent':0, 'voucher_type':'Sales Invoice', 'credit':0, 'debit':0}] + sales_invoices + [{'party':'<b>Total Amount</b>', 'debit':d,'credit':c, 'is_total':1}]


def get_purchase_invoice_data(filters={}):
    conditions = f'''gl.is_cancelled = 0 '''
    conditions += f''' and gl.voucher_type = 'Purchase Invoice' '''

    if(filters.get('company')):
        conditions += f''' and gl.company = '{filters['company']}' '''
    if(filters.get('voucher_no')):
        conditions += f''' and  gl.voucher_no like '%{filters['voucher_no']}%' '''

    if filters.get('from_date') and filters.get('to_date'):
        conditions += f''' and pi.posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}' '''

    purchase_invoice = frappe.db.sql(f"""
		SELECT
            voucher_type as doc_type,
			pi.posting_date,
			gl.voucher_no as voucher_no,
            gl.party_type,
			gl.party as party,
			pi.outstanding_amount AS debit,
			(pi.rounded_total - pi.outstanding_amount) AS credit
		FROM
			`tabGL Entry` gl
		JOIN
			`tabPurchase Invoice` pi ON gl.against_voucher = pi.name
        WHERE
            {conditions}
    """, as_dict = 1)

    for i in purchase_invoice:
        i['indent'] = 1
    d = 0
    c = 0
    for m in purchase_invoice:
        d +=m.get('debit', 0) or 0
        c +=m.get('credit', 0) or 0
    if(len(purchase_invoice) == 0):
        purchase_invoice = [{'voucher_no':'No record found', 'indent':1}]
    return [{'indent':0, 'voucher_type':'Purchase Invoice', 'credit':0, 'debit':0}] + purchase_invoice + [{'party':'<b>Total Amount</b>', 'debit':d,'credit':c, 'is_total':1}]


def get_payment_entry_data(filters={}):
    default_payable_acc = frappe.db.get_value('Company', filters.get('company'), 'default_payable_account')
    default_receivable_acc = frappe.db.get_value('Company', filters.get('company'), 'default_receivable_account')
    conditions = f'''account in ('{default_payable_acc}', '{default_receivable_acc}') and voucher_type = 'Payment Entry' and is_cancelled = 0 '''

    if(filters.get('company')):
        conditions += f''' and company = '{filters['company']}' '''

    if(filters.get('party')):
        conditions += f''' and party in ('{"', '".join(filters['party'])}') '''
    if(filters.get('party_type')):
        conditions += f''' and  party_type like '%{filters['party_type']}%' '''
    if(filters.get('voucher_no')):
        conditions += f''' and  voucher_no like '%{filters['voucher_no']}%' '''

    if filters.get('from_date') and filters.get('to_date'):
        conditions += f''' and gl.posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}' '''

    payment_entry = frappe.db.sql(f"""
        SELECT
            voucher_type as doc_type, name, posting_date, party, party_type, voucher_no, sum(debit) as credit, sum(credit) as debit
        FROM `tabGL Entry` gl
        WHERE {conditions}
         GROUP BY voucher_no
         ORDER BY posting_date;
    """,  as_dict = 1)
    for i in payment_entry:
        i['indent'] = 1
    d = 0
    c = 0
    for m in payment_entry:
        d=d+m.debit
        c=c+m.credit
    if(len(payment_entry) == 0):
        payment_entry = [{'voucher_no':'No record found', 'indent':1}]
    return [{'indent':0, 'voucher_type':'Payment Entry', 'credit':0, 'debit':0}] + payment_entry + [{'party':'<b>Total Amount</b>', 'debit':d,'credit':c, 'is_total':1}]


def display_journal_entry(filters = {}):

    conditions = f'''gl.voucher_type = 'Journal Entry'  and gl.is_cancelled = 0 and al.root_type in ("Expense", "Income", "Asset", "Liability") '''
    abr = frappe.get_value('Company', filters.get('company'), 'abbr')
    if(filters.get('company')):
        company_name = filters.get('company')
    accounts = frappe.get_all('Account', filters={'root_type': 'Expense','company': company_name, 'is_group':'0'}, fields=['name', 'is_group', 'parent_account', 'company'])
    names = []
    for i in accounts:
        if(i.parent_account != 'Stock Expenses - {0}'.format(abr)):
            if i.parent_account and i.name:
                names.append(i.name)
    inputacc = "', '".join(names)

    conditions += f" AND gl.account IN ('{inputacc}')"

    if(filters.get('company')):
        conditions += f''' and gl.company = '{filters['company']}' '''
    if(filters.get('party')):
        conditions += f''' and gl.party in ('{"', '".join(filters['party'])}') '''
    if(filters.get('voucher_no')):
        conditions += f''' and  gl.voucher_no like '%{filters['voucher_no']}%' '''

    if filters.get('from_date') and filters.get('to_date'):
        conditions += f''' and gl.posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}' '''


    journal_entry = frappe.db.sql(f"""
        SELECT gl.name, gl.voucher_type as doc_type, gl.posting_date, gl.party, gl.party_type,gl.voucher_no, gl.debit, gl.credit, gl.remarks, gl.account as account_head
        FROM `tabGL Entry` gl
        LEFT JOIN `tabAccount` al ON al.name = gl.account
        WHERE {conditions}
         ORDER BY gl.posting_date;
    """,  as_dict = 1)
    for i in journal_entry:
        i['indent'] = 1
    d = 0
    c = 0
    for m in journal_entry:
        d=d+m.debit
        c=c+m.credit
    if(len(journal_entry) == 0):
        journal_entry = [{'voucher_no':'No record found', 'indent':1}]
    return [{'indent':0, 'voucher_type':'Journal Entry', 'credit':0, 'debit':0}] + journal_entry + [{'party':'<b>Total Amount</b>', 'debit':d,'credit':c, 'is_total':1}]