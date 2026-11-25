# EVENTRA

**QR-Based Event Registration & Attendance Management System**

EVENTRA is an offline-first desktop application for registering participants, issuing QR entry tickets, scanning those tickets at the door, and reporting on attendance. It uses SQLite for storage, CustomTkinter for the UI, and OpenCV for camera-based QR decoding.

---

## Quick start

The project already contains a self-contained macOS app at `dist/EVENTRA.app` and a working virtual environment at `.venv`. `./run.sh` opens the self-contained app so macOS grants camera access to EVENTRA rather than to bare Python.

```bash
cd "/Users/xlr-01/Desktop/PP MP"
./run.sh
```

Default administrator account:

| Username  | Password      |
|-----------|---------------|
| `admin` | `admin@123` |

Change this password after your first sign-in from **Settings → Change Password**.

If `dist/EVENTRA.app` is missing, `run.sh` rebuilds it using the virtual environment. Always start the app through `./run.sh` (or by opening `dist/EVENTRA.app`) so camera permission is attributed correctly.

---

## Manual setup

```bash
cd "/Users/xlr-01/Desktop/PP MP"

brew install python@3.12 python-tk@3.12
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

./run.sh
```

> Note: EVENTRA requires Python 3.12 with Homebrew `python-tk@3.12` (Tk 9.1) on macOS. The old macOS Python 3.9 / Tk 8.5 combination renders a blank CustomTkinter window. CustomTkinter is pinned to the stable 5.2.2 release; the 6.x preview has layout/API regressions on macOS.

Rebuild the macOS app after changing source files:

```bash
.venv/bin/python setup.py py2app
```

Run directly without the launcher for development only (camera permission may not work):

```bash
.venv/bin/python main.py
```

Override the data directory if needed:

```bash
EVENTRA_DATA_DIR=/path/to/eventra-data ./run.sh
```

---

## Features

- Event creation, capacity settings, registration status, and check-in status.
- Open a specific event and register a participant directly inside its detail page; the QR ticket appears immediately and the registration list updates in place.
- Delete events with confirmation from either the Events list or the event detail page; registrations and attendance are removed with the event.
- Remove a participant from a specific event from **Event Details** or **Attendance**; the QR ticket and that event's check-in record are deleted, while the shared participant record remains available.
- Mouse-wheel and trackpad scrolling are normalized on macOS, including inside event dialogs and screen panels.
- Fast native table widgets, cached screens, debounced search, and lightweight in-window notifications keep the interface responsive.
- Participant registration with automatic reuse of existing phone/email records.
- Unique, versioned QR payload per registration: `EVENTRA:V1:<token>`.
- Only the SHA-256 hash of the QR token is stored in SQLite.
- Ticket reissue rotates the token and invalidates the previous QR code.
- Camera-based QR scanning in a background thread with thread-safe Tkinter updates.
- Manual payload verification for testing or when no camera is available.
- Seven-step check-in validation: format, token lookup, active registration, active event, correct event, open check-in, and duplicate attendance prevention.
- Role-based access control for `ADMIN`, `REGISTRATION_OPERATOR`, and `CHECKIN_OPERATOR`.
- Dashboard metrics, event summaries, hourly check-in charts, and CSV exports.
- SQLite backups using the SQLite online backup API.
- Audit logging for registrations, participant removals, check-ins, failed scans, status changes, exports, and account actions.
- Modern light-theme UI with a navy sidebar, white cards, and teal primary actions.

---

## Architecture

```text
Presentation (ui/)
      ↓
Controllers (controllers/)
      ↓
Business logic (services/)
      ↓
Repositories (repositories/)
      ↓
Database / storage (database/, data/)
```

The UI never executes SQL directly. All data access goes through controllers → services → repositories → `Database`.

Cross-cutting concerns live in `config.py`, `utils/`, and `core/`:

