from decimal import Decimal, getcontext
getcontext().prec = 12  # High precision for financial calculations

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

