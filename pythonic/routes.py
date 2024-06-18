import secrets
from PIL import Image
import os
from pythonic.models import User, Lesson, Course
from flask import render_template, url_for, flash, redirect, request, session,abort
from pythonic.forms import (
    NewCourseForm,
    NewLessonForm,
    RegistrationForm,
    LoginForm,
    UpdateProfileForm,
    LessonUpdateForm,
    )
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import sqlalchemy.orm as so

from werkzeug.utils import secure_filename
from pythonic import app, bcrypt, db
from flask_login import (
    login_required,
    login_user,
    current_user,
    logout_user,
    login_required,
)


def save_picture(form_picture, path, output_size=None):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_name = random_hex + f_ext
    picture_path = os.path.join(app.root_path, path, picture_name)
    i = Image.open(form_picture)
    if output_size:
        i.thumbnail(output_size)
    i.save(picture_path)
    return picture_name

def get_previous_next_lesson(lesson):
    course = lesson.course_name
    for lsn in course.lessons:
        if lsn.title == lesson.title:
            index = course.lessons.index(lsn)
            previous_lesson = course.lessons[index - 1] if index > 0 else None
            next_lesson = (
                course.lessons[index + 1] if index < len(course.lessons) - 1 else None
            )
            break
    return previous_lesson, next_lesson


def delete_picture(picture_name, path):
    picture_path = os.path.join(app.root_path, path, picture_name)
    try:
        os.remove(picture_path)
    except:
        pass


@app.route("/")
@app.route("/home")
def home():
    lessons = Lesson.query.all()
    courses = Course.query.all()
    return render_template("home.html", lessons=lessons, courses=courses)


