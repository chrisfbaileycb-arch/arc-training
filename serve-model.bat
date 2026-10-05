@echo off
setlocal
set CORE=%1
if "%CORE%"=="" set CORE=ornith-9b-cortex
set ROOT=%~dp0
set SRV=%ROOT%runtime\win\llama-server.exe
if /i "%CORE%"=="ornith-9b-cortex" ( set MODEL=%ROOT%models\weights\Ornith-9B-CORTEX-v3-Q4_K_M.gguf & set EXTRA=--temp 0.6 --top-p 0.95 )
if /i "%CORE%"=="mimo-9b-cortex" ( set MODEL=%ROOT%models\weights\MiMo-9B-CORTEX-v1.1-Q4_K_M.gguf & set EXTRA=--temp 0.6 --top-p 0.95 )
if /i "%CORE%"=="muse-glimmer-30b" ( set MODEL=%ROOT%models\weights\Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf & set EXTRA=--jinja --temp 1.0 --top-p 0.95 --top-k 64 )
if /i "%CORE%"=="muse-glimmer-30b-cortex" ( set MODEL=%ROOT%models\weights\Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf & set EXTRA=--jinja --temp 1.0 --top-p 0.95 --top-k 64 )
if not defined MODEL ( echo Unknown core: %CORE% & exit /b 64 )
if not exist "%MODEL%" ( echo Model not found: %MODEL% & echo Run once with internet: python download_models.py --core %CORE% & exit /b 1 )
echo Starting %CORE% at http://127.0.0.1:8080  (Ctrl+C to stop)
echo Protocol file: %ROOT%protocol\glimmer_cortex_system_prompt.txt
"%SRV%" -m "%MODEL%" -c 8192 --host 127.0.0.1 --port 8080 %EXTRA%
