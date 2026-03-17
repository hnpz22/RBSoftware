from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.academic.schemas import (
    AssignmentSubmissionRead,
    AssignmentWithSubmissions,
    CourseDetail,
    CourseStudentRead,
    CourseTeacherRead,
    GradeDirectorRead,
    GradeWithCourses,
    LmsAssignmentCreate,
    LmsAssignmentRead,
    LmsAssignmentUpdate,
    LmsCourseCreate,
    LmsCourseRead,
    LmsCourseUpdate,
    LmsGradeCreate,
    LmsGradeRead,
    LmsGradeUpdate,
    LmsMaterialRead,
    LmsSubmissionRead,
    LmsUnitCreate,
    LmsUnitRead,
    LmsUnitUpdate,
    SchoolCreate,
    SchoolRead,
    SchoolUpdate,
    StudentAssignmentWithMySubmission,
    StudentCourseContentUnit,
    SubmissionStudentRead,
)
from app.domains.academic.services import AcademicService

router = APIRouter(prefix="/academic", tags=["academic"])

_svc = AcademicService()


# ── Request bodies ───────────────────────────────────────────────────────────


class DirectorAssignRequest(BaseModel):
    user_id: UUID


class TeacherAssignRequest(BaseModel):
    teacher_id: UUID


class StudentEnrollRequest(BaseModel):
    user_id: UUID


class StudentTransferRequest(BaseModel):
    from_course_id: UUID
    to_course_id: UUID


class GradeSubmissionRequest(BaseModel):
    score: Decimal
    feedback: str | None = None


class CourseCreateRequest(LmsCourseCreate):
    teacher_id: UUID | None = None


# ── Admin: Schools ───────────────────────────────────────────────────────────


