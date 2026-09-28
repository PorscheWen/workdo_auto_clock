FROM python:3.11-slim

ENV TZ=Asia/Taipei

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY workdo_auto_clock.py .
COPY leave_days.json.example ./leave_days.json.example

# 預設查詢狀態；Scheduler / 手動執行時以 args 覆寫為 in / out
ENTRYPOINT ["python", "workdo_auto_clock.py"]
CMD ["status"]
