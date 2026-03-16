# Session Context

## User Prompts

### Prompt 1

현재 코드를 vercel 로 마이그레이션 하면서 로컬에서 실행시 정상적인 백그라운드 동작이 안되고있는것 같아 (apscheduler 동작안함). 관련 내용 분석해서 로컬에서 실행했을땐 스케쥴러가 동작하도록 수정해줘.

### Prompt 2

❯ .venv/bin/python main.py
WARNING:	uvicorn.error.Notifier - Telegram Bot Token or Chat ID not configured.
INFO:	uvicorn.error.Main - Starting MovieHub Web & Scheduler Service...
INFO:     Started server process [79814]
INFO:     Waiting for application startup.
INFO:     Initializing database...
INFO:     Running database migrations...
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
WARNI [apscheduler.executors.d...

### Prompt 3

아예 스케쥴러가 안켜진거같은데?

❯ .venv/bin/python main.py
WARNING:	uvicorn.error.Notifier - Telegram Bot Token or Chat ID not configured.
INFO:	uvicorn.error.Main - Starting MovieHub Web & Scheduler Service...
INFO:     Started server process [4138]
INFO:     Waiting for application startup.
INFO:     Initializing database...
INFO:     Running database migrations...
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.

### Prompt 4

❯ .venv/bin/python main.py
WARNING:	uvicorn.error.Notifier - Telegram Bot Token or Chat ID not configured.
INFO:	uvicorn.error.Main - Starting MovieHub Web & Scheduler Service...
INFO:     Started server process [15133]
INFO:     Waiting for application startup.
INFO:     Initializing database...
INFO:     Running database migrations...
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.



동일해 로컬에서 스케쥴러가 실행이 안돼

### Prompt 5

로컬 데이터가 어디에 있는지 확인해봐. vercel 마이그레이션 전에는 sqlite 였던걸로 기억해.

만약 sqlite 로 되어있다면 로컬 postgresql 로 마이그레이션해줘

### Prompt 6

❯ .venv/bin/python main.py
WARNING:	uvicorn.error.Notifier - Telegram Bot Token or Chat ID not configured.
INFO:	uvicorn.error.Main - Initializing MovieHub Service...
INFO:	uvicorn.error.Main - Initializing database schema...
INFO:	uvicorn.error.Main - Running database migrations...
INFO:	uvicorn.error.Migration - Applying Alembic migrations to postgresql:///moviehub...
INFO:	uvicorn.error.Migration - Alembic migrations applied successfully.
INFO:	uvicorn.error.Main - Database initialization ...

### Prompt 7

ERROR:    Discovery failed for LOTTE: invalid literal for int() with base 10: 'LOCAL_GIFT'

이건 뭐야?

### Prompt 8

테스트용 데이터는 삭제하는게 나을거같아

### Prompt 9

수정내역 커밋 푸시해줘

