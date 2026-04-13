import pytest
from src.manager import Manager
from src.models import Parameters

def test_data_integrity_total_due_matches_apartment_costs():
    manager = Manager(Parameters())
    
    apartment_key = 'apart-polanka'
    year = 2025
    month = 1
    apartment_settlement = manager.get_settlement(apartment_key, year, month)
    
    assert apartment_settlement is not None, "Rozliczenie mieszkania nie powinno być None"
    
    tenants_settlements = manager.create_tenants_settlements(apartment_settlement)
    
    assert tenants_settlements is not None
    assert len(tenants_settlements) > 0, "Brak lokatorów w mieszkaniu do przeprowadzenia testu"

    sum_tenants_due = sum(settlement.total_due_pln for settlement in tenants_settlements)


    assert sum_tenants_due == pytest.approx(apartment_settlement.total_due_pln)


from src.models import Bill

def test_get_annual_summary():
    manager = Manager(Parameters())
    summary = manager.get_annual_summary(2025)
    
    assert summary is not None
    assert summary["year"] == 2025
    assert summary["total_costs_pln"] == 910.0
    assert summary["total_transfers_pln"] == 7500.0
    assert summary["balance_pln"] == 6590.0

def test_get_debtors_report():
    manager = Manager(Parameters())
    
    debtors = manager.get_debtors_report(2025, 1)
    assert len(debtors) == 0
    
    manager.bills.append(Bill(
        amount_pln=9000.0, 
        date_due="2025-01-20", 
        apartment="apart-polanka", 
        settlement_year=2025, 
        settlement_month=1, 
        type="repair"
    ))
    
    debtors_with_huge_bill = manager.get_debtors_report(2025, 1)
    
    assert len(debtors_with_huge_bill) == 3
    assert "Jan Nowak" in debtors_with_huge_bill
    assert debtors_with_huge_bill["Jan Nowak"] == pytest.approx(-803.333333)



def test_get_tax():
    manager = Manager(Parameters())
    manager.transfers = [] 
    
    from src.models import Transfer
    manager.transfers.extend([
        Transfer(amount_pln=2000.0, date="2025-01-01", settlement_year=2025, settlement_month=1, tenant="tenant-1"),
        Transfer(amount_pln=1000.0, date="2025-01-02", settlement_year=2025, settlement_month=1, tenant="tenant-2"),
    ])
    
    tax = manager.get_tax(2025, 1, 0.085)
    assert tax == 255

    manager.transfers[0].amount_pln = 3333.0
    manager.transfers[1].amount_pln = 0.0
    tax_rounded = manager.get_tax(2025, 1, 0.085)
    assert tax_rounded == 283


def test_find_apartments_without_bills():
    manager = Manager(Parameters())
    
    from src.models import Bill, Apartment
    manager.apartments = {
        "apart-1": Apartment(key="apart-1", name="A1", location="L1", area_m2=50, rooms={}),
        "apart-2": Apartment(key="apart-2", name="A2", location="L2", area_m2=60, rooms={})
    }
    
    manager.bills = [
        Bill(amount_pln=500.0, date_due="2025-02-10", apartment="apart-1", settlement_year=2025, settlement_month=2, type="rent")
    ]
    
    missing = manager.find_apartments_without_bills(2025, 2)
    assert isinstance(missing, list)
    assert len(missing) == 1
    assert "apart-2" in missing
    assert "apart-1" not in missing