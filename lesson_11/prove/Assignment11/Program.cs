using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;

namespace assignment11;

public class Assignment11
{
    private const long START_NUMBER = 10_000_000_000;
    private const int RANGE_COUNT = 1_000_000;
    private const int DEFAULT_WORKER_COUNT = 10;

    private static bool IsPrime(long n)
    {
        if (n <= 3) return n > 1;
        if (n % 2 == 0 || n % 3 == 0) return false;

        for (long i = 5; i * i <= n; i += 6)
        {
            if (n % i == 0 || n % (i + 2) == 0)
                return false;
        }
        return true;
    }

    public static void Main(string[] args)
    {
        var workerCount = DEFAULT_WORKER_COUNT;
        var quiet = false;

        foreach (var arg in args)
        {
            if (arg.Equals("--quiet", StringComparison.OrdinalIgnoreCase) || arg.Equals("-q", StringComparison.OrdinalIgnoreCase))
            {
                quiet = true;
                continue;
            }

            if (int.TryParse(arg, out var parsed) && parsed > 0)
            {
                workerCount = parsed;
            }
        }

        var numbersProcessed = 0;
        var primeCount = 0;

        Console.WriteLine(quiet ? "Prime search running (quiet mode)..." : "Prime numbers found:");

        using var numberQueue = new BlockingCollection<long>(new ConcurrentQueue<long>());
        var consoleLock = new object();
        var stopwatch = Stopwatch.StartNew();

        var workers = new List<Thread>(workerCount);

        void Worker()
        {
            foreach (var value in numberQueue.GetConsumingEnumerable())
            {
                var isPrime = IsPrime(value);
                Interlocked.Increment(ref numbersProcessed);

                if (!isPrime)
                {
                    continue;
                }

                Interlocked.Increment(ref primeCount);
                if (!quiet)
                {
                    lock (consoleLock)
                    {
                        Console.Write($"{value}, ");
                    }
                }
            }
        }

        for (var i = 0; i < workerCount; i++)
        {
            var thread = new Thread(Worker)
            {
                IsBackground = true
            };
            workers.Add(thread);
            thread.Start();
        }

        for (long number = START_NUMBER; number < START_NUMBER + RANGE_COUNT; number++)
        {
            numberQueue.Add(number);
        }

        numberQueue.CompleteAdding();

        foreach (var worker in workers)
        {
            worker.Join();
        }

        stopwatch.Stop();

        Console.WriteLine();
        Console.WriteLine();

        Console.WriteLine($"Numbers processed = {numbersProcessed}");
        Console.WriteLine($"Primes found      = {primeCount}");
        Console.WriteLine($"Total time        = {stopwatch.Elapsed}");
    }
}
