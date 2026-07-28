async def nested():
    return 42
async def main():
    # Starts nested() immediately in the background
    task = asyncio.create_task(nested())

    # You can do other things here while 'task' runs...

    # Wait for the task to finish and get its result
    await task