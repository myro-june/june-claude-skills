---
name: 바로메모하루조회
description: 메모.app 001-하루 인박스의 메모 목록을 조회합니다.
triggers: []
argument-hint: ""
---

# /바로메모하루조회 — 하루 인박스 메모 목록 조회

001-하루 인박스에 있는 메모들의 제목과 내용을 보여줍니다.

## When to Activate

사용자가 명시적으로 `/바로메모하루조회`를 입력했을 때만 실행.

## Workflow

### Step 1: 메모 목록 조회

```bash
osascript -e '
tell application "Notes"
  set noteList to every note in folder "001-하루 인박스"
  set output to ""
  set i to 1
  repeat with n in noteList
    set output to output & i & "|||" & name of n & "|||" & plaintext of n & "
---SEPARATOR---
"
    set i to i + 1
  end repeat
  return output
end tell'
```

### Step 2: 결과 표시

메모가 없으면: "하루 인박스가 비어있습니다." 알림 후 종료.

메모가 있으면 번호와 함께 목록 표시:

```
하루 인박스 (N개):

1. **메모 제목 A**
   내용 미리보기 (첫 1~2줄)

2. **메모 제목 B**
   내용 미리보기 (첫 1~2줄)
```

- 내용이 길면 첫 100자까지만 미리보기로 표시한다.
- 총 메모 개수를 함께 알린다.
