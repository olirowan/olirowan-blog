import datetime
from email.policy import default
import jwt
import urllib
import bleach
from hashlib import md5
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db, login

from markdown import markdown
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension
from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache
from flask import Markup

oembed_providers = bootstrap_basic(OEmbedCache())

markdown_tags = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "b", "i", "strong", "em", "tt",
    "p", "br",
    "span", "div", "blockquote", "code", "hr",
    "thead", "tbody", "table",
    "th", "tr", "td", "ul", "ol", "li", "dd", "dt", "dl",
    "img",
    "a",
    "pre",
]

markdown_styles = [
    "background",
    "border", "border-top", "border-bottom", "border-left", "border-right",
    "border-color", "border-radius", "border-style", "border-width",
    "color", "font-weight", "font-style", "text-decoration"
]

markdown_attributes = {
    "*": ["style", "class"],
    "a": ["href"],
    "img": ["src"]
}


@app.template_filter('clean_querystring')
def clean_querystring(request_args, *keys_to_remove, **new_values):

    querystring = dict((key, value) for key, value in request_args.items())

    for key in keys_to_remove:
        querystring.pop(key, None)

    querystring.update(new_values)

    return urllib.urlencode(querystring)


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    username_lower = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(128), index=True, unique=True)

    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))

    registered = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_username_lower(self, username):
        self.username_lower = str(username).lower()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):

        value_to_hash = str(self.registered.strftime('%s')) + str(self.email.lower())

        digest = md5(value_to_hash.encode('utf-8')).hexdigest()

        return 'https://www.gravatar.com/avatar/\
            {}?d=robohash&s={}'.format(digest, size)

    def get_reset_password_token(self, expires_in=43200):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):

        try:
            id = jwt.decode(
                token, app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']

        except KeyError:
            return

        return User.query.get(id)


@login.user_loader
def load_user(id):

    return User.query.get(int(id))



class BlogPostTags(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blogpost_tag = db.Column(db.String(16), index=True, unique=True)

    @classmethod
    def tag_names(cls):
        return BlogPostTags.query.filter()


class BlogPost(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    icon = db.Column(db.String(50))
    slug = db.Column(db.String(200), unique=True)
    content = db.Column(db.Text)

    timestamp = db.Column(
        db.DateTime,
        default=datetime.datetime.now,
        index=True
    )

    blogtags_association = db.Table(
        'blogtags_association',
        db.Column('tag_id', db.Integer, db.ForeignKey('blog_post_tags.id')),
        db.Column('blogpost_id', db.Integer, db.ForeignKey('blog_post.id'))
    )

    tag = db.relationship(
        'BlogPostTags',
        secondary=blogtags_association,
        uselist=True,
        lazy='subquery',
        backref=db.backref('tag_name', lazy='subquery')
    )

    type = db.Column(db.String(20))

    @classmethod
    def public(cls):
        return BlogPost.query.filter()

    @property
    def html_content(self):

        code_css_class = "friendly"

        hilite = CodeHiliteExtension(
            linenums=False,
            noclasses=True,
            pygments_style=code_css_class
        )

        extras = ExtraExtension()
        tables = TableExtension()
        toc = TocExtension()
        pre_sanistised_markup = Markup(self.content)

        markdown_content = markdown(
            pre_sanistised_markup,
            extensions=[hilite, extras, tables, toc]
        )

        post_sanitised_markup = bleach.clean(
            markdown_content,
            tags=markdown_tags,
            attributes=markdown_attributes,
            styles=markdown_styles,
            strip=False
        )

        oembed_content = parse_html(
            post_sanitised_markup,
            oembed_providers,
            urlize_all=True,
            maxwidth=app.config['SITE_WIDTH']
        )

        post_markup = Markup(oembed_content)
        return post_markup


db.create_all()
