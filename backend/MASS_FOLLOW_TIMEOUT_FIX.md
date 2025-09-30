# Mass Follow Stream Timeout Controls

## Problem

The mass-follow stream was running for very long periods without proper timeout controls, causing it to run indefinitely in some cases.

## Solution

Added comprehensive timeout controls and performance optimizations:

### 1. **Timeout Controls**

- **Maximum Duration**: 10 minutes (configurable via `max_duration_minutes` parameter)
- **Reduced Max Scrolls**: 50 (was 200) to prevent excessive scrolling
- **Automatic Timeout**: Stream automatically stops after timeout with clear reason

### 2. **Performance Optimizations**

- **Faster Action Delays**: 1.0-1.5 seconds (was 2.5-4 seconds) between actions
- **Reduced Scroll Limits**: 50 max scrolls (was 200)
- **Progress Updates**: Include elapsed time in progress events

### 3. **API Changes**

#### Backend (`backend/app/services/actions.py`)

```python
async def perform_mass_follow_stream(
    ws_url: str,
    target_username: str,
    mode: str,
    limit: int = 50,
    percent: int | None = None,
    max_scrolls: int = 50,  # Reduced from 200
    section: str = "followers",
    debug_dom: bool = False,
    max_duration_minutes: int = 10,  # NEW: Maximum 10 minutes
):
```

#### Backend (`backend/app/api/actions.py`)

```python
@router.get("/mass-follow-stream")
async def mass_follow_stream(
    # ... existing parameters ...
    max_scrolls: int = 50,  # Reduced default
    max_duration_minutes: int = 10,  # NEW: Maximum 10 minutes
    # ... rest of parameters ...
):
```

### 4. **Frontend Changes**

#### Progress Display (`frontend/src/pages/Actions.tsx`)

- Added elapsed time to progress state
- Updated progress display to show elapsed minutes
- Updated label to mention timeout: "Use mass-follow stream (safer scrolling + delays, max 10min timeout)"

### 5. **Timeout Logic**

```python
# Check timeout in main loop
current_time = asyncio.get_event_loop().time()
elapsed_time = current_time - start_time
if elapsed_time > max_duration_seconds:
    yield {"type": "done", "reason": "timeout", "message": f"Reached maximum duration of {max_duration_minutes} minutes"}
    return
```

### 6. **Progress Updates**

```python
# Include elapsed time in progress events
yield {"type": "progress", "processed": len(processed), "acted": acted, "total": est_total, "elapsed_minutes": round(elapsed_time / 60, 1)}
```

## Benefits

- ✅ **No more infinite runs** - Maximum 10 minutes duration
- ✅ **Faster execution** - Reduced delays between actions
- ✅ **Better user feedback** - Shows elapsed time in progress
- ✅ **Configurable timeouts** - Can be adjusted via API parameters
- ✅ **Clear completion reasons** - Shows why the stream stopped (limit, timeout, max_scrolls)

## Usage

The timeout controls are now automatic. Users will see:

- Progress updates with elapsed time
- Clear completion messages
- Maximum 10-minute runtime
- Faster action execution

## Testing

Run `test_mass_follow_timeout.ps1` to verify the timeout controls work correctly.

