import os

# Evita que qualquer import indireto de pygame tente abrir janela/audio
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
