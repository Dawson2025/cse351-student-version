using System.Diagnostics;
using System.Collections.Concurrent;

namespace assignment11;

public class Assignment11
{
    private const long START_NUMBER = 10_000_000_000;
    private const int RANGE_COUNT = 1_000_000;
    private const int NUM_WORKERS = 10;

    // Thread-safe queue for numbers to process
    private static ConcurrentQueue<long> _numberQueue = new ConcurrentQueue<long>();
    
    // Lock for synchronized console output (prevents mixed-up numbers)
    private static readonly object _consoleLock = new object();
    
    // Thread-safe counter for primes found
    private static int _primeCount = 0;
    
    // Flag to signal workers that production is complete
    private static volatile bool _doneProducing = false;

    private static bool IsPrime(long n)
    {
        if (n <= 3) return n > 1;
        if (n % 2 == 0 || n % 3 == 0) return false;

        for (long i = 5; i * i <= n; i = i + 6)
        {
            if (n % i == 0 || n % (i + 2) == 0)
                return false;
        }
        return true;
    }

    private static void WorkerThread()
    {
        while (true)
        {
            // Try to get a number from the queue
            if (_numberQueue.TryDequeue(out long number))
            {
                // Check if the number is prime
                if (IsPrime(number))
                {
                    // Synchronize console output to prevent mixed-up numbers
                    lock (_consoleLock)
                    {
                        Console.Write($"{number}, ");
                    }
                    // Atomically increment the prime count
                    Interlocked.Increment(ref _primeCount);
                }
            }
            else if (_doneProducing)
            {
                // Queue is empty and production is done - exit the worker
                break;
            }
            else
            {
                // Queue is temporarily empty but production continues - brief wait
                Thread.Sleep(1);
            }
        }
    }

    public static void Main(string[] args)
    {
        Console.WriteLine("Prime numbers found:");

        var stopwatch = Stopwatch.StartNew();

        // Create and start worker threads
        List<Thread> workers = new List<Thread>();
        for (int i = 0; i < NUM_WORKERS; i++)
        {
            Thread worker = new Thread(WorkerThread);
            worker.Name = $"Worker-{i + 1}";
            workers.Add(worker);
            worker.Start();
        }

        // Main thread: Add numbers to the queue
        for (long i = START_NUMBER; i < START_NUMBER + RANGE_COUNT; i++)
        {
            _numberQueue.Enqueue(i);
        }

        // Signal that we're done producing numbers
        _doneProducing = true;

        // Wait for all worker threads to complete
        foreach (Thread worker in workers)
        {
            worker.Join();
        }

        stopwatch.Stop();

        Console.WriteLine(); // New line after all primes are printed
        Console.WriteLine();

        // Should find 43427 primes for range_count = 1000000
        Console.WriteLine($"Numbers processed = {RANGE_COUNT}");
        Console.WriteLine($"Primes found      = {_primeCount}");
        Console.WriteLine($"Total time        = {stopwatch.Elapsed}");
    }
}
