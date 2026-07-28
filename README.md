<h1 style="color: #0066cc;">🐍 Python asyncio Master Guide & Cheat Sheet</h1>

A comprehensive, all-in-one guide to mastering asynchronous programming in Python (`asyncio`). This single document covers everything from zero-level mental models and sequential vs. concurrent execution to advanced APIs (`TaskGroup`, `timeout`, `ExceptionGroup`, and garbage collection traps).

---

<h2 style="color: #0066cc;">📌 Table of Contents</h2>

1. [Mental Model: The Office Worker Analogy](#1-mental-model-the-office-worker-analogy)
2. [Sequential vs Concurrent Execution](#2-sequential-vs-concurrent-execution)
3. [The 3 Types of Awaitables](#3-the-3-types-of-awaitables)
4. [Creating Tasks & The Garbage Collection Trap](#4-creating-tasks--the-garbage-collection-trap)
5. [Structured Concurrency: TaskGroup](#5-structured-concurrency-taskgroup)
6. [Managing Timeouts](#6-managing-timeouts)
7. [Running Blocking Code with to_thread](#7-running-blocking-code-with-to_thread)
8. [Task Object Inspection & Cancellation](#8-task-object-inspection--cancellation)
9. [Summary Cheat Sheet](#9-summary-cheat-sheet)

---

<h2 style="color: #0066cc;">1. Mental Model: The Office Worker Analogy</h2>

Think of your computer's CPU core as a **single office worker** sitting at a desk:

* **Synchronous (Normal Code):** The worker orders a pizza and stands staring at the phone for 30 minutes doing zero other work until it arrives.
* **Asynchronous (`asyncio`):** The worker orders a pizza, sets a timer, and immediately goes back to filing invoices while waiting.

> [!NOTE]
> `asyncio` does not make heavy math run faster. It stops your code from sitting idle while waiting for external I/O (network requests, database queries, file reading).

---

<h2 style="color: #0066cc;">2. Sequential vs Concurrent Execution</h2>

> <h3 style="color: #0066cc;">1. Sequential Version (Slow: 1s + 2s = 3s)</h3>
>
> `await` pauses execution until that specific coroutine is 100% finished before moving to the next line.
>
> ```python
> import asyncio
> import time
>
> async def say_after(delay, what):
>     await asyncio.sleep(delay)
>     print(what)
>
> async def main():
>     print(f"Started at {time.strftime('%X')}")
>     await say_after(1, 'hello')
>     await say_after(2, 'world')
>     print(f"Finished at {time.strftime('%X')}") # Takes 3 seconds total
>
> asyncio.run(main())
> ```

> <h3 style="color: #0066cc;">2. Concurrent Version (Fast: max(1s, 2s) = 2s)</h3>
>
> `asyncio.create_task()` schedules coroutines to run simultaneously in the background.
>
> ```python
> async def main():
>     print(f"Started at {time.strftime('%X')}")
>     
>     # Schedule both tasks to run concurrently in the background
>     task1 = asyncio.create_task(say_after(1, 'hello'))
>     task2 = asyncio.create_task(say_after(2, 'world'))
>
>     # Wait for both tasks to complete
>     await task1
>     await task2
>     
>     print(f"Finished at {time.strftime('%X')}") # Takes 2 seconds total
>
> asyncio.run(main())
> ```

---

<h2 style="color: #0066cc;">3. The 3 Types of Awaitables</h2>

An **awaitable** is any object that can be used in an `await` expression.

              ┌──────────────────────────────┐
              │       Awaitable Objects      │
              └──────────────┬───────────────┘
                             │
     ┌───────────────────────┼────────────────────────┐
     ▼                       ▼                        ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐│  Coroutines  │        │    Tasks     │        │   Futures    ││ (Your Code)  │        │ (Background) │        │ (Low-Level)  │└──────────────┘        └──────────────┘        └──────────────┘
> <h3 style="color: #0066cc;">1. Coroutines</h3>
>
> Functions declared with `async def`. Calling a coroutine function returns a **coroutine object**, but it **will not run** until you explicitly `await` it.
>
> ```python
> async def nested():
>     return 42
>
> async def main():
>     nested()             # ⚠️ RuntimeWarning! Doesn't execute.
>     res = await nested() # ✅ Executes and returns 42.
> ```

> <h3 style="color: #0066cc;">2. Tasks</h3>
>
> Coroutines wrapped by `asyncio.create_task()` or `TaskGroup`. They are scheduled to execute immediately in the background on the event loop.

> <h3 style="color: #0066cc;">3. Futures</h3>
>
> Low-level placeholders representing a result that hasn't arrived yet (e.g., a claim ticket at dry cleaners). Used mainly by internal libraries or thread executors.

---

<h2 style="color: #0066cc;">4. Creating Tasks & The Garbage Collection Trap</h2>

When creating background tasks without awaiting them immediately, you **must store a strong reference** to them. Otherwise, Python's Garbage Collector (GC) may destroy them mid-execution.

> [!NOTE]
> Always maintain strong references to running background tasks so Python's Garbage Collector doesn't delete them mid-execution!

> <h3 style="color: #0066cc;">❌ 1. The Disappearing Task Bug</h3>
>
> ```python
> # DANGEROUS: Task isn't stored anywhere. GC may collect it before it completes!
> asyncio.create_task(some_coro())
> ```

> <h3 style="color: #0066cc;">✅ 2. The Safe Pattern (Strong Reference Set)</h3>
>
> ```python
> background_tasks = set()
>
> for i in range(10):
>     task = asyncio.create_task(some_coro(i))
>     
>     # 1. Add to set (creates a strong reference)
>     background_tasks.add(task)
>     
>     # 2. Auto-remove from set when done
>     task.add_done_callback(background_tasks.discard)
> ```

---

<h2 style="color: #0066cc;">5. Structured Concurrency: TaskGroup</h2>

Introduced in **Python 3.11+**, `asyncio.TaskGroup` is the recommended, safest way to run concurrent tasks.

<h3 style="color: #0066cc;">Key Features</h3>

* **Implicit Await:** Automatically waits for all enclosed tasks when exiting the `async with` block.
* **Fail-Fast Safety:** If any child task fails, all other running tasks in the group are **immediately canceled**.
* **Exception Grouping:** Errors are caught and combined into an `ExceptionGroup`.

> <h3 style="color: #0066cc;">1. Basic TaskGroup Execution</h3>
>
> ```python
> import asyncio
>
> async def job(task_id, sleep_time):
>     await asyncio.sleep(sleep_time)
>     print(f"Task {task_id} completed")
>     return f"Result {task_id}"
>
> async def main():
>     async with asyncio.TaskGroup() as tg:
>         task1 = tg.create_task(job(1, 1.0))
>         task2 = tg.create_task(job(2, 0.5))
>
>     # Reaches here ONLY after both tasks finish
>     print(f"Outputs: {task1.result()}, {task2.result()}")
>
> asyncio.run(main())
> ```

> <h3 style="color: #0066cc;">2. Force-Terminating a TaskGroup</h3>
>
> To shut down a `TaskGroup` early, trigger a custom exception inside it:
>
> ```python
> class TerminateGroup(Exception):
>     pass
>
> async def force_stop():
>     raise TerminateGroup()
>
> async def main():
>     try:
>         async with asyncio.TaskGroup() as group:
>             group.create_task(job(1, 0.5))
>             group.create_task(job(2, 5.0)) # Long running
>             
>             await asyncio.sleep(1.0)
>             group.create_task(force_stop()) # Kills remaining tasks
>     except* TerminateGroup:
>         pass # Handle or suppress the group termination
> ```

---

<h2 style="color: #0066cc;">6. Managing Timeouts</h2>

> <h3 style="color: #0066cc;">1. Modern Way: asyncio.timeout() (Python 3.11+)</h3>
>
> Wraps async blocks with a strict deadline. Raises standard `TimeoutError` if exceeded.
>
> ```python
> async def main():
>     try:
>         async with asyncio.timeout(2.0): # 2-second limit
>             await long_network_request()
>     except TimeoutError:
>         print("Request timed out and was safely cancelled!")
> ```

> <h3 style="color: #0066cc;">2. Legacy / Single-Awaitable: asyncio.wait_for()</h3>
>
> ```python
> try:
>     result = await asyncio.wait_for(long_network_request(), timeout=2.0)
> except TimeoutError:
>     print("Timed out!")
> ```

---

<h2 style="color: #0066cc;">7. Running Blocking Code with to_thread</h2>

Standard synchronous functions (like `time.sleep()`, file operations, or heavy math) **block the single event loop thread** and freeze the entire program.

Use `asyncio.to_thread()` to offload blocking I/O calls to a separate OS thread:

```python
import time
import asyncio

def blocking_io():
    time.sleep(2) # Normal blocking code
    return "File content"

async def main():
    # Runs blocking_io in a separate thread without freezing the event loop
    result = await asyncio.to_thread(blocking_io)
    print(result)

asyncio.run(main())
Every Task instance exposes helpful control and inspection methods:
---
MethodDescription
1.task.done()Returns True if the task is finished, canceled, or raised an exception.
2.task.result()Returns the return value of the wrapped coroutine.
3.task.exception()Returns the exception raised by the task (if any).
4.task.cancel(msg=None)Requests task cancellation on the next event loop iteration.
5.task.cancelled()Returns True if the task was successfully canceled.
6.task.set_name("name")Assigns a custom name to the task for easier debugging.
---
async def cancelable_worker():
    try:
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print("Cleanup work before exiting...")
        raise # Re-raise to ensure cancellation propagates cleanly

---
                          ┌──────────────────────────┐
                          │   What are you doing?    │
                          └────────────┬─────────────┘
                                       │
      ┌────────────────────────────────┼────────────────────────────────┐
      ▼                                ▼                                ▼
┌───────────┐                    ┌───────────┐                    ┌───────────┐
│ Regular   │                    │ Running   │                    │ Slow /    │
│  Async    │                    │  Multiple │                    │ Blocking  │
│  Waiting  │                    │   Tasks   │                    │   Work    │
└─────┬─────┘                    └─────┬─────┘                    └─────┬─────┘
      │                                │                                │
      ▼                                ▼                                ▼
Use `await`                       Use `TaskGroup`                  Use `to_thread()`
& `sleep()`                       or `gather()`                    so loop doesn't freeze
---
Single Async Call: await my_coroutine()
Multiple Background Tasks (Safe): async with asyncio.TaskGroup() as tg:
Time Limits: async with asyncio.timeout(seconds):
Blocking I/O or Legacy Functions: await asyncio.to_thread(blocking_func)
Yield Control Briefly: await asyncio.sleep(0)