import re
from app import app, db, view_counter

from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_user, logout_user, current_user, login_required

from app.forms import RegistrationForm, LoginForm
from app.forms import CreateBlogPost, EditProfileForm, CreateTag
from app.forms import ResetPasswordForm, ResetPasswordRequestForm
from app.models import User, BlogPost, BlogPostTags
from app.email import send_password_reset_email
from app.utils import validate_if_admin_user


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/home/')
def home():

    query = BlogPost.query.join(
        BlogPostTags,
        BlogPost.tag).order_by(BlogPost.timestamp.desc()
                               ).all()

    return render_template('home.html', blogposts=query)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')

        if not next_page or not next_page.startswith('/'):
            next_page = url_for('home')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=str(form.email.data).lower())
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
        return redirect(url_for('home'))
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

        return redirect(url_for('home'))

    user = User.verify_reset_password_token(token)

    if not user:

        return redirect(url_for('home'))

    form = ResetPasswordForm()

    if form.validate_on_submit():

        user.set_password(form.password.data)
        db.session.commit()

        flash('Your password has been reset.')

        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form)


@app.route('/editprofile', methods=['GET', 'POST'])
@login_required
def editprofile():

    form = EditProfileForm(current_user.username)

    if form.validate_on_submit():

        current_user.username = form.username.data
        current_user.username_lower = str(form.username.data).lower()
        current_user.about_me = form.about_me.data
        db.session.commit()

        flash('Your changes have been saved.')

        return redirect(url_for('admin', user=current_user))

    elif request.method == 'GET':

        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('editprofile.html', form=form)


@app.route('/toggle-theme')
def toggle_theme():

    current_theme = session.get("theme")

    if current_theme == "dark":
        session["theme"] = "light"

    else:
        session["theme"] = "dark"

    app.logger.warn(app.config['SESSION_COOKIE_SECURE'])

    return redirect(request.args.get("current_page"))


@app.route('/blog')
def blog():

    blog_join = BlogPost.query.join(BlogPostTags, BlogPost.tag).order_by(
        BlogPost.timestamp.desc()).filter(BlogPost.type == "blog")
    tag_query = BlogPostTags.query.filter().order_by(BlogPostTags.blogpost_tag)

    return render_template(
        'blog.html',
        blogposts=blog_join,
        blogtags=tag_query
    )


@app.route('/snippets')
def snippets():

    blog_join = BlogPost.query.join(BlogPostTags, BlogPost.tag).order_by(
        BlogPost.timestamp.desc()).filter(BlogPost.type == "snippet")
    tag_query = BlogPostTags.query.filter().order_by(BlogPostTags.blogpost_tag)

    return render_template(
        'snippets.html',
        blogposts=blog_join,
        blogtags=tag_query
    )


@app.route('/blog/tag/<tag_name>')
def blog_tags(tag_name):

    blog_join = BlogPost.query.filter(
        BlogPostTags.blogpost_tag.contains(tag_name)
            ).join(BlogPostTags, BlogPost.tag
        ).order_by(BlogPost.timestamp.desc()).all()

    return render_template(
        'blog_tag.html',
        blogposts=blog_join,
        tagged_as=tag_name
    )


@app.route('/<slug>/')
@view_counter.count
def readpost(slug):

    query = BlogPost.public().filter_by(slug=slug).first_or_404()

    view_count_sql = 'SELECT COUNT(id) from vc_requests where path="/' + slug + '/"'
    view_count = db.engine.execute(view_count_sql).scalar()

    return render_template(
        'readpost.html',
        blogpost=query,
        view_count=view_count
    )


@app.route('/admin/', methods=['GET', 'POST'])
@login_required
def admin():

    if validate_if_admin_user(current_user):

        overview_count_sql = ("SELECT path, COUNT(*) \
            from vc_requests \
            where path is not null \
            group by path \
            order by COUNT(path) desc")

        overview_count = db.engine.execute(overview_count_sql)

        viewcount_list = []
        total_viewcount = 0

        for path, count in overview_count:

            total_viewcount += count

            sublist = []
            sublist.append((path,count))
            viewcount_list.append(sublist)

        return render_template(
            'admin.html',
            user=current_user,
            overview_count=viewcount_list,
            total_viewcount=total_viewcount
        )

    else:
        return redirect(url_for('home'))


@app.route('/createpost/', methods=['GET', 'POST'])
@login_required
def createpost():
    if validate_if_admin_user(current_user):

        form = CreateBlogPost.refresh_values()
        if form.validate_on_submit():

            slug = re.sub('[^\w]+', '-', form.blog_title.data.lower())

            app.logger.warn(form.blog_tags.data)
            app.logger.warn(type(form.blog_tags.data))

            if '1' not in form.blog_tags.data:

                form.blog_tags.data.append('1')

            blog_entry = BlogPost(
                title=form.blog_title.data,
                slug=slug,
                icon=form.blog_icon.data,
                tag=[BlogPostTags.query.filter(BlogPostTags.id == int(
                    tag)).first() for tag in form.blog_tags.data],
                type=form.blog_type.data,
                content=form.blog_content.data
            )

            db.session.add(blog_entry)
            db.session.commit()
            flash('Blog Post Created.')
            return redirect(url_for('readpost', slug=slug))

        return render_template('createpost.html', form=form)

    else:
        return redirect(url_for('home'))


@app.route('/editpost/<slug>', methods=['GET', 'POST'])
@login_required
def editpost(slug):
    if validate_if_admin_user(current_user):

        blog_entry = BlogPost.public().filter_by(slug=slug).first_or_404()
        form = CreateBlogPost.edit_values(blog_entry)
        if form.validate_on_submit():

            if '1' not in form.blog_tags.data:

                form.blog_tags.data.append('1')

            updated_slug = re.sub('[^\w]+', '-', form.blog_title.data.lower())

            blog_entry.title = form.blog_title.data
            blog_entry.slug = updated_slug
            blog_entry.icon = form.blog_icon.data
            blog_entry.tag = [BlogPostTags.query.filter(
                BlogPostTags.id == int(tag)).first() for tag in form.blog_tags.data]
            blog_entry.content = form.blog_content.data

            db.session.commit()
            flash('Blog Post Updated.')
            return redirect(url_for('readpost', slug=updated_slug))

        return render_template('createpost.html', form=form)

    else:
        return redirect(url_for('home'))


@app.route('/admin/managetags', methods=['GET', 'POST'])
@login_required
def managetags():
    if validate_if_admin_user(current_user):

        form = CreateTag()
        if form.validate_on_submit():
            tag = BlogPostTags(blogpost_tag=form.tag.data)
            db.session.add(tag)
            db.session.commit()
            flash('Tag Added.')
            return redirect(url_for('managetags'))

        query = BlogPostTags.tag_names()
        return render_template('managetags.html', blogtags=query, form=form)

    else:
        return redirect(url_for('home'))
