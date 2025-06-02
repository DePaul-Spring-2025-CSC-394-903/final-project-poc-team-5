import datetime
from decimal import Decimal, getcontext
from .tax_data import federal_tax_brackets, state_tax_brackets_2025
getcontext().prec = 12

# IRS contribution caps for 2025
EMPLOYEE_LIMIT = 23000
CATCHUP_CONTRIBUTION = 7500
TOTAL_CONTRIBUTION_LIMIT = 66000

def calcGains(init_deposit, current_age, retirement_age, salary,
              salary_growth_per, contribution_per, employer_match_per,
              employer_match_limit, annual_yield):
    
    balance = Decimal(init_deposit)
    salary = Decimal(salary)
    contribution_per = Decimal(contribution_per)
    employer_match_per = Decimal(employer_match_per)
    employer_match_limit = Decimal(employer_match_limit)
    salary_growth_per = Decimal(salary_growth_per)
    annual_yield = Decimal(annual_yield)

    months = (retirement_age - current_age) * 12
    monthly_yield = (1 + annual_yield) ** (Decimal(1) / 12) - 1
    balance_by_year = [float(balance)]

    total_employee_contrib = Decimal(0)
    total_employer_contrib = Decimal(0)

    for m in range(1, months + 1):
        age = current_age + (m // 12)

        if m % 12 == 1 and m > 1:
            salary *= (1 + salary_growth_per)

        monthly_salary = salary / 12
        proposed_employee_contrib = monthly_salary * contribution_per

        annual_employee_cap = EMPLOYEE_LIMIT + (CATCHUP_CONTRIBUTION if age >= 50 else 0)
        annual_total_cap = TOTAL_CONTRIBUTION_LIMIT + (CATCHUP_CONTRIBUTION if age >= 50 else 0)
        monthly_employee_cap = Decimal(annual_employee_cap) / 12
        monthly_total_cap = Decimal(annual_total_cap) / 12

        employee_contrib = min(proposed_employee_contrib, monthly_employee_cap)

        max_matchable = monthly_salary * employer_match_limit
        matchable_amount = min(employee_contrib, max_matchable)
        raw_employer_match = matchable_amount * employer_match_per

        available_room = monthly_total_cap - employee_contrib
        employer_match = min(raw_employer_match, max(Decimal(0), available_room))

        total_employee_contrib += employee_contrib
        total_employer_contrib += employer_match

        total_contribution = employee_contrib + employer_match
        balance += total_contribution
        balance *= (1 + monthly_yield)

        if m % 12 == 0:
            balance_by_year.append(round(float(balance), 2))

    return (
        round(float(balance), 2),
        balance_by_year,
        float(total_employee_contrib),
        float(total_employer_contrib),
    )

    return round(float(balance), 2), balance_by_year, float(total_emp), float(total_em)

#federal_tax_brackets = {
    #"single": [(0, 11000, 0.10), (11001, 44725, 0.12), (44726, 95375, 0.22), (95376, 182100, 0.24)],
    #"married": [(0, 22000, 0.10), (22001, 89450, 0.12), (89451, 190750, 0.22), (190751, 364200, 0.24)]
#}

"""full_state_tax_rates = {
    "AL": {"single_rate": 0.05, "married_rate": 0.05},
    "AK": {"single_rate": 0.00, "married_rate": 0.00},
    "AZ": {"single_rate": 0.025, "married_rate": 0.025},
    "AR": {"single_rate": 0.049, "married_rate": 0.049},
    "CA": {"single_rate": 0.093, "married_rate": 0.093},
    "CO": {"single_rate": 0.044, "married_rate": 0.044},
    "CT": {"single_rate": 0.03, "married_rate": 0.05},
    "DE": {"single_rate": 0.0555, "married_rate": 0.0555},
    "FL": {"single_rate": 0.00, "married_rate": 0.00},
    "GA": {"single_rate": 0.0575, "married_rate": 0.0575},
    "HI": {"single_rate": 0.0825, "married_rate": 0.0825},
    "ID": {"single_rate": 0.058, "married_rate": 0.058},
    "IL": {"single_rate": 0.0495, "married_rate": 0.0495},
    "IN": {"single_rate": 0.0323, "married_rate": 0.0323},
    "IA": {"single_rate": 0.06, "married_rate": 0.06},
    "KS": {"single_rate": 0.057, "married_rate": 0.057},
    "KY": {"single_rate": 0.045, "married_rate": 0.045},
    "LA": {"single_rate": 0.045, "married_rate": 0.045},
    "ME": {"single_rate": 0.0715, "married_rate": 0.0715},
    "MD": {"single_rate": 0.0475, "married_rate": 0.0475},
    "MA": {"single_rate": 0.050, "married_rate": 0.050},
    "MI": {"single_rate": 0.0425, "married_rate": 0.0425},
    "MN": {"single_rate": 0.0535, "married_rate": 0.068},
    "MS": {"single_rate": 0.05, "married_rate": 0.05},
    "MO": {"single_rate": 0.045, "married_rate": 0.045},
    "MT": {"single_rate": 0.0675, "married_rate": 0.0675},
    "NE": {"single_rate": 0.0664, "married_rate": 0.0664},
    "NV": {"single_rate": 0.00, "married_rate": 0.00},
    "NH": {"single_rate": 0.00, "married_rate": 0.00},
    "NJ": {"single_rate": 0.059, "married_rate": 0.059},
    "NM": {"single_rate": 0.049, "married_rate": 0.049},
    "NY": {"single_rate": 0.062, "married_rate": 0.062},
    "NC": {"single_rate": 0.0475, "married_rate": 0.0475},
    "ND": {"single_rate": 0.021, "married_rate": 0.021},
    "OH": {"single_rate": 0.029, "married_rate": 0.029},
    "OK": {"single_rate": 0.0475, "married_rate": 0.0475},
    "OR": {"single_rate": 0.0875, "married_rate": 0.0875},
    "PA": {"single_rate": 0.0307, "married_rate": 0.0307},
    "RI": {"single_rate": 0.051, "married_rate": 0.051},
    "SC": {"single_rate": 0.0575, "married_rate": 0.0575},
    "SD": {"single_rate": 0.00, "married_rate": 0.00},
    "TN": {"single_rate": 0.00, "married_rate": 0.00},
    "TX": {"single_rate": 0.00, "married_rate": 0.00},
    "UT": {"single_rate": 0.0485, "married_rate": 0.0485},
    "VT": {"single_rate": 0.065, "married_rate": 0.065},
    "VA": {"single_rate": 0.0575, "married_rate": 0.0575},
    "WA": {"single_rate": 0.00, "married_rate": 0.00},
    "WV": {"single_rate": 0.05, "married_rate": 0.05},
    "WI": {"single_rate": 0.045, "married_rate": 0.045},
    "WY": {"single_rate": 0.00, "married_rate": 0.00},
    "DC": {"single_rate": 0.06, "married_rate": 0.06}
}"""

def calculate_federal_tax(income, status, allowances=0):
    brackets = federal_tax_brackets

    standard_deductions = {
        "single": 15000,
        "married": 30000,
        #"head": 22500  # wont do this maybe idk
    }

    # Subtract standard deduction instead of allowance-based method
    deduction = standard_deductions.get(status, 15000)
    taxable_income = max(0, income - deduction)

    tax = 0
    for lower, upper, rate in brackets[status]:
        if taxable_income > upper:
            tax += (upper - lower) * rate
        else:
            tax += (taxable_income - lower) * rate
            break

    return round(tax, 2)

def calculate_state_tax(income, state, status, allowances=0):
    brackets = state_tax_brackets_2025.get(state)
    if not brackets:
        return 0.0  # No state income tax

    taxable_income = max(0, income - allowances * 1000)
    tax = 0.0
    for lower, upper, rate in brackets[status]:
        if taxable_income > upper:
            tax += (upper - lower) * rate
        else:
            tax += (taxable_income - lower) * rate
            break
    return round(tax, 2)

def calculate_fica_breakdown(income, status="single"):
    ss = round(min(income, 168600) * 0.062, 2)
    medicare = round(income * 0.0145, 2)

    surtax_threshold = 200000 if status == "single" else 250000
    if income > surtax_threshold:
        medicare += round((income - surtax_threshold) * 0.009, 2)

    return ss, medicare

def calculate_take_home(income, status, state, fed_allowances=1, state_allowances=1, local_rate=0.0, pre_tax=0.0, post_tax=0.0):
    gross_income = income
    income -= pre_tax

    fed_tax = calculate_federal_tax(income, status, fed_allowances)
    state_tax = calculate_state_tax(income, state, status, state_allowances)
    ss, medicare = calculate_fica_breakdown(income)
    local_tax = round(income * local_rate, 2)

    total_tax = fed_tax + state_tax + ss + medicare + local_tax
    take_home = income - total_tax - post_tax

    return {
        "gross_income": round(gross_income, 2),
        "federal_tax": fed_tax,
        "state_tax": state_tax,
        "social_security": ss,
        "medicare": medicare,
        "fica_tax": ss + medicare,
        "local_tax": local_tax,
        "total_tax": round(total_tax, 2),
        "post_tax_deductions": post_tax,
        "take_home_pay": round(take_home, 2),
    }

def generate_amortization_schedule(principal, annual_rate, years, start_date):
    monthly_rate = Decimal(annual_rate) / 100 / 12
    n = years * 12
    schedule = []
    balance = principal

    try:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)
    except ZeroDivisionError:
        monthly_payment = principal / n

    current_date = start_date

    for _ in range(n):
        interest = balance * monthly_rate
        principal_payment = monthly_payment - interest
        balance -= principal_payment

        schedule.append({
            "date": current_date.strftime("%b %Y"),
            "principal": round(principal_payment, 2),
            "interest": round(interest, 2),
            "monthly_total": round(monthly_payment, 2),
            "balance": round(balance, 2)
        })

        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    return schedule    