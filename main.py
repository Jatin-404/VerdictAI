# main.py
import subprocess
import sys
import os

services = [
    {
        "name": "gateway",
        "module": "app.services.gateway:app",
        "port": 8000
    },
    {
        "name": "chunker",
        "module": "app.services.chunker:app",
        "port": 8001
    },
    {
        "name": "embed",
        "module": "app.services.embed:app",
        "port": 8002
    },
    {
        "name": "store",
        "module": "app.services.store:app",
        "port": 8003
    },
    {
        "name": "search",
        "module": "app.services.search:app",
        "port": 8004
    },
]

def run():
    processes = []

    for service in services:
        print(f"Starting {service['name']} on port {service['port']}...")
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            service["module"],
            "--host", "0.0.0.0",
            "--port", str(service["port"]),
            "--reload"
        ])
        processes.append((service["name"], process))

    print("\n✅ All services started!")
    print("Gateway:  http://localhost:8000")
    print("Chunker:  http://localhost:8001")
    print("Embed:    http://localhost:8002")
    print("Store:    http://localhost:8003")
    print("Search:   http://localhost:8004")
    print("\nPress Ctrl+C to stop all services\n")

    try:
        # wait — keep main process alive
        for name, process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\nShutting down all services...")
        for name, process in processes:
            process.terminate()
            print(f"  stopped {name}")
        print("All services stopped.")

if __name__ == "__main__":
    run()