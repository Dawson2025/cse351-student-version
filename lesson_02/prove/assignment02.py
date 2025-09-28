"""
Course    : CSE 351
Assignment: 02
Student   : Dawson Packer

Instructions:
    - review instructions in the course
"""

# Don't import any other packages for this assignment
import os
import random
import threading
from money import *
from cse351 import *

# ---------------------------------------------------------------------------
def main(): 

    print('\nATM Processing Program:')
    print('=======================\n')

    create_data_files_if_needed()

    # Load ATM data files
    data_files = get_filenames('data_files')
    # print(data_files)
    
    log = Log(show_terminal=True)
    log.start_timer()

    bank = Bank()

    threads = []
    for filename in data_files:
        reader = ATM_Reader(filename, bank)
        reader.start()
        threads.append(reader)

    for reader in threads:
        reader.join()

    test_balances(bank)

    log.stop_timer('Total time')


# ===========================================================================
class ATM_Reader(threading.Thread):
    """Thread that processes a single ATM transaction file."""

    def __init__(self, filename, bank):
        super().__init__()
        self.filename = filename
        self.bank = bank

    def run(self):
        with open(self.filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = [part.strip() for part in line.split(',')]
                if len(parts) != 3:
                    continue

                account_number = int(parts[0])
                transaction_type = parts[1].lower()
                amount = Money(parts[2])

                if transaction_type == 'd':
                    self.bank.deposit(account_number, amount)
                elif transaction_type == 'w':
                    self.bank.withdraw(account_number, amount)


# ===========================================================================
class Account:
    """Represents a single bank account with a thread-safe balance."""

    def __init__(self):
        self.balance = Money('0.00')
        self._lock = threading.Lock()

    def deposit(self, amount):
        if not isinstance(amount, Money):
            amount = Money(str(amount))
        with self._lock:
            self.balance.add(amount)

    def withdraw(self, amount):
        if not isinstance(amount, Money):
            amount = Money(str(amount))
        with self._lock:
            self.balance.sub(amount)

    def get_balance(self):
        with self._lock:
            return Money(self.balance.digits)


# ===========================================================================
class Bank:
    """Manages accounts and coordinates thread-safe transactions."""

    def __init__(self):
        self.accounts = {}
        self._accounts_lock = threading.Lock()

    def _get_or_create_account(self, account_number):
        account_number = int(account_number)
        with self._accounts_lock:
            account = self.accounts.get(account_number)
            if account is None:
                account = Account()
                self.accounts[account_number] = account
        return account

    def deposit(self, account_number, amount):
        account = self._get_or_create_account(account_number)
        account.deposit(amount)

    def withdraw(self, account_number, amount):
        account = self._get_or_create_account(account_number)
        account.withdraw(amount)

    def get_balance(self, account_number):
        with self._accounts_lock:
            account = self.accounts.get(int(account_number))
        if account is None:
            return Money('0.00')
        return account.get_balance()


# ---------------------------------------------------------------------------

def get_filenames(folder):
    """ Don't Change """
    filenames = []
    for filename in os.listdir(folder):
        if filename.endswith(".dat"):
            filenames.append(os.path.join(folder, filename))
    return filenames

# ---------------------------------------------------------------------------
def create_data_files_if_needed():
    """ Don't Change """
    ATMS = 10
    ACCOUNTS = 20
    TRANSACTIONS = 250000

    sub_dir = 'data_files'
    if os.path.exists(sub_dir):
        return

    print('Creating Data Files: (Only runs once)')
    os.makedirs(sub_dir)

    random.seed(102030)
    mean = 100.00
    std_dev = 50.00

    for atm in range(1, ATMS + 1):
        filename = f'{sub_dir}/atm-{atm:02d}.dat'
        print(f'- {filename}')
        with open(filename, 'w') as f:
            f.write(f'# Atm transactions from machine {atm:02d}\n')
            f.write('# format: account number, type, amount\n')

            # create random transactions
            for i in range(TRANSACTIONS):
                account = random.randint(1, ACCOUNTS)
                trans_type = 'd' if random.randint(0, 1) == 0 else 'w'
                amount = f'{(random.gauss(mean, std_dev)):0.2f}'
                f.write(f'{account},{trans_type},{amount}\n')

    print()

# ---------------------------------------------------------------------------
def test_balances(bank):
    """ Don't Change """

    # Verify balances for each account
    correct_results = (
        (1, '59362.93'),
        (2, '11988.60'),
        (3, '35982.34'),
        (4, '-22474.29'),
        (5, '11998.99'),
        (6, '-42110.72'),
        (7, '-3038.78'),
        (8, '18118.83'),
        (9, '35529.50'),
        (10, '2722.01'),
        (11, '11194.88'),
        (12, '-37512.97'),
        (13, '-21252.47'),
        (14, '41287.06'),
        (15, '7766.52'),
        (16, '-26820.11'),
        (17, '15792.78'),
        (18, '-12626.83'),
        (19, '-59303.54'),
        (20, '-47460.38'),
    )

    wrong = False
    for account_number, balance in correct_results:
        bal = bank.get_balance(account_number)
        print(f'{account_number:02d}: balance = {bal}')
        if Money(balance) != bal:
            wrong = True
            print(f'Wrong Balance: account = {account_number}, expected = {balance}, actual = {bal}')

    if not wrong:
        print('\nAll account balances are correct')




if __name__ == "__main__":
    main()


