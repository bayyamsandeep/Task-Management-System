#!/bin/bash
echo ">>> Forcing correct typing_extensions import..."
pip install --upgrade --force-reinstall typing_extensions
export PYTHONPATH=$(python -c 'import site; print(site.getsitepackages()[0])'):$PYTHONPATH
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
