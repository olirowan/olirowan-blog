import re
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db
from app.tasks import create_database_backup
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Post, BlogPost
from app.email import send_password_reset_email
from app.validate_admin import validate_if_admin_user


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index/')
def index():
    query = BlogPost.public().order_by(BlogPost.timestamp.desc())
    return render_template('index.html', blogposts=query)


@app.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Noted.')
        return redirect(url_for('notes'))

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('notes', page=posts.next_num) \
        if posts.has_next else None

    prev_url = url_for('notes', page=posts.prev_num) \
        if posts.has_prev else None

    return render_template('notes.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None

    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None

    return render_template('explore.html', title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')

        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=str(form.email.data).lower())
        user.set_password(form.password.data)
        user.set_username_lower(form.username.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created.')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password.')
        return redirect(url_for('login'))

    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    user = User.verify_reset_password_token(token)

    if not user:
        return redirect(url_for('index'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None

    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None

    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()

    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))

    if user == current_user:
        flash('You cannot follow yourself.')
        return redirect(url_for('user', username=username))

    current_user.follow(user)
    db.session.commit()
    flash('Following {}.'.format(username))

    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()

    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))

    if user == current_user:
        flash('You cannot unfollow yourself.')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('No longer following {}.'.format(username))

    return redirect(url_for('user', username=username))


# @app.route('/about')
# def about():
#     return render_template('about.html')


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.username_lower = str(form.username.data).lower()
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/post/<id>/<uid>/delete')
@login_required
def delete(id, uid):
    if int(uid) == (current_user.id):

        db.session.query(Post).filter_by(id=int(id)).delete()
        db.session.commit()
        flash('Post removed.')
        return redirect(url_for('notes'))

    else:
        return redirect(url_for('notes'))


@app.route('/post/<id>/<uid>/edit')
@login_required
def edit(id, uid):
    if int(uid) == (current_user.id):

        flash('Edit option soon to be implemented.')
        return redirect(url_for('notes'))

    else:
        return redirect(url_for('notes'))


@app.route('/blog')
def blog():
    query = BlogPost.public().order_by(BlogPost.timestamp.desc())
    return render_template('blog.html', blogposts=query)


@app.route('/<slug>/')
def readpost(slug):
    query = BlogPost.public().filter_by(slug=slug).first_or_404()
    return render_template('readpost.html', blogpost=query)


@app.route('/admin_panel/', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if validate_if_admin_user(current_user):
        query = BlogPost.drafts().order_by(BlogPost.timestamp.desc())
        return render_template('admin_panel.html', blogposts=query)

    else:
        return redirect(url_for('user', username=current_user.username))


@app.route('/createpost/', methods=['GET', 'POST'])
@login_required
def createpost():
    if validate_if_admin_user(current_user):
        method = 'INSERT'
        return _create_or_edit(BlogPost(title='', content=''), 'createpost.html', method)

    else:
        return redirect(url_for('notes'))


@app.route('/<slug>/editpost/', methods=['GET', 'POST'])
@login_required
def editpost(slug):
    if validate_if_admin_user(current_user):
        method = 'UPDATE'
        entry = BlogPost.drafts().filter_by(slug=slug).first_or_404()
        return _create_or_edit(entry, 'editpost.html', method)

    else:
        return redirect(url_for('notes'))


def _create_or_edit(entry, template, method):
    if request.method == 'POST':
        entry.title = request.form.get('title') or ''
        entry.icon = request.form.get('icon') or ''
        entry.content = request.form.get('content') or ''
        entry.published = bool(int(request.form.get('published') or '0'))

        if not (entry.title and entry.content and entry.icon):
            flash('Title and Content values required.', 'danger')
        else:
            if method == 'INSERT':
                try:
                    entry.slug = re.sub('[^\w]+', '-', entry.title.lower())
                    blog_entry = BlogPost(title=entry.title, slug=entry.slug, content=entry.content, published=entry.published)
                    db.session.add(blog_entry)
                    db.session.commit()
                except IntegrityError:
                    flash('This title has already been used.', 'danger')
                else:
                    flash('BlogPost saved successfully.', 'success')
                    if entry.published:
                        return redirect(url_for('readpost', slug=entry.slug))
                    else:
                        return redirect(url_for('admin_panel'))
            else:
                try:
                    entry.slug = re.sub('[^\w]+', '-', entry.title.lower())
                    BlogPost.title = entry.title
                    BlogPost.slug = entry.slug
                    BlogPost.icon = entry.icon
                    BlogPost.content = entry.content
                    BlogPost.published = entry.published
                    db.session.commit()
                except IntegrityError:
                    flash('This title has already been used.', 'danger')
                else:
                    flash('BlogPost saved successfully.', 'success')
                    if entry.published:
                        return redirect(url_for('readpost', slug=entry.slug))
                    else:
                        return redirect(url_for('admin_panel'))

    return render_template(template, entry=entry)


@app.route('/drafts/')
@login_required
def drafts():
    if validate_if_admin_user(current_user):
        query = BlogPost.drafts().order_by(BlogPost.timestamp.desc())
        return render_template('blog.html', blogposts=query)

    else:
        return redirect(url_for('notes'))


@app.route('/admin_panel/run_db_backup')
@login_required
def run_db_backup():
    if validate_if_admin_user(current_user):
        create_database_backup()
        flash('Initiated database backup.')
        return redirect(url_for('admin_panel'))

    else:
        return redirect(url_for('user', username=current_user.username))