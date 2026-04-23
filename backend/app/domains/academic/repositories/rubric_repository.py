from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.domains.academic.models.rubric import Rubric
from app.domains.academic.models.rubric_criteria import RubricCriteria
from app.domains.academic.models.rubric_level import RubricLevel


class RubricRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_evaluation(self, evaluation_id: int) -> Rubric | None:
        stmt = select(Rubric).where(Rubric.training_evaluation_id == evaluation_id)
        return self.session.exec(stmt).first()

    def get_by_assignment(self, assignment_id: int) -> Rubric | None:
        stmt = select(Rubric).where(Rubric.lms_assignment_id == assignment_id)
        return self.session.exec(stmt).first()

    def get_full(self, rubric_id: int) -> dict[str, Any] | None:
        rubric = self.session.get(Rubric, rubric_id)
        if not rubric:
            return None
        criteria = self.session.exec(
            select(RubricCriteria)
            .where(RubricCriteria.rubric_id == rubric_id)
            .order_by(RubricCriteria.order_index)
        ).all()
        result: dict[str, Any] = {
            "public_id": rubric.public_id,
            "title": rubric.title,
            "description": rubric.description,
            "criteria": [],
        }
        for c in criteria:
            levels = self.session.exec(
                select(RubricLevel)
                .where(RubricLevel.criteria_id == c.id)
                .order_by(RubricLevel.order_index)
            ).all()
            result["criteria"].append(
                {
                    "public_id": c.public_id,
                    "title": c.title,
                    "description": c.description,
                    "weight": c.weight,
                    "order_index": c.order_index,
                    "levels": [
                        {
                            "public_id": l.public_id,
                            "title": l.title,
                            "description": l.description,
                            "points": l.points,
                            "order_index": l.order_index,
                        }
                        for l in levels
                    ],
                }
            )
        return result

    def upsert_full(
        self,
        data: dict[str, Any],
        evaluation_id: int | None = None,
        assignment_id: int | None = None,
    ) -> Rubric:
        if evaluation_id is not None:
            rubric = self.get_by_evaluation(evaluation_id)
        else:
            rubric = self.get_by_assignment(assignment_id)

        if rubric is None:
            rubric = Rubric(
                title=data["title"],
                description=data.get("description"),
                training_evaluation_id=evaluation_id,
                lms_assignment_id=assignment_id,
            )
            self.session.add(rubric)
            self.session.commit()
            self.session.refresh(rubric)

        old_criteria = self.session.exec(
            select(RubricCriteria).where(RubricCriteria.rubric_id == rubric.id)
        ).all()
        for c in old_criteria:
            self.session.delete(c)
        self.session.commit()

        for i, crit_data in enumerate(data.get("criteria", [])):
            criteria = RubricCriteria(
                rubric_id=rubric.id,
                title=crit_data["title"],
                description=crit_data.get("description"),
                weight=crit_data.get("weight", 1),
                order_index=i,
            )
            self.session.add(criteria)
            self.session.commit()
            self.session.refresh(criteria)

            for j, level_data in enumerate(crit_data.get("levels", [])):
                level = RubricLevel(
                    criteria_id=criteria.id,
                    title=level_data["title"],
                    description=level_data.get("description"),
                    points=level_data["points"],
                    order_index=j,
                )
                self.session.add(level)
            self.session.commit()

        rubric.title = data["title"]
        rubric.description = data.get("description")
        rubric.updated_at = datetime.now(timezone.utc)
        self.session.add(rubric)
        self.session.commit()
        return rubric
