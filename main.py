import sys
from src.manager import Manager
from src.models import Parameters

def print_section_header(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

def print_subsection_header(title: str):
    """Print a formatted subsection header"""
    print(f"\n  {title}")
    print(f"  {'-' * 40}")

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"{amount:,.2f} PLN"

def display_apartments(manager):
    """Display all apartments with their rooms and bills"""
    print_section_header("APARTMENTS")
    
    for apartment in manager.apartments.values():
        print(f"\n📍 {apartment.name} ({apartment.key})")
        print(f"   Location: {apartment.location}")
        print(f"   Total Area: {apartment.area_m2} m²")
        
        print_subsection_header("Rooms")
        for room in apartment.rooms.values():
            print(f"      • {room.name:<25} {room.area_m2:>6} m²")
        
        apartment_bills = [bill for bill in manager.bills if bill.apartment == apartment.key]
        if apartment_bills:
            print_subsection_header("Bills")
            for bill in apartment_bills:
                month_year = f"{bill.settlement_month}/{bill.settlement_year}" if bill.settlement_month and bill.settlement_year else "N/A"
                print(f"      • {bill.type:<15} {format_currency(bill.amount_pln):>15}  Due: {bill.date_due}  Period: {month_year}")

def display_tenants(manager):
    """Display all tenants with their details and transfers"""
    print_section_header("TENANTS")
    
    for tenant in manager.tenants.values():
        print(f"\n👤 {tenant.name}")
        print(f"   Apartment: {tenant.apartment}")
        print(f"   Room: {tenant.room}")
        print(f"   Rent: {format_currency(tenant.rent_pln)}/month")
        print(f"   Deposit: {format_currency(tenant.deposit_pln)}")
        print(f"   Agreement: {tenant.date_agreement_from} to {tenant.date_agreement_to}")
        
        tenant_transfers = [transfer for transfer in manager.transfers if transfer.tenant == tenant.name]
        if tenant_transfers:
            print_subsection_header("Transfers")
            for transfer in tenant_transfers:
                month_year = f"{transfer.settlement_month}/{transfer.settlement_year}" if transfer.settlement_month and transfer.settlement_year else "N/A"
                print(f"      • {format_currency(transfer.amount_pln):>15}  Date: {transfer.date}  Period: {month_year}")


def display_specific_settlement(manager, apartment_key: str, year: int, month: int):
    """Wyświetla szczegółowe rozliczenie dla konkretnego mieszkania i miesiąca."""
    print_section_header(f"ROZLICZENIE: {apartment_key} (Okres: {month}/{year})")
    
    settlement = manager.get_settlement(apartment_key, year, month)
    
    if not settlement:
        print(f"  ❌ Brak danych, rachunków lub mieszkanie '{apartment_key}' nie istnieje.")
        return
        
    print(f"  Całkowity koszt wygenerowany przez mieszkanie: {format_currency(settlement.total_due_pln)}")
    
    tenant_settlements = manager.create_tenants_settlements(settlement)
    
    if not tenant_settlements:
        print("  ⚠️ Brak przypisanych lokatorów do tego mieszkania w systemie.")
        return
        
    print_subsection_header("Podział kosztów na lokatorów")
    for ts in tenant_settlements:
        print(f"      • {ts.tenant:<20} Do zapłaty: {format_currency(ts.total_due_pln)}")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Blad. Uzycie: python main.py <klucz> <rok> <miesiac>")
        sys.exit(1)

    klucz = sys.argv[1]
    rok = int(sys.argv[2])
    miesiac = int(sys.argv[3])

    zarzadca = Manager(Parameters())
    rozliczenie = zarzadca.get_settlement(klucz, rok, miesiac)

    if rozliczenie:
        print(f"Mieszkanie: {rozliczenie.apartment}")
        print(f"Okres: {rozliczenie.month}/{rozliczenie.year}")
        print(f"Koszty calkowite: {rozliczenie.total_due_pln} PLN")
        
        lokatorzy = zarzadca.create_tenants_settlements(rozliczenie)
        if lokatorzy:
            print("Rozliczenie lokatorow:")
            for l in lokatorzy:
                print(f"- {l.tenant}: {l.total_due_pln:.2f} PLN")
    else:
        print("Brak danych.")
