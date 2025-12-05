using System.Collections.Concurrent;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

namespace Assignment14;

public static class Solve
{
    // Tunable knobs for controlling parallelism; adjust if the server is overloaded
    private const int MaxConcurrentRequests = 32;
    private const int MaxBfsWorkers = 16;

    private static readonly HttpClient HttpClient = new()
    {
        Timeout = TimeSpan.FromSeconds(180)
    };
    private static readonly SemaphoreSlim RequestLimiter = new(MaxConcurrentRequests, MaxConcurrentRequests);
    public const string TopApiUrl = "http://127.0.0.1:8123";

    // This function retrieves JSON from the server
    public static async Task<JObject?> GetDataFromServerAsync(string url)
    {
        await RequestLimiter.WaitAsync();
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
            RequestLimiter.Release();
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
        // Note: invalid IDs are zero not null

        if (familyId == 0) return false;

        // A single lock guards Tree mutation because its internal dictionaries
        // are not thread-safe.
        var treeLock = new object();
        var visitedFamilies = new ConcurrentDictionary<long, byte>();

        async Task<Person?> FetchAndAddPerson(long personId)
        {
            if (personId == 0) return null;

            // Check if already loaded
            lock (treeLock)
            {
                var existing = tree.GetPerson(personId);
                if (existing != null) return existing;
            }

            var person = await FetchPersonAsync(personId);
            if (person != null)
            {
                lock (treeLock)
                {
                    if (!tree.PersonExists(person.Id))
                    {
                        tree.AddPerson(person);
                    }
                }
            }
            return person;
        }

        async Task DepthFirstAsync(long famId)
        {
            if (famId == 0) return;
            if (!visitedFamilies.TryAdd(famId, 0)) return; // already processed

            var family = await FetchFamilyAsync(famId);
            if (family == null) return;

            lock (treeLock)
            {
                if (tree.GetFamily(family.Id) == null)
                {
                    tree.AddFamily(family);
                }
            }

            // Fetch all people in this family concurrently
            var personTasks = new List<Task<Person?>>
            {
                FetchAndAddPerson(family.HusbandId),
                FetchAndAddPerson(family.WifeId)
            };
            foreach (var childId in family.Children)
            {
                personTasks.Add(FetchAndAddPerson(childId));
            }

            var people = await Task.WhenAll(personTasks);

            // Recurse into the parents of the spouses (DFS)
            var nextFamilies = new List<long>();
            if (people.Length > 0 && people[0]?.ParentId > 0)
            {
                nextFamilies.Add(people[0]!.ParentId);
            }
            if (people.Length > 1 && people[1]?.ParentId > 0)
            {
                nextFamilies.Add(people[1]!.ParentId);
            }

            var recurseTasks = nextFamilies.Select(DepthFirstAsync).ToList();
            await Task.WhenAll(recurseTasks);
        }

        await DepthFirstAsync(familyId);
        return true;
    }

    // =======================================================================================================
    public static async Task<bool> BreathFS(long famid, Tree tree)
    {
        // Note: invalid IDs are zero not null
        if (famid == 0) return false;

        var treeLock = new object();
        var visitedFamilies = new ConcurrentDictionary<long, byte>();
        var queue = new ConcurrentQueue<long>();
        var queueSignal = new SemaphoreSlim(0);
        int pending = 0;

        void EnqueueFamily(long id)
        {
            if (id == 0) return;
            // Light pre-check to avoid obvious duplicates
            if (visitedFamilies.ContainsKey(id)) return;
            Interlocked.Increment(ref pending);
            queue.Enqueue(id);
            queueSignal.Release();
        }

        EnqueueFamily(famid);

        async Task<Person?> FetchAndAddPerson(long personId)
        {
            if (personId == 0) return null;

            lock (treeLock)
            {
                var existing = tree.GetPerson(personId);
                if (existing != null) return existing;
            }

            var person = await FetchPersonAsync(personId);
            if (person != null)
            {
                lock (treeLock)
                {
                    if (!tree.PersonExists(person.Id))
                    {
                        tree.AddPerson(person);
                    }
                }
            }
            return person;
        }

        async Task<List<long>> ProcessFamily(long familyId)
        {
            var family = await FetchFamilyAsync(familyId);
            if (family == null) return [];

            lock (treeLock)
            {
                if (tree.GetFamily(family.Id) == null)
                {
                    tree.AddFamily(family);
                }
            }

            // Gather all people concurrently
            var tasks = new List<Task<Person?>>
            {
                FetchAndAddPerson(family.HusbandId),
                FetchAndAddPerson(family.WifeId)
            };
            foreach (var child in family.Children)
            {
                tasks.Add(FetchAndAddPerson(child));
            }

            var people = await Task.WhenAll(tasks);

            var parents = new List<long>(2);
            if (people.Length > 0 && people[0]?.ParentId > 0) parents.Add(people[0]!.ParentId);
            if (people.Length > 1 && people[1]?.ParentId > 0) parents.Add(people[1]!.ParentId);

            return parents;
        }

        async Task Worker()
        {
            while (true)
            {
                await queueSignal.WaitAsync();
                if (Volatile.Read(ref pending) == 0)
                {
                    break; // nothing left to do
                }

                if (!queue.TryDequeue(out var familyId))
                {
                    continue;
                }

                if (!visitedFamilies.TryAdd(familyId, 0))
                {
                    if (Interlocked.Decrement(ref pending) == 0)
                    {
                        queueSignal.Release(MaxBfsWorkers);
                    }
                    continue;
                }

                var parents = await ProcessFamily(familyId);
                foreach (var parentId in parents)
                {
                    if (parentId == 0) continue;
                    EnqueueFamily(parentId);
                }

                if (Interlocked.Decrement(ref pending) == 0)
                {
                    // Wake any waiting workers so they can exit
                    queueSignal.Release(MaxBfsWorkers);
                }
            }
        }

        var workers = Enumerable.Range(0, MaxBfsWorkers)
            .Select(_ => Task.Run(Worker))
            .ToArray();

        await Task.WhenAll(workers);

        return true;
    }
}
