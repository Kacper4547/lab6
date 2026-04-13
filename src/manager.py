from src.models import Apartment, Bill, Parameters, Tenant, TenantSettlement, Transfer, ApartmentSettlement
from typing import List, Tuple

class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters 

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
       
        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment_costs(self, apartment_key: str, year: int = None, month: int = None) -> float | None:
        if month is not None and (month < 1 or month > 12):
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = 0.0
        for bill in self.bills:
            if bill.apartment == apartment_key and (year is None or bill.settlement_year == year) and (month is None or bill.settlement_month == month):
                total_cost += bill.amount_pln
        return total_cost

    def get_settlement(self, apartment_key: str, year: int, month: int) -> ApartmentSettlement | None:
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = self.get_apartment_costs(apartment_key, year, month)
        if total_cost is None:
            return None
        
        return ApartmentSettlement(
            key=f"{apartment_key}-{year}-{month}",
            apartment=apartment_key,
            year=year,
            month=month,
            total_due_pln=total_cost
        )
    
    def create_tenants_settlements(self, apartment_settlement: ApartmentSettlement) -> List[TenantSettlement] | None:
        if apartment_settlement.month < 1 or apartment_settlement.month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_settlement.apartment not in self.apartments:
            return None
        tenants_in_apartment = [tenant for tenant in self.tenants.values() if tenant.apartment == apartment_settlement.apartment]
        if not tenants_in_apartment:
            return []
        
        return [
            TenantSettlement(
                tenant=tenant.name,
                apartment_settlement=apartment_settlement.key,
                month=apartment_settlement.month,
                year=apartment_settlement.year,
                total_due_pln=apartment_settlement.total_due_pln / len(tenants_in_apartment)
            )
        for tenant in tenants_in_apartment ] 
    

    def get_annual_summary(self, year: int) -> dict:
        """Generuje roczne zestawienie finansowe dla wszystkich mieszkań i lokatorów."""
        total_costs = sum(bill.amount_pln for bill in self.bills if bill.settlement_year == year)
        total_transfers = sum(t.amount_pln for t in self.transfers if t.settlement_year == year)
        
        return {
            "year": year,
            "total_costs_pln": total_costs,
            "total_transfers_pln": total_transfers,
            "balance_pln": total_transfers - total_costs
        }

    def get_debtors_report(self, year: int, month: int) -> dict:
        """Zwraca słownik dłużników (imię i nazwisko -> kwota na minusie) dla danego okresu."""
        debtors = {}
        
        for apt_key in self.apartments:
            apt_settlement = self.get_settlement(apt_key, year, month)
            if not apt_settlement:
                continue
                
            tenant_settlements = self.create_tenants_settlements(apt_settlement)
            if not tenant_settlements:
                continue
                
            for ts in tenant_settlements:
                tenant_key = next((k for k, v in self.tenants.items() if v.name == ts.tenant), None)
                if not tenant_key:
                    continue
                    
                paid = sum(t.amount_pln for t in self.transfers 
                           if t.tenant == tenant_key and t.settlement_year == year and t.settlement_month == month)
                
                balance = paid - ts.total_due_pln
                
                if balance < 0:
                    debtors[ts.tenant] = balance
                    
        return debtors
    
    def get_tax(self, year: int, month: int, tax_rate: float) -> int:
        """
        Zwraca kwotę podatku (zaokrągloną do pełnych złotych) na podstawie wszystkich
        przelewów wpłaconych w danym miesiącu rozliczeniowym.
        """
        total_income = sum(
            t.amount_pln for t in self.transfers 
            if t.settlement_year == year and t.settlement_month == month
        )
        return round(total_income * tax_rate)

    def find_apartments_without_bills(self, year: int, month: int) -> list[str]:
        """
        Zwraca listę kluczy mieszkań (apartment_key), dla których w danym
        miesiącu i roku rozliczeniowym nie wprowadzono żadnego rachunku.
        """
        apartments_with_bills = {
            bill.apartment for bill in self.bills 
            if bill.settlement_year == year and bill.settlement_month == month
        }
        
        apartments_without_bills = [
            apt_key for apt_key in self.apartments.keys() 
            if apt_key not in apartments_with_bills
        ]
        
        return apartments_without_bills