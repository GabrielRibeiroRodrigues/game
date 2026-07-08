"""Logging central do jogo — use get_logger(__name__) em vez de print.

Nivel controlavel pela variavel de ambiente CRAZYWORLD_LOG (default INFO).
"""
import logging
import os

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    level_name = os.environ.get("CRAZYWORLD_LOG", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(name)
