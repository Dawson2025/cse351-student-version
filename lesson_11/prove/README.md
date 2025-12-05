# Lesson 11: Prime Finder

## Run
```bash
# Default 10 workers, quiet output
dotnet run --configuration Release --project Assignment11 -- --quiet

# Custom workers + verbose primes
dotnet run --configuration Release --project Assignment11 -- 12
```

Flags/args:
- `--quiet` or `-q` suppresses per-prime printing.
- First numeric arg sets worker count (defaults to 10).

## Test prime count
```bash
./test_prime_count.sh          # defaults to 10 workers
WORKERS=12 ./test_prime_count.sh
```
Passes when primes found = `43427` for the 1,000,000-number range starting at 10,000,000,000.
