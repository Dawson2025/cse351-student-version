## Lesson 14 C# server runs (DFS/BFS)

- Server: `FamilyTreeServer` (`dotnet run`), client from `Assignment14/bin/Debug/net8.0/Assignment14.dll`
- Generations: 6
- Runs: 30 (DFS + BFS per run)
- Threshold: 10 seconds
- Results:
  - DFS: 30/30 under 10s (100%), average 4.91s
  - BFS: 30/30 under 10s (100%), average 4.95s

Notes: Concurrency settings used defaults in `Solve.cs` (`MaxConcurrentRequests=32`, `MaxBfsWorkers=16`).***
