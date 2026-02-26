# Python 샘플 앱

이 프로젝트는 간단한 Python 샘플 애플리케이션입니다. 가상환경은 `.venv`를 사용합니다.

Windows PowerShell에서 빠르게 시작하려면:

```powershell
cd python
python -m venv .venv
. .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install uv
python main.py
```

주의: 여기서 패키지 관리자로 지정된 `uv`는 사용자의 지침에 따른 이름입니다. 실제로는 설치하려는 패키지 이름을 사용하세요.
한국어 안내서

이 프로젝트는 로컬 가상환경 `.venv`를 사용합니다.

설치 및 실행 (Windows PowerShell):

```powershell
# 1. python 디렉터리로 이동
cd python

# 2. 가상환경 생성
python -m venv .venv

# 3. 가상환경 활성화
. .\.venv\Scripts\Activate.ps1

# 4. pip 업데이트 및 'uv' 설치 (사용자 요청대로 'uv' 사용)
python -m pip install --upgrade pip
pip install uv

# 5. 샘플 앱 실행
python main.py
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

`uv`가 실제로 어떤 도구인지 확인하려면 Context7 문서를 참고하세요. (별도 명령으로 문서 조회 필요)

참고: PowerShell 실행 정책 때문에 스크립트 실행이 차단될 수 있습니다. 그 경우 관리자 권한으로 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`를 실행하세요.
