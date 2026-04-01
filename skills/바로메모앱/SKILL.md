---
name: 바로메모앱
description: macOS 메모.app(Notes.app)을 열고 포커스합니다.
triggers: []
argument-hint: ""
---

# /바로메모앱 — 메모.app 열기

메모.app을 실행하고 포커스합니다.

## When to Activate

사용자가 명시적으로 `/바로메모앱`을 입력했을 때만 실행.

## Workflow

```bash
open -a "Notes"
```

성공 시: "메모.app을 열었습니다." 한 줄로 알림.
