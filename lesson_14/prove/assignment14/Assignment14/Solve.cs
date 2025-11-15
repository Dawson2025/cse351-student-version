using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Threading;
using Newtonsoft.Json.Linq;

namespace Assignment14;

public static class Solve
{
    private static readonly HttpClient HttpClient;
    private static readonly SemaphoreSlim HttpSemaphore = new(50);
    public const string TopApiUrl = "http://127.0.0.1:8123";

    static Solve()
    {
        var handler = new SocketsHttpHandler
        {
            MaxConnectionsPerServer = 256,
            PooledConnectionLifetime = TimeSpan.FromMinutes(5),
            AutomaticDecompression = DecompressionMethods.All
        };

        HttpClient = new HttpClient(handler)
        {
            Timeout = TimeSpan.FromSeconds(180),
            DefaultRequestVersion = HttpVersion.Version11
        };
    }

    // This function retrieves JSON from the server
    public static async Task<JObject?> GetDataFromServerAsync(string url)
    {
        await HttpSemaphore.WaitAsync();
        try
        {
            var jsonString = await HttpClient.GetStringAsync(url);
            return JObject.Parse(jsonString);
        }
        catch (HttpRequestException e)
        {
            Console.WriteLine($"Error fetching data from {url}: {e.Message}");
            return null;
        }
        finally
        {
            HttpSemaphore.Release();
        }
    }

    // This function takes in a person ID and retrieves a Person object
    // Hint: It can be used in a "new List<Task<Person?>>()" list
    private static async Task<Person?> FetchPersonAsync(long personId)
    {
        var personJson = await Solve.GetDataFromServerAsync($"{Solve.TopApiUrl}/person/{personId}");
        return personJson != null ? Person.FromJson(personJson.ToString()) : null;
    }

    // This function takes in a family ID and retrieves a Family object
    // Hint: It can be used in a "new List<Task<Family?>>()" list
    private static async Task<Family?> FetchFamilyAsync(long familyId)
    {
        var familyJson = await Solve.GetDataFromServerAsync($"{Solve.TopApiUrl}/family/{familyId}");
        return familyJson != null ? Family.FromJson(familyJson.ToString()) : null;
    }
    
    // =======================================================================================================
    public static async Task<bool> DepthFS(long familyId, Tree tree)
    {
        if (familyId == 0)
        {
            return false;
        }

        var visitedFamilies = new ConcurrentDictionary<long, bool>();
        var personCache = new ConcurrentDictionary<long, Task<Person?>>();
        var familyCache = new ConcurrentDictionary<long, Task<Family?>>();
        visitedFamilies.TryAdd(familyId, true);

        var stack = new ConcurrentStack<long>();
        var signal = new SemaphoreSlim(0);
        var pending = 0;
        using var cts = new CancellationTokenSource();

        void Push(long id)
        {
            stack.Push(id);
            Interlocked.Increment(ref pending);
            signal.Release();
        }

        Push(familyId);

        var workerCount = Math.Max(4, Environment.ProcessorCount * 8);
        var workers = new List<Task>(workerCount);

        for (var i = 0; i < workerCount; i++)
        {
            workers.Add(Task.Run(async () =>
            {
                try
                {
                    while (true)
                    {
                        await signal.WaitAsync(cts.Token);

                        if (!stack.TryPop(out var currentId))
                        {
                            continue;
                        }

                        var parents = await ProcessFamilyAsync(currentId, tree, personCache, familyCache);

                        foreach (var parentId in parents)
                        {
                            if (parentId == 0)
                            {
                                continue;
                            }

                            if (visitedFamilies.TryAdd(parentId, true))
                            {
                                Push(parentId);
                            }
                        }

                        if (Interlocked.Decrement(ref pending) == 0)
                        {
                            cts.Cancel();
                            break;
                        }
                    }
                }
                catch (OperationCanceledException)
                {
                    // finished
                }
            }));
        }

        try
        {
            await Task.WhenAll(workers);
        }
        catch (OperationCanceledException)
        {
            // ignore cancellation cascade
        }

        return true;
    }

