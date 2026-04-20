# API Token Usage

This document describes how API token authentication works with the current architecture.

## Architecture

The toolkit now provides abstract base classes only:

- `django_toolkit.models.api_token.AbstractDTApiToken`
- `django_toolkit.models.api_token.AbstractDTApiTokenAllowedCIDR`

Concrete database models must be defined in the project app (for example `user`):

- `user.models.user_token.ApiToken`
- `user.models.user_token.ApiTokenAllowedCIDR`

Authentication resolves the concrete model dynamically via setting:

- `DT_API_TOKEN_MODEL` (format: `app_label.ModelName`)
- Example: `user.ApiToken`

## Overview

`DTApiTokenAuthentication` expects the token in the HTTP `Authorization` header.

Header format:

```http
Authorization: Token <raw_token>
```

Important:

- Send the raw token, not the SHA-256 hash.
- The database stores only `token_hash`.
- The raw token is typically shown only once when it is created.

## How Authentication Works

Authentication flow:

1. Read the `Authorization` header.
2. Expect `Token <raw_token>`.
3. Hash the raw token with SHA-256.
4. Resolve token model from `DT_API_TOKEN_MODEL`.
5. Find token by `token_hash`.
6. Check `valid_until` (if set).
7. If CIDR restrictions exist, validate client IP against `allowed_cidrs`.
8. Authenticate as the token user.

Implementation:

- Authentication class: `django_toolkit.api.authentication.DTApiTokenAuthentication`
- Default setting in project: `DT_API_TOKEN_MODEL = 'user.ApiToken'`

## Token Fields

Expected concrete fields on the token model:

- `user`
- `name`
- `token_hash`
- `created_at`
- `valid_until` (nullable)

Expected concrete field on CIDR model:

- `token` with `related_name='allowed_cidrs'`
- `cidr`

## Creating a Token

Tokens are typically created in Django Admin.

Recommended behavior:

1. Generate a random raw token.
2. Store only `sha256(raw_token)` in `token_hash`.
3. Show raw token once to the user.

## Example Requests

### cURL

```bash
curl -H "Authorization: Token YOUR_RAW_TOKEN" \
  http://127.0.0.1:8000/api/
```

### PowerShell

```powershell
$headers = @{ Authorization = 'Token YOUR_RAW_TOKEN' }
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/' -Headers $headers -Method Get
```

### Python requests

```python
import requests

response = requests.get(
    'http://127.0.0.1:8000/api/',
    headers={
        'Authorization': 'Token YOUR_RAW_TOKEN',
    },
)

print(response.status_code)
print(response.json())
```

### JavaScript fetch

```javascript
const response = await fetch('http://127.0.0.1:8000/api/', {
  method: 'GET',
  headers: {
    Authorization: 'Token YOUR_RAW_TOKEN'
  }
});

const data = await response.json();
console.log(response.status, data);
```

## `valid_until` Behavior

- `valid_until = null`: token does not expire automatically.
- `valid_until <= now()`: authentication fails with `Token has expired.`

## CIDR Restrictions

If `allowed_cidrs` entries exist for a token, requests are only allowed from matching client IP addresses.

Examples:

- `192.168.1.10` becomes `192.168.1.10/32`
- `192.168.1.0/24`
- `10.0.0.0/8`

If the IP is not in allowed ranges, authentication fails.

## Typical Errors

### 1) Invalid header format

Wrong:

```http
Authorization: YOUR_RAW_TOKEN
```

Correct:

```http
Authorization: Token YOUR_RAW_TOKEN
```

### 2) Hash used instead of raw token

Wrong:

- Sending the value from `token_hash`

Correct:

- Send the original raw token from creation time

### 3) Token expired

`valid_until` is in the past.

### 4) CIDR restriction blocks request

Current client IP does not match configured CIDRs.

### 5) Wrong token model setting

`DT_API_TOKEN_MODEL` must be in `app_label.ModelName` format and point to an existing model.

## Example Response Behavior

Typical outcomes:

- `200 OK`: token is valid
- `401 Unauthorized`: token missing, invalid, expired, or blocked by CIDR

## Security Notes

- Treat raw tokens like passwords.
- Never commit tokens to Git.
- Never log raw tokens.
- Prefer one token per integration/client.
- Use CIDR restrictions where possible.
- Set `valid_until` for temporary integrations.
- Rotate tokens if exposed.

## Quick Checklist

Before testing a request, verify:

- A concrete token model exists (for example `user.ApiToken`)
- `DT_API_TOKEN_MODEL` points to the concrete model
- You still have the raw token
- Request sends `Authorization: Token <raw_token>`
- `DTApiTokenAuthentication` is enabled in DRF settings
- Token is not expired (`valid_until`)
- CIDR restrictions (if configured) match your client IP
