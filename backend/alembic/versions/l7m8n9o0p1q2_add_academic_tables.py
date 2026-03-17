"""add_academic_tables

Revision ID: l7m8n9o0p1q2
Revises: k6l7m8n9o0p1
Create Date: 2026-03-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'l7m8n9o0p1q2'
down_revision = 'k6l7m8n9o0p1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. schools
    op.create_table(
        'schools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(as_uuid=True, native_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('contact_name', sa.String(length=200), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
        sa.UniqueConstraint('code'),
    )

    # 2. lms_grades (FK → schools)
    op.create_table(
        'lms_grades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(as_uuid=True, native_uuid=False), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
    )
    op.create_index('ix_lms_grades_school_id', 'lms_grades', ['school_id'], unique=False)

    # 3. lms_grade_directors (FK → lms_grades, users)
    op.create_table(
        'lms_grade_directors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grade_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['grade_id'], ['lms_grades.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('grade_id', 'user_id', name='uq_lms_grade_directors_grade_user'),
    )
    op.create_index('ix_lms_grade_directors_grade_id', 'lms_grade_directors', ['grade_id'])
    op.create_index('ix_lms_grade_directors_user_id', 'lms_grade_directors', ['user_id'])

    # 4. lms_courses (FK → lms_grades, schools, users)
    op.create_table(
        'lms_courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(as_uuid=True, native_uuid=False), nullable=False),
        sa.Column('grade_id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['grade_id'], ['lms_grades.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
    )
    op.create_index('ix_lms_courses_grade_id', 'lms_courses', ['grade_id'])
    op.create_index('ix_lms_courses_school_id', 'lms_courses', ['school_id'])
    op.create_index('ix_lms_courses_teacher_id', 'lms_courses', ['teacher_id'])

    # 5. lms_course_students (FK → lms_courses, users)
    op.create_table(
        'lms_course_students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('transferred_from_course_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column(
            'enrolled_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['course_id'], ['lms_courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['transferred_from_course_id'], ['lms_courses.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'user_id', name='uq_lms_course_students_course_user'),
    )
    op.create_index('ix_lms_course_students_course_id', 'lms_course_students', ['course_id'])
    op.create_index('ix_lms_course_students_user_id', 'lms_course_students', ['user_id'])

    # 6. lms_units (FK → lms_courses)
    op.create_table(
        'lms_units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(as_uuid=True, native_uuid=False), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['course_id'], ['lms_courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
    )
    op.create_index('ix_lms_units_course_id', 'lms_units', ['course_id'])

    # 7. lms_materials (FK → lms_units)
    op.create_table(
        'lms_materials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(as_uuid=True, native_uuid=False), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_key', sa.String(length=500), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['unit_id'], ['lms_units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
    )
    op.create_index('ix_lms_materials_unit_id', 'lms_materials', ['unit_id'])

    # 8. lms_assignments (FK → lms_units)
    op.create_table(
        'lms_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(as_uuid=True, native_uuid=False), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['unit_id'], ['lms_units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
    )
    op.create_index('ix_lms_assignments_unit_id', 'lms_assignments', ['unit_id'])

    # 9. lms_submissions (FK → lms_assignments, users)
    op.create_table(
        'lms_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.Uuid(as_uuid=True, native_uuid=False), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_key', sa.String(length=500), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'DRAFT'")),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('graded_by', sa.Integer(), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'submitted_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['assignment_id'], ['lms_assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['graded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
        sa.UniqueConstraint(
            'assignment_id', 'student_id', name='uq_lms_submissions_assignment_student'
        ),
    )
    op.create_index('ix_lms_submissions_assignment_id', 'lms_submissions', ['assignment_id'])
    op.create_index('ix_lms_submissions_student_id', 'lms_submissions', ['student_id'])
    op.create_index('ix_lms_submissions_status', 'lms_submissions', ['status'])


def downgrade() -> None:
    op.drop_index('ix_lms_submissions_status', table_name='lms_submissions')
    op.drop_index('ix_lms_submissions_student_id', table_name='lms_submissions')
    op.drop_index('ix_lms_submissions_assignment_id', table_name='lms_submissions')
    op.drop_table('lms_submissions')

    op.drop_index('ix_lms_assignments_unit_id', table_name='lms_assignments')
    op.drop_table('lms_assignments')

    op.drop_index('ix_lms_materials_unit_id', table_name='lms_materials')
    op.drop_table('lms_materials')

    op.drop_index('ix_lms_units_course_id', table_name='lms_units')
    op.drop_table('lms_units')

    op.drop_index('ix_lms_course_students_user_id', table_name='lms_course_students')
    op.drop_index('ix_lms_course_students_course_id', table_name='lms_course_students')
    op.drop_table('lms_course_students')

    op.drop_index('ix_lms_courses_teacher_id', table_name='lms_courses')
    op.drop_index('ix_lms_courses_school_id', table_name='lms_courses')
    op.drop_index('ix_lms_courses_grade_id', table_name='lms_courses')
    op.drop_table('lms_courses')

    op.drop_index('ix_lms_grade_directors_user_id', table_name='lms_grade_directors')
    op.drop_index('ix_lms_grade_directors_grade_id', table_name='lms_grade_directors')
    op.drop_table('lms_grade_directors')

    op.drop_index('ix_lms_grades_school_id', table_name='lms_grades')
    op.drop_table('lms_grades')

    op.drop_table('schools')
