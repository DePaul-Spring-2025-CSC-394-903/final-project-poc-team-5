import datetime

YEAR = datetime.date.today().year

EMPLOYEE_LIMIT = 23000
CATCHUP_CONTRIBUTION = 7500
TOTAL_CONTRIBUTION_LIMIT = 66000

def calcGains(init_deposit, current_age, retirement_age, salary, salary_growth_per, contribution_per, employer_match_per, annual_yield):
    balance = init_deposit
    years_until_retirement = retirement_age - current_age
    balance_by_year = [balance]

    for year in range(years_until_retirement):
        salary *= (1 + salary_growth_per)
        age = current_age + year

        # IRS caps
        employee_cap = EMPLOYEE_LIMIT + (CATCHUP_CONTRIBUTION if age >= 50 else 0)
        total_cap = TOTAL_CONTRIBUTION_LIMIT + (CATCHUP_CONTRIBUTION if age >= 50 else 0)

        employee_contribution = salary * contribution_per
        if employee_contribution > employee_cap:
            employee_contribution = employee_cap

        employer_match = salary * employer_match_per
        if employee_contribution + employer_match > total_cap:
            employer_match = total_cap - employee_contribution
            if employer_match < 0:
                employer_match = 0

        total_contribution = employee_contribution + employer_match
        balance += total_contribution
        balance *= (1 + annual_yield)

        balance_by_year.append(round(balance, 2))

        # DEBUG:
        print(f"Year {year+1} | Age {age} | Salary: {salary:.2f} | Emp: {employee_contribution:.2f} | Match: {employer_match:.2f} | Balance: {balance:.2f}")

    return round(balance, 2), balance_by_year