    // =======================================================================================================
    public static async Task<bool> BreathFS(long famid, Tree tree)
    {
        if (famid == 0)
        {
            return false;
        }

        var visitedFamilies = new ConcurrentDictionary<long, bool>();
        var personCache = new ConcurrentDictionary<long, Task<Person?>>();
        var familyCache = new ConcurrentDictionary<long, Task<Family?>>();
        visitedFamilies.TryAdd(famid, true);

        var queue = new ConcurrentQueue<long>();
        var signal = new SemaphoreSlim(0);
        var pending = 0;
        using var cts = new CancellationTokenSource();

        void Enqueue(long id)
        {
            queue.Enqueue(id);
            Interlocked.Increment(ref pending);
            signal.Release();
        }

        Enqueue(famid);

        var workerCount = Math.Max(4, Environment.ProcessorCount * 8);
        var workers = new List<Task>(workerCount);

        for (var i = 0; i < workerCount; i++)
        {
            workers.Add(Task.Run(async () =>
            {
                try
                {
                    while (true)
                    {
                        await signal.WaitAsync(cts.Token);

                        if (!queue.TryDequeue(out var familyId))
                        {
                            continue;
                        }

                        var parents = await ProcessFamilyAsync(familyId, tree, personCache, familyCache);

                        foreach (var parentId in parents)
                        {
                            if (parentId == 0)
                            {
                                continue;
                            }

                            if (visitedFamilies.TryAdd(parentId, true))
                            {
                                Enqueue(parentId);
                            }
                        }

                        if (Interlocked.Decrement(ref pending) == 0)
                        {
                            cts.Cancel();
                            break;
                        }
                    }
                }
                catch (OperationCanceledException)
                {
                    // finished
                }
            }));
        }

        try
        {
            await Task.WhenAll(workers);
        }
        catch (OperationCanceledException)
        {
            // ignore
        }

        return true;
    }

    private static async Task<List<long>> ProcessFamilyAsync(long familyId, Tree tree, ConcurrentDictionary<long, Task<Person?>> personCache, ConcurrentDictionary<long, Task<Family?>> familyCache)
    {
        var parentIds = new List<long>();
        if (familyId == 0)
        {
            return parentIds;
        }

        var familyTask = familyCache.GetOrAdd(familyId, _ => FetchFamilyAsync(familyId));
        var family = await familyTask;
        if (family == null)
        {
            return parentIds;
        }

        tree.AddFamily(family);

        var personTasks = new List<Task<Person?>>();
        var cachedPeople = new List<Person?>();

        void QueuePerson(long personId)
        {
            if (personId != 0)
            {
                var existing = tree.GetPerson(personId);

                if (existing != null)
                {
                    cachedPeople.Add(existing);
                }
                else
                {
                    var task = personCache.GetOrAdd(personId, _ => FetchPersonAsync(personId));
                    personTasks.Add(task);
                }
            }
        }

        QueuePerson(family.HusbandId);
        QueuePerson(family.WifeId);
        foreach (var childId in family.Children)
        {
            QueuePerson(childId);
        }

        if (personTasks.Count > 0)
        {
            var people = await Task.WhenAll(personTasks);
            foreach (var person in people)
            {
                if (person == null)
                {
                    continue;
                }

                if (!tree.PersonExists(person.Id))
                {
                    tree.AddPerson(person);
                    if (person.ParentId != 0)
                    {
                        familyCache.GetOrAdd(person.ParentId, _ => FetchFamilyAsync(person.ParentId));
                    }
                }
                personCache.TryRemove(person.Id, out _);

                cachedPeople.Add(person);
            }
        }

        foreach (var person in cachedPeople)
        {
            if (person == null)
            {
                continue;
            }

            if ((person.Id == family.HusbandId || person.Id == family.WifeId) && person.ParentId != 0)
            {
                parentIds.Add(person.ParentId);
            }
        }

        return parentIds;
    }
}
