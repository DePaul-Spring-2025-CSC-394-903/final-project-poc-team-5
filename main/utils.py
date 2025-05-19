import datetime

YEAR = datetime.date.today().year

def calcGains(initDeposit, yearOfRetirement, salary, salaryGrowthPer, contributionPer, employerMatchPer, annualYield):
    balance = initDeposit
    distance = int(yearOfRetirement - YEAR)
    balance_by_year = [balance]

    for _ in range(distance):
        salary *= (1 + salaryGrowthPer)
        balance += salary * ((contributionPer) + (employerMatchPer))
        balance *= (1 + annualYield)
        balance_by_year.append(round(balance, 2))

    return round(balance, 2), balance_by_year