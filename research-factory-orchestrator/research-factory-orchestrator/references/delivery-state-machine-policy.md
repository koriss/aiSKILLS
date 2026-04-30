
# Delivery State Machine Policy

Delivery states:

```text
created
running
ready
delivering
delivered
partial
failed
cancelled
```

`delivered` requires:
- standalone HTML sent;
- research-package.zip sent;
- Telegram summary sent;
- delivery manifest present;
- attachment ledger says all required sent.
