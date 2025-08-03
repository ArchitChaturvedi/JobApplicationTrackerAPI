from flask import request, jsonify, current_app as app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models import db, User, JobApplication
from datetime import datetime

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user = User(username=data['username'], password=data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify(message='User registered'), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user:
        token = create_access_token(identity=user.id)
        return jsonify(access_token=token)
    return jsonify(message='Invalid credentials'), 401

@app.route('/jobs', methods=['POST'])
@jwt_required()
def add_job():
    user_id = get_jwt_identity()
    data = request.get_json()
    job = JobApplication(
        user_id=user_id,
        company=data['company'],
        role=data['role'],
        status=data.get('status', 'Applied'),
        notes=data.get('notes')
    )
    db.session.add(job)
    db.session.commit()
    return jsonify(message='Job application added'), 201

@app.route('/jobs', methods=['GET'])
@jwt_required()
def get_jobs():
    user_id = get_jwt_identity()
    jobs = JobApplication.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': job.id,
        'company': job.company,
        'role': job.role,
        'status': job.status,
        'date_applied': job.date_applied.isoformat(),
        'notes': job.notes
    } for job in jobs])

@app.route('/jobs/<int:job_id>', methods=['PUT'])
@jwt_required()
def update_job(job_id):
    user_id = get_jwt_identity()
    job = JobApplication.query.filter_by(id=job_id, user_id=user_id).first()
    if not job:
        return jsonify(message='Job not found'), 404
    data = request.get_json()
    job.status = data.get('status', job.status)
    job.notes = data.get('notes', job.notes)
    db.session.commit()
    return jsonify(message='Job updated')

@app.route('/analytics', methods=['GET'])
@jwt_required()
def analytics():
    user_id = get_jwt_identity()
    jobs = JobApplication.query.filter_by(user_id=user_id).all()
    total = len(jobs)
    rejected = sum(1 for job in jobs if job.status.lower() == 'rejected')
    offers = sum(1 for job in jobs if job.status.lower() == 'offer')
    return jsonify({
        'total_applications': total,
        'offers': offers,
        'rejections': rejected,
        'success_rate': f"{(offers / total * 100):.2f}%" if total else '0.00%'
    })

@app.route('/')
def home():
    return 'Job Tracker API is running!'