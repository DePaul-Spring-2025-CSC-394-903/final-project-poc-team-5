import datetime
from decimal import Decimal, getcontext

getcontext().prec = 12

EMPLOYEE_LIMIT = Decimal('23000')
CATCHUP = Decimal('7500')
TOTAL_LIMIT = Decimal('66000')

def calcGains(init_deposit, current_age, retirement_age, salary,
              salary_growth_per, contribution_per, employer_match_per,
              employer_match_limit_per, annual_yield,
              contrib_growth_per_year=Decimal('0.00'),
              annual_fee_per_year=Decimal('0.00')):

    balance = Decimal(init_deposit)
    salary = Decimal(salary)
    contribution_per = Decimal(contribution_per)
    employer_match_per = Decimal(employer_match_per)
    employer_match_limit_per = Decimal(employer_match_limit_per)
    salary_growth_per = Decimal(salary_growth_per)
    annual_yield = Decimal(annual_yield)

    months = (retirement_age - current_age) * 12
    monthly_yield = (1 + annual_yield) ** (Decimal(1)/12) - 1

    balance_by_year = [float(balance)]
    total_emp = Decimal(0)
    total_em = Decimal(0)

    for m in range(1, months+1):
        # At beginning of each year except month 1
        if m % 12 == 1 and m > 1:
            salary *= (1 + salary_growth_per)
            contribution_per += contrib_growth_per_year

        monthly_salary = salary / 12
        emp_cap_annual = EMPLOYEE_LIMIT + (CATCHUP if (current_age + (m//12)) >= 50 else Decimal('0'))
        total_cap = TOTAL_LIMIT + (CATCHUP if (current_age + (m//12)) >= 50 else Decimal('0'))

        emp_cap_monthly = emp_cap_annual / 12
        total_cap_monthly = total_cap / 12

        emp_contrib = min(monthly_salary * contribution_per, emp_cap_monthly)
        matchable_base = min(emp_contrib, monthly_salary * employer_match_limit_per)
        em_contrib = min(matchable_base * employer_match_per, total_cap_monthly - emp_contrib)
        em_contrib = max(em_contrib, Decimal('0'))

        total_emp += emp_contrib
        total_em += em_contrib

        balance += (emp_contrib + em_contrib)
        balance *= (1 + monthly_yield)

        # Apply annual fee at end of each year
        if m % 12 == 0 and annual_fee_per_year > 0:
            balance *= (1 - annual_fee_per_year)

        if m % 12 == 0:
            balance_by_year.append(round(float(balance), 2))

    return round(float(balance), 2), balance_by_year, float(total_emp), float(total_em)
