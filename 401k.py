#!/usr/bin/env python3

# pip install matplotlib

import matplotlib.pyplot as plt

# constants we'll use to calculate what our traditional vs roth 401k accounts will look like
starting_balance = 0
annual_salary = 100000
annual_contributions = 20000
annual_growth_rate = 0.05
age = 23
retirement_age = 65
annual_retirement_expenses = 125000
annual_social_security = 15000
standard_deduction = 15000 # for married couples filing separately


def calculate_federal_tax(income):
    # 2025 tax brackets for Married Filing Separately
    brackets = [
        (0, 11925, 0.10),
        (11925, 48475, 0.12),
        (48475, 103350, 0.22),
        (103350, 197300, 0.24),
        (197300, 250525, 0.32),
        (250525, 375800, 0.35),
        (375800, float('inf'), 0.37)
    ]

    tax = 0.0
    for lower, upper, rate in brackets:
        if income > lower:
            taxable_amount = min(income, upper) - lower
            tax += taxable_amount * rate
        else:
            break
    return tax

def sim_401k(
        starting_balance,
        annual_contribution,
        annual_growth_rate,
        age,
        retirement_age,
        annual_retirement_expenses,
        annual_social_security,
        standard_deduction,
):
    def gross_withdrawal_needed(net_needed, deduction=15000, tolerance=1e-2, max_iter=100):
        # Estimate gross needed to net a given amount after tax
        guess = net_needed
        for _ in range(max_iter):
            taxable_income = max(guess - deduction, 0)
            tax = calculate_federal_tax(taxable_income)
            net = guess - tax
            if abs(net - net_needed) < tolerance:
                return guess, tax
            guess += (net_needed - net)  # Adjust guess toward target
        return guess, tax
    
    balance = starting_balance
    balance_history = [] # (age, balance, taxes, withdrawals)

    for year in range(age, 110):
        balance += annual_contribution if year < retirement_age else 0
        balance *= (1 + annual_growth_rate) # apply before withdrawal

        withdrawal = tax = 0

        if year > retirement_age:
            social_security_income = 0
            if year > 65: # social security age
                social_security_income = annual_social_security

            expenses = max(annual_retirement_expenses - social_security_income, 0)
            
            # this is what I need net. Now calculate the gross withdrawal
            withdrawal, tax = gross_withdrawal_needed(expenses, deduction=standard_deduction)
            withdrawal = round(withdrawal, 2)
            tax = round(tax, 2)
            
            balance -= withdrawal
            balance = round(balance, 2)

        balance_history.append((year, balance, withdrawal, tax))
        # print(f'{year}\n\t{balance}\n\t{withdrawal}\n\t{tax}\n')

        if balance <= 0:
            break

    return balance_history


def sim_roth(
        starting_balance,
        annual_salary,
        annual_contribution,
        annual_growth_rate,
        age,
        retirement_age,
        annual_retirement_expenses,
        annual_social_security,
):
    balance = starting_balance
    balance_history = [] # (age, balance, withdrawals)

    for year in range(age, 110):
        tax = 0
        if year < retirement_age:
            tax = calculate_federal_tax(annual_salary)
            decrease = tax / annual_salary
            yearly_contrib = annual_contribution - (annual_contribution * decrease)

            balance += yearly_contrib

        balance *= (1 + annual_growth_rate)

        withdrawal = 0
        if year > retirement_age:
            social_security_income = 0
            if year > 65: # social security age
                social_security_income = annual_social_security
            
            withdrawal = max(annual_retirement_expenses - social_security_income, 0)

            balance -= withdrawal
            balance = round(balance, 2)

        balance_history.append((year, balance, withdrawal, tax))
        # print(f'{year}\n\t{balance}\n\t{withdrawal}\n\t{tax}\n')

        if balance <= 0:
            break

    return balance_history


data_401k = sim_401k(starting_balance=starting_balance, 
                annual_contribution=annual_contributions,
                annual_growth_rate=annual_growth_rate,
                age=age,
                retirement_age=retirement_age,
                annual_retirement_expenses=annual_retirement_expenses,
                annual_social_security=annual_social_security,
                standard_deduction=standard_deduction)

data_roth = sim_roth(starting_balance=starting_balance, 
                annual_salary=annual_salary,
                annual_contribution=annual_contributions,
                annual_growth_rate=annual_growth_rate,
                age=age,
                retirement_age=retirement_age,
                annual_retirement_expenses=annual_retirement_expenses,
                annual_social_security=annual_social_security)

ages_k, balances_k, withdrawals_k, taxes_k = zip(*data_401k) # unzip
ages_roth, balances_roth, withdrawals_roth, taxes_roth = zip(*data_roth) # unzip

# pyplot time :)
plt.figure(figsize=(12, 6))
plt.plot(ages_k, balances_k, label='401(k) Balance', linewidth=2)
plt.plot(ages_k, withdrawals_k, label='401(k) withdrawals', linestyle='--')
plt.plot(ages_k, taxes_k, label='401(k) Tax Paid', linestyle=':')
plt.plot(ages_roth, balances_roth, label='Roth IRA Balance', linewidth=2)
plt.plot(ages_roth, withdrawals_roth, label='Roth IRA withdrawals', linestyle='--')
plt.plot(ages_roth, taxes_roth, label='Roth IRA Tax Paid', linestyle=':')
plt.title("401(k) vs Roth IRA Balance and withdrawals Over Time")
plt.xlabel("Age")
plt.ylabel("Dollars ($)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('out/401k.png')
