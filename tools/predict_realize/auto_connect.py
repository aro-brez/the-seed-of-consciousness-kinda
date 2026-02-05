#!/usr/bin/env python3
"""
PREDICT/REALIZE Auto-Connect
Automatically detects and connects to available health data sources.
Zero configuration - just run and it finds what you have.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class DataSource(Enum):
    APPLE_HEALTH = "apple_health"
    GOOGLE_FIT = "google_fit"
    OURA = "oura"
    WHOOP = "whoop"
    FITBIT = "fitbit"
    GARMIN = "garmin"
    GOOGLE_CALENDAR = "google_calendar"
    APPLE_CALENDAR = "apple_calendar"
    MANUAL = "manual"

@dataclass
class DetectedSource:
    source: DataSource
    available: bool
    connection_method: str
    data_types: List[str]
    setup_required: bool
    setup_instructions: Optional[str] = None

class AutoConnector:
    """Automatically detect and connect to health data sources."""

    def __init__(self):
        self.detected: Dict[DataSource, DetectedSource] = {}
        self.platform = self._detect_platform()

    def _detect_platform(self) -> str:
        """Detect the operating system."""
        if sys.platform == "darwin":
            return "macos"
        elif sys.platform == "linux":
            return "linux"
        elif sys.platform == "win32":
            return "windows"
        return "unknown"

    def scan_all(self) -> Dict[str, Any]:
        """Scan for all available data sources."""
        print("🔍 Scanning for health data sources...")

        scanners = [
            self._scan_apple_health,
            self._scan_apple_calendar,
            self._scan_google_calendar,
            self._scan_oura,
            self._scan_whoop,
            self._scan_fitbit,
            self._scan_garmin,
        ]

        for scanner in scanners:
            try:
                scanner()
            except Exception as e:
                print(f"  ⚠️  {scanner.__name__}: {e}")

        return self._summarize()

    def _scan_apple_health(self):
        """Check for Apple Health availability (macOS/iOS)."""
        if self.platform != "macos":
            return

        # Check if Health data export exists or Shortcuts can access it
        health_export = Path.home() / "Library" / "Health"
        shortcuts_available = self._check_shortcuts()

        self.detected[DataSource.APPLE_HEALTH] = DetectedSource(
            source=DataSource.APPLE_HEALTH,
            available=shortcuts_available or health_export.exists(),
            connection_method="shortcuts" if shortcuts_available else "manual_export",
            data_types=["sleep", "steps", "heart_rate", "workouts", "weight"],
            setup_required=not shortcuts_available,
            setup_instructions="We'll create a Shortcut that automatically shares your health data" if not shortcuts_available else None
        )

    def _check_shortcuts(self) -> bool:
        """Check if Shortcuts app can be used for automation."""
        try:
            result = subprocess.run(
                ["shortcuts", "list"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _scan_apple_calendar(self):
        """Check for Apple Calendar."""
        if self.platform != "macos":
            return

        calendar_db = Path.home() / "Library" / "Calendars"

        self.detected[DataSource.APPLE_CALENDAR] = DetectedSource(
            source=DataSource.APPLE_CALENDAR,
            available=calendar_db.exists(),
            connection_method="eventkit",
            data_types=["events", "time_allocation", "meeting_patterns"],
            setup_required=False
        )

    def _scan_google_calendar(self):
        """Check for Google Calendar (via existing OAuth)."""
        # Check if we have Google OAuth tokens from Brez
        google_creds = Path.home() / ".config" / "google" / "credentials.json"
        brez_creds = Path.home() / "REPOS" / "brez-os" / ".env"

        has_google = google_creds.exists() or (
            brez_creds.exists() and
            "GOOGLE_CLIENT_ID" in brez_creds.read_text()
        )

        self.detected[DataSource.GOOGLE_CALENDAR] = DetectedSource(
            source=DataSource.GOOGLE_CALENDAR,
            available=has_google,
            connection_method="oauth",
            data_types=["events", "time_allocation", "meeting_patterns"],
            setup_required=not has_google,
            setup_instructions="Connect your Google account" if not has_google else None
        )

    def _scan_oura(self):
        """Check for Oura Ring connection."""
        # Check for Oura token in environment or config
        oura_token = os.environ.get("OURA_TOKEN") or self._check_config("oura")

        self.detected[DataSource.OURA] = DetectedSource(
            source=DataSource.OURA,
            available=bool(oura_token),
            connection_method="api",
            data_types=["sleep", "readiness", "activity", "heart_rate"],
            setup_required=not bool(oura_token),
            setup_instructions="Get your Oura API token from cloud.ouraring.com"
        )

    def _scan_whoop(self):
        """Check for Whoop connection."""
        whoop_token = os.environ.get("WHOOP_TOKEN") or self._check_config("whoop")

        self.detected[DataSource.WHOOP] = DetectedSource(
            source=DataSource.WHOOP,
            available=bool(whoop_token),
            connection_method="api",
            data_types=["strain", "recovery", "sleep", "heart_rate"],
            setup_required=not bool(whoop_token),
            setup_instructions="Connect via Whoop API"
        )

    def _scan_fitbit(self):
        """Check for Fitbit connection."""
        fitbit_token = os.environ.get("FITBIT_TOKEN") or self._check_config("fitbit")

        self.detected[DataSource.FITBIT] = DetectedSource(
            source=DataSource.FITBIT,
            available=bool(fitbit_token),
            connection_method="api",
            data_types=["sleep", "steps", "heart_rate", "activity", "weight"],
            setup_required=not bool(fitbit_token),
            setup_instructions="Connect via Fitbit API"
        )

    def _scan_garmin(self):
        """Check for Garmin connection."""
        garmin_token = os.environ.get("GARMIN_TOKEN") or self._check_config("garmin")

        self.detected[DataSource.GARMIN] = DetectedSource(
            source=DataSource.GARMIN,
            available=bool(garmin_token),
            connection_method="api",
            data_types=["sleep", "steps", "heart_rate", "activity", "stress"],
            setup_required=not bool(garmin_token),
            setup_instructions="Connect via Garmin Connect"
        )

    def _check_config(self, service: str) -> Optional[str]:
        """Check for service credentials in config files."""
        config_paths = [
            Path.home() / ".predict_realize" / f"{service}.json",
            Path.home() / ".config" / "predict_realize" / f"{service}.json",
        ]
        for path in config_paths:
            if path.exists():
                try:
                    data = json.loads(path.read_text())
                    return data.get("token") or data.get("access_token")
                except:
                    pass
        return None

    def _summarize(self) -> Dict[str, Any]:
        """Summarize detected sources."""
        available = [s for s in self.detected.values() if s.available]
        needs_setup = [s for s in self.detected.values() if s.setup_required and not s.available]

        summary = {
            "platform": self.platform,
            "available_sources": [asdict(s) for s in available],
            "needs_setup": [asdict(s) for s in needs_setup],
            "data_types_available": list(set(
                dt for s in available for dt in s.data_types
            )),
            "ready_for_tracking": len(available) > 0
        }

        return summary

    def print_summary(self, summary: Dict[str, Any]):
        """Print a human-friendly summary."""
        print("\n" + "="*60)
        print("🔮 PREDICT/REALIZE - Data Source Scan")
        print("="*60)

        if summary["available_sources"]:
            print("\n✅ READY TO CONNECT:")
            for source in summary["available_sources"]:
                name = source['source'].value if hasattr(source['source'], 'value') else str(source['source'])
                print(f"   • {name.replace('_', ' ').title()}")
                print(f"     Data: {', '.join(source['data_types'])}")

        if summary["needs_setup"]:
            print("\n🔜 AVAILABLE WITH SETUP:")
            for source in summary["needs_setup"]:
                name = source['source'].value if hasattr(source['source'], 'value') else str(source['source'])
                print(f"   • {name.replace('_', ' ').title()}")
                if source.get("setup_instructions"):
                    print(f"     → {source['setup_instructions']}")

        if not summary["available_sources"]:
            print("\n💬 NO AUTO-SOURCES DETECTED")
            print("   That's okay! We'll track through conversation instead.")
            print("   It's actually more personal that way.")

        print("\n" + "="*60)
        return summary


def main():
    """Run auto-detection and print results."""
    connector = AutoConnector()
    summary = connector.scan_all()
    connector.print_summary(summary)

    # Save results
    output_path = Path(__file__).parent.parent.parent / "BRAIN" / "PROJECTS" / "predict_realize_sources.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\n📁 Results saved to: {output_path}")

    return summary


if __name__ == "__main__":
    main()
