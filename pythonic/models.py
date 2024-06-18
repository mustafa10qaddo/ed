from datetime import datetime, timezone
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from pythonic import db,login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    fname: so.Mapped[str] = so.mapped_column(sa.String(25), nullable=False)
    lname: so.Mapped[str] = so.mapped_column(sa.String(25), nullable=False)
    username: so.Mapped[str] = so.mapped_column(sa.String(25), unique=True, nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(125), unique=True, nullable=False)
    image_file: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False, default="default.jpg")
    bio = db.Column(db.Text, nullable=True)
    password: so.Mapped[str] = so.mapped_column(sa.String(60), nullable=False)

    lessons: so.WriteOnlyMapped[List['Lesson']] = so.relationship("Lesson", back_populates="author", lazy=True)

    def __repr__(self):
        return f"User('{self.fname}', '{self.lname}', '{self.username}', '{self.email}', '{self.image_file}')"

class Lesson(db.Model):
    __tablename__ = 'lesson'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)
    date_posted: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)
    content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    thumbnail: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False, default="default_thumbnail.jpg")
    slug: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), nullable=False)
    course_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("course.id"), nullable=False)

    author: so.Mapped[User] = so.relationship("User", back_populates="lessons")
    course_name: so.Mapped['Course'] = so.relationship("Course", back_populates="lessons")
    
    def __repr__(self):
        return f"Lesson('{self.title}', '{self.date_posted}')"

class Course(db.Model):
    __tablename__ = 'course'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(50), unique=True, nullable=False)
    description: so.Mapped[str] = so.mapped_column(sa.String(150), nullable=False)
    icon: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False, default="default_icon.jpg")

    lessons: so.WriteOnlyMapped[List[Lesson]] = so.relationship("Lesson", back_populates="course_name", lazy=True)
    def __repr__(self):
        return f"Course('{self.title}')"