@app.route("/about")
def about():
    return render_template("about.html", title="About")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            fname=form.fname.data,
            lname=form.lname.data,
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
        )
        db.session.add(user)
        db.session.commit()
        flash(f"Account created successfully for {form.username.data}", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash("You have been logged in!", "success")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login Unsuccessful. Please check credentials", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return render_template("dashboard.html", title="Dashboard", active_tab=None)


@app.route("/dashboard/profile", methods=["GET", "POST"])
@login_required
def profile():
    profile_form = UpdateProfileForm()
    if profile_form.validate_on_submit():
        if profile_form.picture.data:
            picture_file = save_picture(
                profile_form.picture.data, "static/user_pics", output_size=(150, 150)
            )
            current_user.image_file = picture_file
        current_user.username = profile_form.username.data
        current_user.email = profile_form.email.data
        current_user.bio = profile_form.bio.data
        db.session.commit()
        flash("Your profile has been updated", "success")
        return redirect(url_for("profile"))
    elif request.method == "GET":
        profile_form.username.data = current_user.username
        profile_form.email.data = current_user.email
        profile_form.bio.data = current_user.bio
    image_file = url_for("static", filename=f"user_pics/{current_user.image_file}")
    return render_template(
        "profile.html",
        title="Profile",
        profile_form=profile_form,
        image_file=image_file,
        active_tab="profile",
    )

@app.route("/dashboard/new_lesson", methods=["GET", "POST"])
@login_required
def new_lesson():
    new_lesson_form = NewLessonForm()
    new_course_form = NewCourseForm()
    form = ""
    flag = session.pop("flag", False)
    if "content" in request.form:
        form = "new_lesson_form"
    elif "description" in request.form:
        form = "new_course_form"

    if form == "new_lesson_form" and new_lesson_form.validate_on_submit():
        if new_lesson_form.thumbnail.data:
            picture_file = save_picture(
                new_lesson_form.thumbnail.data, "static/lesson_thumbnails"
            )
        lesson_slug = str(new_lesson_form.slug.data).replace(" ", "-")
        course = new_lesson_form.course.data
        lesson = Lesson(
            title=new_lesson_form.title.data,
            content=new_lesson_form.content.data,
            slug=lesson_slug,
            author=current_user,
            course_name=course,
            thumbnail=picture_file,
        )
        db.session.add(lesson)
        db.session.commit()
        flash("Your lesson has been created!", "success")
        return redirect(url_for("new_lesson"))

    elif form == "new_course_form":
        if new_lesson_form.icon.data:
            picture_file = save_picture(
                new_lesson_form.thumbnail.data, "static/course_icons"
            )
        if new_course_form.validate_on_submit():
            course_title = str(new_course_form.title.data).replace(" ", "-")
            course = Course(
                title=course_title,
                description=new_course_form.description.data,
            )
            db.session.add(course)
            db.session.commit()
            session["flag"] = True
            flash("New Course has been created!", "success")
            return redirect(url_for("dashboard"))
        else:
            print(new_course_form.errors)  # Print form validation errors

    return render_template(
        "new_lesson.html",
        title="New Lesson",
        new_lesson_form=new_lesson_form,
        new_course_form=new_course_form,
        active_tab="new_lesson",
    )


@app.route("/dashboard/new_course", methods=["GET", "POST"])
@login_required
def new_course():
    new_course_form = NewCourseForm()

    if new_course_form.validate_on_submit():
        picture_file = save_picture(
            new_course_form.icon.data, "static/course_icons", output_size=(150, 150)
        )
        course_title = str(new_course_form.title.data).replace(" ", "-")
        course = Course(
            title=course_title,
            description=new_course_form.description.data,
            icon=picture_file,
        )

        # Handle the file upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                course.photo = filename

        db.session.add(course)
        db.session.commit()
        flash("New Course has been created!", "success")
        return redirect(url_for("dashboard"))

    return render_template(
        "new_course.html",
        title="New Course",
        new_course_form=new_course_form,
        active_tab="new_course",
    )


from flask import render_template, abort
from pythonic.models import Lesson
@app.route("/<string:course>/<string:lesson_slug>")
def lesson(lesson_slug, course):
    lesson = Lesson.query.filter_by(slug=lesson_slug).first()
    if not lesson:
        abort(404)
    
    # Fetch course lessons for the lesson's course
    course_lessons = Lesson.query.filter_by(course_id=lesson.course_id).all()

    return render_template(
        "lesson_view.html",
        title=lesson.title,
        lesson=lesson,
        course_lessons=course_lessons,
    )






from pythonic.models import Lesson

def get_previous_next_lesson(lesson, course):
    # Assuming course is correctly fetched or passed
    lessons = course.lessons
    
    # Filter lessons by course and order by date_posted
    all_lessons = Lesson.query.filter_by(course_id=course.id).order_by(Lesson.date_posted).all()
    
    # Find index of current lesson
    lesson_index = next((i for i, lsn in enumerate(all_lessons) if lsn.id == lesson.id), None)

    # Calculate previous and next lessons
    previous_lesson = all_lessons[lesson_index - 1] if lesson_index > 0 else None
    next_lesson = all_lessons[lesson_index + 1] if lesson_index < len(all_lessons) - 1 else None

    return previous_lesson, next_lesson














@app.route("/<string:course_title>")
def course(course_title):
    course = Course.query.filter_by(title=course_title).first_or_404()
    course_lessons = Lesson.query.filter_by(course_id=course.id).all()

    return render_template(
        "course.html",
        title=course.title,
        course=course,
        course_lessons=course_lessons,
    )



@app.route("/courses")
def courses():
    courses = Course.query.all()
    return render_template("courses.html", title="Courses", courses=courses)



@app.route("/dashboard/user_lessons", methods=["GET", "POST"])
@login_required
def user_lessons():
    user_lessons = db.session.scalars(
        db.select(Lesson).where(Lesson.user_id == current_user.id)
    ).all()

    return render_template(
        "user_lessons.html",
        title="Your Lessons",
        active_tab="user_lessons",
        lessons=user_lessons
    )

@app.route("/<string:course>/<string:lesson_slug>/update", methods=["GET", "POST"])
@login_required
def update_lesson(course, lesson_slug):
    # Retrieve the lesson based on course title and lesson slug
    lesson = Lesson.query.join(Course).filter(Course.title == course, Lesson.slug == lesson_slug).first_or_404()

    # Check if the current user is authorized to update this lesson
    if lesson.author != current_user:
        abort(403)

    # Create the lesson update form
    form = LessonUpdateForm()

    # Handle form submission (POST request)
    if form.validate_on_submit():
        # Retrieve the course object based on form input
        course_obj = Course.query.filter_by(title=form.course.data).first()
        
        # Update lesson attributes based on form data
        if course_obj:
            lesson.course_id = course_obj.id
        lesson.title = form.title.data
        lesson.slug = str(form.slug.data).replace(" ", "-")
        lesson.content = form.content.data
        
        # Handle thumbnail upload (if provided)
        if form.thumbnail.data:
            lesson.thumbnail = save_picture(form.thumbnail.data)
        
        # Commit changes to the database
        db.session.commit()
        
        # Flash success message and redirect to the updated lesson page
        flash("Your lesson has been updated!", "success")
        return redirect(url_for("home", lesson_slug=lesson.slug, course=course))

    # Handle GET request (populate form with current lesson data)
    elif request.method == "GET":
        form.course.data = lesson.course_name.title
        form.title.data = lesson.title
        form.slug.data = lesson.slug
        form.content.data = lesson.content

    # Fetch the course object associated with the lesson
    course_obj = Course.query.filter_by(id=lesson.course_id).first_or_404()

    # Render the update lesson template with necessary data
    return render_template("update_lesson.html", title="Update | " + lesson.title, lesson=lesson, course=course_obj, form=form)








@app.route("/lesson/<lesson_id>/delete", methods=["POST"])
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.author != current_user:
        abort(403)
    db.session.delete(lesson)
    db.session.commit()
    flash("Your lesson has been deleted!", "success")
    return redirect(url_for("user_lessons"))