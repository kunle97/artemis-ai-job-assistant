"""
Backfill missing job feed links for a specific user.

This script links existing jobs into job_user_feed for the given user email.
Use --apply to persist changes; otherwise it runs in dry-run mode.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
import uuid

from sqlalchemy import and_, func

# Ensure src.* imports resolve when running from services/api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.domain.auth.models import User
from src.domain.profile.models import CandidateProfile
from src.domain.jobs.models import Job, JobFeedStatus, JobUserFeed
from src.infrastructure.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill job_user_feed links for one user")
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--apply", action="store_true", help="Persist inserts (default dry-run)")
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive jobs as well (default: only active jobs)",
    )
    parser.add_argument(
        "--status",
        default="seen",
        choices=["new", "seen", "saved", "dismissed"],
        help="Initial status for inserted feed rows (default: seen)",
    )
    args = parser.parse_args()

    status_value = JobFeedStatus(args.status)
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == args.email).first()
        if user is None:
            print(f"ERROR user_not_found email={args.email}")
            return

        total_jobs_query = db.query(func.count(Job.id))
        if not args.include_inactive:
            total_jobs_query = total_jobs_query.filter(Job.is_active == True)  # noqa: E712
        total_jobs = int(total_jobs_query.scalar() or 0)

        existing_links = int(
            db.query(func.count(JobUserFeed.id))
            .filter(JobUserFeed.user_id == user.id)
            .scalar()
            or 0
        )

        missing_job_rows = (
            db.query(Job.id)
            .outerjoin(
                JobUserFeed,
                and_(
                    JobUserFeed.job_id == Job.id,
                    JobUserFeed.user_id == user.id,
                ),
            )
            .filter(JobUserFeed.id.is_(None))
        )
        if not args.include_inactive:
            missing_job_rows = missing_job_rows.filter(Job.is_active == True)  # noqa: E712

        missing_job_ids = [row[0] for row in missing_job_rows.all()]
        missing_count = len(missing_job_ids)

        print("JOB_FEED_BACKFILL_SUMMARY")
        print(f"user_email={args.email}")
        print(f"user_id={user.id}")
        print(f"total_jobs_considered={total_jobs}")
        print(f"existing_feed_links={existing_links}")
        print(f"missing_feed_links={missing_count}")
        print(f"mode={'apply' if args.apply else 'dry-run'}")
        print(f"insert_status={status_value.value}")

        if not args.apply:
            print("DRY_RUN_COMPLETE")
            return

        if missing_count == 0:
            print("APPLY_COMPLETE inserted=0")
            return

        now = datetime.now(UTC)
        rows_to_insert = [
            JobUserFeed(
                id=uuid.uuid4(),
                user_id=user.id,
                job_id=job_id,
                status=status_value,
                created_at=now,
            )
            for job_id in missing_job_ids
        ]
        db.bulk_save_objects(rows_to_insert)
        db.commit()

        final_links = int(
            db.query(func.count(JobUserFeed.id))
            .filter(JobUserFeed.user_id == user.id)
            .scalar()
            or 0
        )
        print(f"APPLY_COMPLETE inserted={missing_count}")
        print(f"final_feed_links={final_links}")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"ERROR backfill_failed reason={exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