- `core/context.py` — dependency container that wires the whole application.
- `core/app.py` — bootstrap, login/main-window lifecycle, logout, shutdown.
- `core/session.py` — authenticated session and permissions.
- `core/navigation.py` — screen switching.
- `utils/security.py` — QR token generation/hashing and PBKDF2 password storage.
- `utils/result.py` — standard service result type and result codes.

---

## Folder layout

```text
.
├── main.py                  # Entry point
├── run.sh                   # Launcher (opens dist/EVENTRA.app on macOS)
├── dist/EVENTRA.app/        # Self-contained macOS app with camera permission
├── setup.py                 # py2app build script
├── requirements.txt
├── config.py                # Paths, constants, roles
├── core/                    # App bootstrap, DI, session, navigation
├── controllers/             # UI-facing operations
├── services/                # Business rules and transactions
├── repositories/            # SQL and mapping
├── database/                # Connection, schema, migrations, initialization
├── models/                  # Dataclasses
├── hardware/                # Camera and QR decoder
├── ui/                      # Screens and reusable components
├── utils/                   # Validation, security, date, file, logging helpers
├── tests/                   # Service-level tests
└── data/                    # Runtime data (created automatically)
    ├── eventra.db
    ├── qr_codes/
    ├── exports/
    ├── backups/
    └── logs/
```

---

## Security notes

- QR tokens are generated with `secrets.token_urlsafe(32)`.
- SQLite stores `sha256(token)`, never the raw token.
- A ticket QR contains only the versioned payload; no personal data is embedded in the QR code.
- Passwords use salted PBKDF2-HMAC-SHA256 with 210,000 iterations.
- Authentication, RBAC, and audit logging are enforced in the service/session layers.
- Because raw tokens are not stored, a lost ticket must be handled by a controlled **Reissue Ticket** action, which rotates the token.

---

## Roles

| Role | Capabilities |
|------|--------------|
| `ADMIN` | Everything: events, registrations, check-in, reports, users, settings, backups |
| `REGISTRATION_OPERATOR` | View events, register participants, manage tickets, view participants/reports |
| `CHECKIN_OPERATOR` | View events, scan tickets, view attendance |

---

## Using the scanner

1. Create an event and set **Registration = OPEN**.
2. Register a participant. The ticket dialog appears immediately with the QR code.
3. Set **Check-in = OPEN** for the event.
4. Open **QR Scanner**, select the event, and start the camera.
5. Present the ticket QR to the camera, or paste the full payload into **Manual Token Verification**.

The scanner result card turns green for success, amber for duplicate check-in, and red for rejected scans.

The first time you start the camera, macOS asks whether to allow camera access for EVENTRA. Click **Allow**. If it was previously blocked, click **Camera Help** on the scanner screen, enable EVENTRA under **System Settings → Privacy & Security → Camera**, then restart the app. EVENTRA also tries camera indexes `0–2` automatically and remembers the working index. If no camera can be used, paste the full `EVENTRA:V1:...` payload into **Manual Token Verification**.

---

## Tests

Run the service-level test suite:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

For a full interactive check of the login screen, event registration, ticket issue, event deletion and every screen, run:

```bash
.venv/bin/python tests/gui_smoke.py
```

The suite covers:

- Password login and role permissions
- QR payload format and hash-only storage
- Duplicate registration and participant reuse
- Capacity enforcement
- Cancelled event handling
- Successful check-in and duplicate scan prevention
- Wrong-event, cancelled-registration, closed-check-in, malformed, and unregistered QR rejection
- Ticket reissue token rotation
- Event summary data
- Attendance CSV export
- Event deletion with cascading registrations
- Settings round-trip
- Database backup creation

Compile/import checks:

```bash
.venv/bin/python -m compileall -q .
```

---

## Excluded / future scope

Online registration, cloud sync, emailed tickets, face recognition, and PDF reports are intentionally out of scope. CSV exports and local SQLite backups are included.
