"""
Resume deletion API tests.

Covers: DELETE /resumes/{resume_id} endpoint behavior.
"""

from src.domain.auth.models import User
from src.domain.applications.models import Application
from src.domain.resume.models import Resume
from src.domain.jobs.models import Job


def _register_and_login(client, sample_user_payload):
    register_response = client.post('/auth/register', json=sample_user_payload)
    assert register_response.status_code == 200

    login_response = client.post(
        '/auth/login',
        data={
            'username': sample_user_payload['email'],
            'password': sample_user_payload['password'],
        },
    )
    assert login_response.status_code == 200
    return login_response.json()['access_token']


def _get_user_by_email(db_session, email: str) -> User:
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    return user


def test_delete_resume_removes_owned_resume(client, sample_user_payload, db_session):
    """DELETE /resumes/{resume_id} deletes the caller's own resume."""
    token = _register_and_login(client, sample_user_payload)
    user = _get_user_by_email(db_session, sample_user_payload['email'])

    resume = Resume(
        user_id=user.id,
        file_name='resume.pdf',
        file_path='/tmp/test-resume.pdf',
        mime_type='application/pdf',
        extracted_text='sample',
        parsed_json=None,
        variant_type='master',
        is_primary=False,
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    resume_id = resume.id
    resume_id = resume.id

    response = client.delete(f'/resumes/{resume_id}', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    assert response.json()['message'] == 'Resume deleted.'
    assert db_session.query(Resume).filter(Resume.id == resume.id).first() is None


def test_delete_resume_returns_404_for_other_users_resume(client, sample_user_payload, db_session):
    """DELETE /resumes/{resume_id} returns 404 when resume belongs to another user."""
    owner_payload = {
        'email': f"owner-{sample_user_payload['email']}",
        'password': sample_user_payload['password'],
        'first_name': 'Owner',
        'last_name': 'User',
    }
    owner_token = _register_and_login(client, owner_payload)
    assert owner_token

    requester_token = _register_and_login(client, sample_user_payload)
    owner_user = _get_user_by_email(db_session, owner_payload['email'])

    resume = Resume(
        user_id=owner_user.id,
        file_name='private-resume.pdf',
        file_path='/tmp/private-resume.pdf',
        mime_type='application/pdf',
        extracted_text='private',
        parsed_json=None,
        variant_type='master',
        is_primary=False,
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    response = client.delete(
        f'/resumes/{resume.id}',
        headers={'Authorization': f'Bearer {requester_token}'},
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'Resume not found.'
    assert db_session.query(Resume).filter(Resume.id == resume.id).first() is not None


def test_delete_resume_clears_application_resume_reference(client, sample_user_payload, db_session):
    """DELETE /resumes/{resume_id} nulls application.resume_id before deleting."""
    token = _register_and_login(client, sample_user_payload)
    user = _get_user_by_email(db_session, sample_user_payload['email'])

    job = Job(
        source='greenhouse',
        source_job_id='resume-delete-fk-test',
        title='Backend Engineer',
        company_name='Artemis',
        apply_url='https://example.com/jobs/1',
        location='Remote',
        workplace_type='remote',
        description='Test job',
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    resume = Resume(
        user_id=user.id,
        file_name='resume-linked.pdf',
        file_path='/tmp/resume-linked.pdf',
        mime_type='application/pdf',
        extracted_text='linked',
        parsed_json=None,
        variant_type='master',
        is_primary=False,
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    resume_id = resume.id

    application = Application(
        user_id=user.id,
        job_id=job.id,
        resume_id=resume_id,
        status='queued',
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)

    response = client.delete(f'/resumes/{resume_id}', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    db_session.expire_all()
    assert db_session.query(Resume).filter(Resume.id == resume_id).first() is None

    persisted_application = db_session.query(Application).filter(Application.id == application.id).first()
    assert persisted_application is not None
    assert persisted_application.resume_id is None
