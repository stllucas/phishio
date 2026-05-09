"""Script otimizado para iniciar a API em testes de carga no Windows."""
import sys
import os
import asyncio
import uvicorn

RUNTIME_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "runtime")
sys.path.insert(0, RUNTIME_DIR)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    print("=====================================================")
    print(" INICIANDO PHISHIO API - MODO DE TESTE DE CARGA (PROACTOR)")
    print("=====================================================")

    uvicorn.run("main:app", host="127.0.0.1", port=8000,
                loop="asyncio", log_level="info")
