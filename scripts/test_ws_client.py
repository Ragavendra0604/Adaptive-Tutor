import asyncio, json
import websockets

async def client():
    uri = "ws://127.0.0.1:8000/v1/ws/chat"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"query":"Explain binary search with example", "user_id":"hari"}))
        while True:
            try:
                msg = await ws.recv()
            except:
                break
            print("MSG:", msg)
            if '"type":"done"' in msg:
                break

asyncio.run(client())
