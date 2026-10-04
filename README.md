# TailorBuy

Android app that uses AI to find best-buy products on Romanian e-commerce sites.

## Setup

### Activare mediu virtual (PowerShell)
```powershell
Invoke-Expression (poetry env activate)
```

### Pornire server backend
```
uvicorn backend.main:app --reload
```