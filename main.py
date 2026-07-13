"""Atalho para a CLI do Sentinela — equivale a `python -m sentinela`.

Mantido na raiz por conveniência; a orquestração real vive em
`sentinela.aplicacao.pipeline` e a CLI em `sentinela.__main__`.
"""

from sentinela.__main__ import main

if __name__ == "__main__":
    main()
