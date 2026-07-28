# genai-llmops-roadmap
# 🐍 Python asyncio Mastery & Cheat Sheet

A beginner-to-advanced, comprehensive guide to mastering asynchronous programming in Python (`asyncio`). Covers everything from fundamental mental models to modern Python 3.11+ structured concurrency APIs (`TaskGroup`, `timeout`, `ExceptionGroup`).

---

## 📌 Table of Contents
1. [Mental Model: The Office Worker Analogy](#1-mental-model-the-office-worker-analogy)
2. [Sequential vs Concurrent Execution](#2-sequential-vs-concurrent-execution)
3. [The 3 Types of Awaitables](#3-the-3-types-of-awaitables)
4. [Creating Tasks & The Garbage Collection Bug](#4-creating-tasks--the-garbage-collection-bug)
5. [Structured Concurrency: TaskGroup](#5-structured-concurrency-taskgroup)
6. [Managing Timeouts](#6-managing-timeouts)
7. [Running Blocking Code with to_thread](#7-running-blocking-code-with-to_thread)
8. [Task Object Inspection & Cancellation](#8-task-object-inspection--cancellation)
9. [Summary Cheat Sheet](#9-summary-cheat-sheet)

---

## 1. Mental Model: The Office Worker Analogy

Think of your computer's CPU core as a **single office worker** sitting at a desk:

* **Synchronous (Normal Code):** The worker orders a pizza and stands by the phone for 30 minutes doing zero other work until it arrives.
* **Asynchronous (`asyncio`):** The worker orders a pizza, sets a timer, and immediately goes back to filing invoices while waiting.

> **Key Rule:** `asyncio` does not make heavy math run faster. It stops your code from sitting idle while waiting for external I/O (network requests, database queries, file reading).

---

## 2. Sequential vs Concurrent Execution

### Sequential Version (Slow: 1s + 2s = 3s)
`await` pauses execution until that specific coroutine is 100% finished before moving to the next line.

```python
import asyncio
import time

async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

async def main():
    print(f"Started at {time.strftime('%X')}")
    await say_after(1, 'hello')
    await say_after(2, 'world')
    print(f"Finished at {time.strftime('%X')}") # Takes 3 seconds total

asyncio.run(main())
Concurrent Version (Fast: max(1s, 2s) = 2s)asyncio.create_task() schedules coroutines to run simultaneously in the background.Pythonasync def main():
    print(f"Started at {time.strftime('%X')}")
    
    # Schedule both tasks to run concurrently in the background
    task1 = asyncio.create_task(say_after(1, 'hello'))
    task2 = asyncio.create_task(say_after(2, 'world'))

    # Wait for both tasks to complete
    await task1
    await task2
    
    print(f"Finished at {time.strftime('%X')}") # Takes 2 seconds total

asyncio.run(main())
3. The 3 Types of AwaitablesAn awaitable is any object that can be used in an await expression.                  ┌──────────────────────────────┐
                  │       Awaitable Objects      │
                  └──────────────┬───────────────┘
                                 │
         ┌───────────────────────┼────────────────────────┐
         ▼                       ▼                        ▼
  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
  │  Coroutines  │        │    Tasks     │        │   Futures    │
  │ (Your Code)  │        │ (Background) │        │ (Low-Level)  │
  └──────────────┘        └──────────────┘        └──────────────┘
1. CoroutinesFunctions declared with async def. Calling a coroutine function returns a coroutine object, but it will not run until you explicitly await it.Pythonasync def nested():
    return 42

async def main():
    nested()        # ⚠️ RuntimeWarning! Doesn't execute.
    res = await nested() # ✅ Executes and returns 42.
2. TasksCoroutines wrapped by asyncio.create_task() or TaskGroup. They are scheduled to execute immediately in the background on the event loop.3. FuturesLow-level placeholders representing a result that hasn't arrived yet (e.g., a claim ticket at dry cleaners). Used mainly by internal libraries or thread executors.4. Creating Tasks & The Garbage Collection BugWhen creating background tasks without awaiting them immediately, you must store a strong reference to them. Otherwise, Python's Garbage Collector (GC) may destroy them mid-execution.❌ The Disappearing Task BugPython# DANGEROUS: Task isn't stored anywhere. GC may collect it before it completes!
asyncio.create_task(some_coro())
✅ The Safe Pattern (Strong Reference Set)Pythonbackground_tasks = set()

for i in range(10):
    task = asyncio.create_task(some_coro(i))
    
    # 1. Add to set (creates a strong reference)
    background_tasks.add(task)
    
    # 2. Auto-remove from set when done
    task.add_done_callback(background_tasks.discard)
5. Structured Concurrency: TaskGroupIntroduced in Python 3.11+, asyncio.TaskGroup is the recommended, safest way to run concurrent tasks.FeaturesImplicit Await: Automatically waits for all enclosed tasks when exiting the async with block.Fail-Fast Safety: If any child task fails, all other running tasks in the group are immediately canceled.Exception Grouping: Errors are caught and combined into an ExceptionGroup.Pythonimport asyncio

async def job(task_id, sleep_time):
    await asyncio.sleep(sleep_time)
    print(f"Task {task_id} completed")
    return f"Result {task_id}"

async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(job(1, 1.0))
        task2 = tg.create_task(job(2, 0.5))

    # Reaches here ONLY after both tasks finish
    print(f"Outputs: {task1.result()}, {task2.result()}")

asyncio.run(main())
Force-Terminating a TaskGroupTo shut down a TaskGroup early, trigger a custom exception inside it:Pythonclass TerminateGroup(Exception):
    pass

async def force_stop():
    raise TerminateGroup()

async def main():
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(job(1, 0.5))
            group.create_task(job(2, 5.0)) # Long running
            
            await asyncio.sleep(1.0)
            group.create_task(force_stop()) # Kills remaining tasks
    except* TerminateGroup:
        pass # Handle or suppress the group termination
6. Managing TimeoutsModern Way: asyncio.timeout() (Python 3.11+)Wraps async blocks with a strict deadline. Raises standard TimeoutError if exceeded.Pythonasync def main():
    try:
        async with asyncio.timeout(2.0): # 2-second limit
            await long_network_request()
    except TimeoutError:
        print("Request timed out and was safely cancelled!")
Legacy / Single-Awaitable: asyncio.wait_for()Pythontry:
    result = await asyncio.wait_for(long_network_request(), timeout=2.0)
except TimeoutError:
    print("Timed out!")
7. Running Blocking Code with to_threadStandard synchronous functions (like time.sleep(), file operations, or heavy math) block the single event loop thread and freeze the entire program.Use asyncio.to_thread() to offload blocking I/O calls to a separate OS thread:Pythonimport time
import asyncio

def blocking_io():
    time.sleep(2) # Normal blocking code
    return "File content"

async def main():
    # Runs blocking_io in a separate thread without freezing the event loop
    result = await asyncio.to_thread(blocking_io)
    print(result)

asyncio.run(main())
8. Task Object Inspection & CancellationEvery Task instance exposes helpful control and inspection methods:MethodDescriptiontask.done()Returns True if the task is finished, canceled, or raised an exception.task.result()Returns the return value of the wrapped coroutine.task.exception()Returns the exception raised by the task (if any).task.cancel(msg=None)Requests task cancellation on the next event loop iteration.task.cancelled()Returns True if the task was successfully canceled.task.set_name("name")Assigns a custom name to the task for easier debugging.Handling Intercepted CancellationPythonasync def cancelable_worker():
    try:
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print("Cleanup work before exiting...")
        raise # Re-raise to ensure cancellation propagates cleanly
9. Summary Cheat Sheet                          ┌──────────────────────────┐
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
Single Async Call: await my_coroutine()Multiple Background Tasks (Safe): async with asyncio.TaskGroup() as tg:Time Limits: async with asyncio.timeout(seconds):Blocking I/O or Legacy Functions: await asyncio.to_thread(blocking_func)Yield Control Briefly: await asyncio.sleep(0)