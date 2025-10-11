"""
Course    : CSE 351
Assignment: 02
Student   : Dawson Packer

Instructions:
    - review instructions in the course
Assessment: 
    - 4: Meets requirements. The test case passed, and the account balances were as they should be. 
      I was able to use all of the threads without failing the test due to race conditions. 
"""

import os
import random
import threading
from money import *
from cse351 import *

# ---------------------------------------------------------------------------

# Define the program entry point when this module runs directly
def main():
    # Print the program header title
    print('\nATM Processing Program:')
    # Print an underline for the header title
    print('=======================\n')

    # Ensure ATM data files exist before attempting to process them
    create_data_files_if_needed()

    # Collect every ATM data filename to be processed
    data_files = get_filenames('data_files')
    # print(data_files)

    # Create a logger that can report timing information to the terminal
    log = Log(show_terminal=True)
    # Start timing the total processing duration
    log.start_timer()

    # Instantiate the bank that will manage all account balances
    bank = Bank()

    # Hold references to all launched ATM reader threads
    threads = []
    # Iterate over each ATM data file to create a corresponding thread
    for filename in data_files:
        # Create a thread dedicated to processing a single ATM file
        reader = ATM_Reader(filename, bank)
        # Start the ATM reader thread so it begins processing immediately
        reader.start()
        # Append the thread reference for later joining
        threads.append(reader)

    # Iterate over every thread that was started
    for reader in threads:
        # Join each thread to wait for completion before continuing
        reader.join()

    # Validate the resulting balances against the expected values
    test_balances(bank)

    # Stop the timer and report the total elapsed time
    log.stop_timer('Total time')


# ===========================================================================

# Define a thread subclass that processes a single ATM transaction file
class ATM_Reader(threading.Thread):
    """Thread that processes a single ATM transaction file."""

    # Initialize the thread with its target filename and the shared bank
    def __init__(self, filename, bank):
        # Initialize the parent threading.Thread class
        super().__init__()
        # Store the ATM data filename this thread will read
        self.filename = filename
        # Store a reference to the shared Bank instance
        self.bank = bank

    # Execute the thread's work when start() is invoked
    def run(self):
        # Open the assigned ATM data file for reading
        with open(self.filename, 'r') as f:
            # Process each line found in the file
            for line in f:
                # Strip whitespace to simplify parsing
                line = line.strip()
                # Skip blank lines and comment lines
                if not line or line.startswith('#'):
                    # Continue with the next line when the current one should be ignored
                    continue

                # Split the transaction line into its components
                parts = [part.strip() for part in line.split(',')]
                # Validate that the line has exactly three parts
                if len(parts) != 3:
                    # Skip malformed transaction lines
                    continue

                # Convert the account identifier into an integer
                account_number = int(parts[0])
                # Normalize the transaction type to lowercase
                transaction_type = parts[1].lower()
                # Create a Money instance to represent the transaction amount
                amount = Money(parts[2])

                # Handle deposit transactions
                if transaction_type == 'd':
                    # Apply the deposit to the appropriate account
                    self.bank.deposit(account_number, amount)
                # Handle withdrawal transactions
                elif transaction_type == 'w':
                    # Apply the withdrawal to the appropriate account
                    self.bank.withdraw(account_number, amount)


# ===========================================================================

# Represent an individual bank account with a thread-safe balance
class Account:
    # Summarize the responsibility of the Account class
    """Represents a single bank account with a thread-safe balance."""

    # Initialize the account with a zero balance and a lock
    def __init__(self):
        # Set the starting balance to zero dollars
        self.balance = Money('0.00')
        # Create a lock to guard balance modifications
        self._lock = threading.Lock()

    # Add funds to the account in a thread-safe manner
    def deposit(self, amount):
        # Convert non-Money inputs into a Money instance
        if not isinstance(amount, Money):
            # Wrap the numeric value in a Money object
            amount = Money(str(amount))
        # Acquire exclusive access while updating the balance
        with self._lock:
            # Add the incoming amount to the balance
            self.balance.add(amount)

    # Remove funds from the account in a thread-safe manner
    def withdraw(self, amount):
        # Convert non-Money inputs into a Money instance
        if not isinstance(amount, Money):
            # Wrap the numeric value in a Money object
            amount = Money(str(amount))
        # Acquire exclusive access while updating the balance
        with self._lock:
            # Subtract the outgoing amount from the balance
            self.balance.sub(amount)

    # Retrieve the current balance without exposing internal references
    def get_balance(self):
        # Acquire the lock to ensure a consistent view of the balance
        with self._lock:
            # Return a new Money object containing the current balance digits
            return Money(self.balance.digits)


# ===========================================================================

# Manage all accounts and coordinate thread-safe transactions
class Bank:
    # Summarize the responsibility of the Bank class
    """Manages accounts and coordinates thread-safe transactions."""

    # Initialize the bank with empty account storage and locking
    def __init__(self):
        # Keep accounts keyed by their account numbers
        self.accounts = {}
        # Guard concurrent modifications to the accounts dictionary
        self._accounts_lock = threading.Lock()

    # Retrieve an existing account or create a new one when necessary
    def _get_or_create_account(self, account_number):
        # Normalize the account number to an integer key
        account_number = int(account_number)
        # Protect account lookup and creation with the dictionary lock
        with self._accounts_lock:
            # Attempt to fetch an existing account
            account = self.accounts.get(account_number)
            # Create a new account if one does not already exist
            if account is None:
                # Instantiate a new Account object for this account number
                account = Account()
                # Store the new account in the dictionary for future use
                self.accounts[account_number] = account
        # Return the located or newly created account
        return account

    # Handle deposits requested by ATM reader threads
    def deposit(self, account_number, amount):
        # Retrieve the account that should receive the deposit
        account = self._get_or_create_account(account_number)
        # Delegate the deposit to the account object
        account.deposit(amount)

    # Handle withdrawals requested by ATM reader threads
    def withdraw(self, account_number, amount):
        # Retrieve the account from which funds should be withdrawn
        account = self._get_or_create_account(account_number)
        # Delegate the withdrawal to the account object
        account.withdraw(amount)

    # Retrieve the current balance for the specified account number
    def get_balance(self, account_number):
        # Protect dictionary access while obtaining the account reference
        with self._accounts_lock:
            # Attempt to retrieve the account from the dictionary
            account = self.accounts.get(int(account_number))
        # Return a zero balance when the account does not exist
        if account is None:
            # Create a Money instance representing zero dollars
            return Money('0.00')
        # Return the account's current balance when it exists
        return account.get_balance()


# ---------------------------------------------------------------------------

# Return a list of .dat filenames from the specified folder
def get_filenames(folder):
    # Honor the assignment requirement not to alter this helper
    """ Don't Change """
    # Initialize an empty list that will store the filenames
    filenames = []
    # Iterate over every entry in the provided folder
    for filename in os.listdir(folder):
        # Add files that end with the .dat extension to the list
        if filename.endswith(".dat"):
            # Append the full path to the qualifying data file
            filenames.append(os.path.join(folder, filename))
    # Return the complete list of data file paths
    return filenames

# ---------------------------------------------------------------------------

# Create ATM data files only when they have not been generated yet
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

            for i in range(TRANSACTIONS):
                account = random.randint(1, ACCOUNTS)
                trans_type = 'd' if random.randint(0, 1) == 0 else 'w'
                amount = f'{(random.gauss(mean, std_dev)):0.2f}'
                f.write(f'{account},{trans_type},{amount}\n')

    print()

# ---------------------------------------------------------------------------

# Verify that all account balances match the expected results
def test_balances(bank):
    """ Don't Change """

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