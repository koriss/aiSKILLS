# nginx TLS termination (operator)

Terminate TLS in front of `webhook_server.py` (or a process manager that
execs it). Pin upstream to loopback; enforce body size limits consistent with
Telegram webhook guidance.
