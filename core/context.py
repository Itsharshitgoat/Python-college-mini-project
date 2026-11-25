"""Dependency container that wires the whole application together."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from config import Paths, default_paths
from controllers.attendance_controller import AttendanceController
from controllers.auth_controller import AuthController
from controllers.event_controller import EventController
from controllers.participant_controller import ParticipantController
from controllers.registration_controller import RegistrationController
from controllers.report_controller import ReportController
from controllers.scanner_controller import ScannerController
from controllers.settings_controller import SettingsController
from controllers.ticket_controller import TicketController
from core.session import Session
from database.connection import Database
from database.initialize import initialize_database
from database.migrations import migrate
from repositories.attendance_repository import AttendanceRepository
from repositories.audit_repository import AuditRepository
from repositories.event_repository import EventRepository
from repositories.participant_repository import ParticipantRepository
from repositories.registration_repository import RegistrationRepository
from repositories.settings_repository import SettingsRepository
from repositories.user_repository import UserRepository
from services.attendance_service import AttendanceService
from services.auth_service import AuthService
from services.backup_service import BackupService
from services.checkin_service import CheckinService
from services.event_service import EventService
from services.participant_service import ParticipantService
from services.qr_service import QrService
from services.registration_service import RegistrationService
from services.report_service import ReportService
from services.settings_service import SettingsService
from utils.logger import configure_logger


@dataclass
class AppContext:
    paths: Paths
    db: Database
    session: Session
    logger: logging.Logger

    event_repo: EventRepository
    participant_repo: ParticipantRepository
    registration_repo: RegistrationRepository
    attendance_repo: AttendanceRepository
    user_repo: UserRepository
    audit_repo: AuditRepository
    settings_repo: SettingsRepository

    qr: QrService
    auth: AuthService
    events: EventService
    participants: ParticipantService
    registrations: RegistrationService
    checkin: CheckinService
    attendance: AttendanceService
    reports: ReportService
    backup: BackupService
    settings: SettingsService

    auth_controller: AuthController
    event_controller: EventController
    participant_controller: ParticipantController
    registration_controller: RegistrationController
    scanner_controller: ScannerController
    attendance_controller: AttendanceController
    report_controller: ReportController
    settings_controller: SettingsController
    ticket_controller: TicketController

    @classmethod
    def create(cls, paths: Paths | None = None) -> "AppContext":
        paths = paths or default_paths()
        paths.ensure()
        logger = configure_logger(paths.logs_dir)
        db = Database(paths.db_path)
        initialize_database(db, paths)
        migrate(db)

        event_repo = EventRepository(db)
        participant_repo = ParticipantRepository(db)
        registration_repo = RegistrationRepository(db)
        attendance_repo = AttendanceRepository(db)
        user_repo = UserRepository(db)
        audit_repo = AuditRepository(db)
        settings_repo = SettingsRepository(db)
        settings = SettingsService(settings_repo)

        qr = QrService(paths)
        auth = AuthService(user_repo, audit_repo)
        events = EventService(event_repo, audit_repo, paths)
        participants = ParticipantService(participant_repo)
        registrations = RegistrationService(
            db, paths, event_repo, participant_repo, registration_repo, qr, audit_repo
        )
        checkin = CheckinService(db, registration_repo, attendance_repo, audit_repo, qr)
        attendance = AttendanceService(db, attendance_repo, registration_repo, audit_repo)
        reports = ReportService(
            db, paths, event_repo, participant_repo, registration_repo,
            attendance_repo, audit_repo,
        )
        backup = BackupService(db, paths, audit_repo)

        return cls(
            paths=paths,
            db=db,
            session=Session(),
            logger=logger,
            event_repo=event_repo,
            participant_repo=participant_repo,
            registration_repo=registration_repo,
            attendance_repo=attendance_repo,
            user_repo=user_repo,
            audit_repo=audit_repo,
            settings_repo=settings_repo,
            qr=qr,
            auth=auth,
            events=events,
            participants=participants,
            registrations=registrations,
            checkin=checkin,
            attendance=attendance,
            reports=reports,
            backup=backup,
            settings=settings,
            auth_controller=AuthController(auth),
            event_controller=EventController(events),
            participant_controller=ParticipantController(participants),
            registration_controller=RegistrationController(registrations, qr),
            scanner_controller=ScannerController(checkin, events),
            attendance_controller=AttendanceController(attendance, reports),
            report_controller=ReportController(reports, backup),
            settings_controller=SettingsController(settings),
            ticket_controller=TicketController(qr),
        )

    def shutdown(self) -> None:
        self.db.close()
