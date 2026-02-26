# PowerShell 스크립트: 가상환경 생성 및 `uv` 설치
python -m venv .venv
. .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install uv