@router.get("/schools", response_model=list[SchoolRead])
def list_schools(
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[SchoolRead]:
    schools = _svc.list_schools(session)
    return [SchoolRead.model_validate(s) for s in schools]


@router.post("/schools", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(
    data: SchoolCreate,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> SchoolRead:
    try:
        school = _svc.create_school(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return SchoolRead.model_validate(school)


@router.get("/schools/{public_id}", response_model=SchoolRead)
def get_school(
    public_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> SchoolRead:
    school = _svc.get_school(session, public_id)
    if school is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    return SchoolRead.model_validate(school)


@router.patch("/schools/{public_id}", response_model=SchoolRead)
def update_school(
    public_id: UUID,
    data: SchoolUpdate,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> SchoolRead:
    try:
        school = _svc.update_school(session, public_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if school is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    return SchoolRead.model_validate(school)


# ── Admin: Grades ────────────────────────────────────────────────────────────


@router.get("/schools/{school_id}/grades", response_model=list[LmsGradeRead])
def list_grades(
    school_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[LmsGradeRead]:
    try:
        grades = _svc.list_grades_by_school(session, school_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return [LmsGradeRead.model_validate(g) for g in grades]


@router.post(
    "/schools/{school_id}/grades",
    response_model=LmsGradeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_grade(
    school_id: UUID,
    data: LmsGradeCreate,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> LmsGradeRead:
    try:
        grade = _svc.create_grade(session, school_id, data)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return LmsGradeRead.model_validate(grade)


@router.get("/grades/{public_id}", response_model=GradeWithCourses)
def get_grade(
    public_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> GradeWithCourses:
    from app.domains.academic.repositories import GradeRepository

    grade_repo = GradeRepository(session)
    result = grade_repo.get_with_courses(grade_repo.get_by_public_id(public_id).id if grade_repo.get_by_public_id(public_id) else 0)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found")
    grade, courses, director = result
    return GradeWithCourses(
        public_id=grade.public_id,
        name=grade.name,
        label=grade.label,
        order_index=grade.order_index,
        is_active=grade.is_active,
        created_at=grade.created_at,
        updated_at=grade.updated_at,
        director=GradeDirectorRead.model_validate(director) if director else None,
        courses=[LmsCourseRead.model_validate(c) for c in courses],
    )


@router.patch("/grades/{public_id}", response_model=LmsGradeRead)
def update_grade(
    public_id: UUID,
    data: LmsGradeUpdate,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> LmsGradeRead:
    grade = _svc.update_grade(session, public_id, data)
    if grade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found")
    return LmsGradeRead.model_validate(grade)


@router.post("/grades/{public_id}/director", status_code=status.HTTP_204_NO_CONTENT)
def assign_director(
    public_id: UUID,
    data: DirectorAssignRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.assign_director(session, public_id, data.user_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.delete("/grades/{public_id}/director", status_code=status.HTTP_204_NO_CONTENT)
def unassign_director(
    public_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.unassign_director(session, public_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ── Director ─────────────────────────────────────────────────────────────────


@router.get("/my-grades", response_model=list[LmsGradeRead])
def my_grades(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[LmsGradeRead]:
    grades = _svc.get_my_grades(session, current_user)
    return [LmsGradeRead.model_validate(g) for g in grades]


@router.get("/grades/{grade_id}/courses", response_model=list[LmsCourseRead])
def list_courses(
    grade_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[LmsCourseRead]:
    try:
        courses = _svc.list_courses_by_grade(session, grade_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return [LmsCourseRead.model_validate(c) for c in courses]


@router.post(
    "/grades/{grade_id}/courses",
    response_model=LmsCourseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    grade_id: UUID,
    data: CourseCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LmsCourseRead:
    try:
        course_data = LmsCourseCreate(
            name=data.name,
            description=data.description,
            year=data.year,
            is_active=data.is_active,
        )
        course = _svc.create_course(
            session, grade_id, course_data, data.teacher_id, current_user
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return LmsCourseRead.model_validate(course)


@router.patch("/courses/{public_id}", response_model=LmsCourseRead)
def update_course(
    public_id: UUID,
    data: LmsCourseUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LmsCourseRead:
    try:
        course = _svc.update_course(session, public_id, data, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return LmsCourseRead.model_validate(course)


@router.post("/courses/{public_id}/teacher", status_code=status.HTTP_204_NO_CONTENT)
def assign_teacher(
    public_id: UUID,
    data: TeacherAssignRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.assign_teacher(session, public_id, data.teacher_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/courses/{public_id}/students", status_code=status.HTTP_204_NO_CONTENT)
def enroll_student(
    public_id: UUID,
    data: StudentEnrollRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.enroll_student(session, public_id, data.user_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete(
    "/courses/{public_id}/students/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unenroll_student(
    public_id: UUID,
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.unenroll_student(session, public_id, user_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post(
    "/students/{student_id}/transfer",
    status_code=status.HTTP_204_NO_CONTENT,
)
def transfer_student(
    student_id: UUID,
    data: StudentTransferRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.transfer_student(
            session, student_id, data.from_course_id, data.to_course_id, current_user
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


# ── Teacher ──────────────────────────────────────────────────────────────────


@router.get("/my-courses", response_model=list[LmsCourseRead])
def my_courses(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[LmsCourseRead]:
    teacher_courses = _svc.get_my_courses_teacher(session, current_user)
    student_courses = _svc.get_my_courses_student(session, current_user)
    seen = set()
    combined = []
    for c in teacher_courses + student_courses:
        if c.id not in seen:
            seen.add(c.id)
            combined.append(c)
    return [LmsCourseRead.model_validate(c) for c in combined]


@router.get("/courses/{public_id}", response_model=CourseDetail)
def get_course(
    public_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> CourseDetail:
    result = _svc.get_course_detail(session, public_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    course, teacher, students, units = result
    return CourseDetail(
        public_id=course.public_id,
        name=course.name,
        description=course.description,
        year=course.year,
        is_active=course.is_active,
        created_at=course.created_at,
        updated_at=course.updated_at,
        teacher=CourseTeacherRead.model_validate(teacher) if teacher else None,
        students=[CourseStudentRead.model_validate(s) for s in students],
        units=[LmsUnitRead.model_validate(u) for u in units],
    )


@router.post(
    "/courses/{public_id}/units",
    response_model=LmsUnitRead,
    status_code=status.HTTP_201_CREATED,
)
def create_unit(
    public_id: UUID,
    data: LmsUnitCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LmsUnitRead:
    try:
        unit = _svc.create_unit(session, public_id, data, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return LmsUnitRead.model_validate(unit)


@router.patch("/units/{public_id}", response_model=LmsUnitRead)
def update_unit(
    public_id: UUID,
    data: LmsUnitUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LmsUnitRead:
    try:
        unit = _svc.update_unit(session, public_id, data, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return LmsUnitRead.model_validate(unit)


@router.post("/units/{public_id}/publish", status_code=status.HTTP_204_NO_CONTENT)
def publish_unit(
    public_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.publish_unit(session, public_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete("/units/{public_id}/publish", status_code=status.HTTP_204_NO_CONTENT)
def unpublish_unit(
    public_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.unpublish_unit(session, public_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post(
    "/units/{public_id}/materials",
    response_model=LmsMaterialRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_material(
    public_id: UUID,
    title: str = Form(...),
    type: str = Form(...),
    content: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LmsMaterialRead:
    file_key = None
    file_name = None
    if file is not None:
        # In production, upload to MinIO here and get the key back
        # file_key = upload_to_minio(file_bytes, content_type, ...)
        file_name = file.filename
        # Placeholder: generate key pattern
        import uuid as _uuid

        file_key = f"academic/materials/{_uuid.uuid4()}/{file.filename}"
    try:
        material = _svc.add_material(
            session,
            public_id,
            title=title,
            material_type=type,
            requesting_user=current_user,
            content=content,
            file_key=file_key,
            file_name=file_name,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return LmsMaterialRead.model_validate(material)


@router.delete("/materials/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    public_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.delete_material(session, public_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("/materials/{public_id}/download")
def download_material(
    public_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    material = _svc.get_material(session, public_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    if material.file_key is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Material has no file",
        )
    # In production: generate presigned URL from MinIO
    # url = minio_client.presigned_get_object(bucket, material.file_key, ...)
    url = f"/files/{material.file_key}"
    return {"url": url}


@router.post(
    "/units/{public_id}/assignments",
    response_model=LmsAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    public_id: UUID,
    data: LmsAssignmentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LmsAssignmentRead:
    try:
        assignment = _svc.create_assignment(session, public_id, data, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return LmsAssignmentRead.model_validate(assignment)


@router.patch("/assignments/{public_id}", response_model=LmsAssignmentRead)
def update_assignment(
    public_id: UUID,
    data: LmsAssignmentUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LmsAssignmentRead:
    try:
        assignment = _svc.update_assignment(session, public_id, data, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )
    return LmsAssignmentRead.model_validate(assignment)


@router.get(
    "/assignments/{public_id}/submissions",
    response_model=AssignmentWithSubmissions,
)
def get_assignment_submissions(
    public_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AssignmentWithSubmissions:
    from app.domains.academic.repositories import AssignmentRepository

    assignment = AssignmentRepository(session).get_by_public_id(public_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )
    try:
        submissions = _svc.get_assignment_submissions(session, public_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return AssignmentWithSubmissions(
        public_id=assignment.public_id,
        title=assignment.title,
        description=assignment.description,
        max_score=assignment.max_score,
        due_date=assignment.due_date,
        is_published=assignment.is_published,
        submissions=[
            AssignmentSubmissionRead(
                public_id=sub.public_id,
                content=sub.content,
                file_name=sub.file_name,
                status=sub.status,
                score=sub.score,
                feedback=sub.feedback,
                graded_at=sub.graded_at,
                submitted_at=sub.submitted_at,
                student=SubmissionStudentRead.model_validate(user),
            )
            for sub, user in submissions
        ],
    )


@router.post("/submissions/{public_id}/grade", status_code=status.HTTP_204_NO_CONTENT)
def grade_submission(
    public_id: UUID,
    data: GradeSubmissionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        _svc.grade_submission(session, public_id, data.score, data.feedback, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


# ── Student ──────────────────────────────────────────────────────────────────


@router.get("/courses/{public_id}/content", response_model=list[StudentCourseContentUnit])
def get_course_content(
    public_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[StudentCourseContentUnit]:
    try:
        result = _svc.get_student_course_content(session, public_id, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    course, units_data = result
    response = []
    for unit, materials, assignment_pairs in units_data:
        response.append(
            StudentCourseContentUnit(
                public_id=unit.public_id,
                title=unit.title,
                description=unit.description,
                order_index=unit.order_index,
                materials=[LmsMaterialRead.model_validate(m) for m in materials],
                assignments=[
                    StudentAssignmentWithMySubmission(
                        public_id=a.public_id,
                        title=a.title,
                        description=a.description,
                        max_score=a.max_score,
                        due_date=a.due_date,
                        order_index=a.order_index,
                        is_published=a.is_published,
                        my_submission=(
                            LmsSubmissionRead.model_validate(sub) if sub else None
                        ),
                    )
                    for a, sub in assignment_pairs
                ],
            )
        )
    return response


@router.post("/assignments/{public_id}/submit", response_model=LmsSubmissionRead)
async def submit_assignment(
    public_id: UUID,
    content: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LmsSubmissionRead:
    file_key = None
    file_name = None
    if file is not None:
        file_name = file.filename
        import uuid as _uuid

        file_key = f"academic/submissions/{public_id}/{current_user.public_id}/{_uuid.uuid4()}/{file.filename}"
    try:
        submission = _svc.submit(
            session,
            public_id,
            current_user,
            content=content,
            file_key=file_key,
            file_name=file_name,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return LmsSubmissionRead.model_validate(submission)


@router.get("/assignments/{public_id}/my-submission", response_model=LmsSubmissionRead)
def get_my_submission(
    public_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> LmsSubmissionRead:
    try:
        submission = _svc.get_my_submission(session, public_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No submission found"
        )
    return LmsSubmissionRead.model_validate(submission)
