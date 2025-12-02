"""Flask-Admin configuration."""
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from .models import Conversation, Message, User


class SecureModelView(ModelView):
    """Base admin view requiring authentication."""

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))


class UserAdmin(SecureModelView):
    """User admin view."""
    column_list = ['id', 'username', 'email', 'is_active', 'is_superuser', 'created_at']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_active', 'is_superuser']
    form_excluded_columns = ['password_hash', 'conversations']

    def on_model_change(self, form, model, is_created):
        if form.password_hash and form.password_hash.data:
            model.set_password(form.password_hash.data)


class ConversationAdmin(SecureModelView):
    """Conversation admin view."""
    column_list = ['id', 'user', 'title', 'created_at', 'updated_at']
    column_searchable_list = ['title']
    column_filters = ['user_id']


class MessageAdmin(SecureModelView):
    """Message admin view."""
    column_list = ['id', 'conversation_id', 'role', 'content', 'created_at']
    column_searchable_list = ['content']
    column_filters = ['role', 'conversation_id']


def setup_admin(admin_instance, db):
    """Setup Flask-Admin views."""
    admin_instance.add_view(UserAdmin(User, db.session))
    admin_instance.add_view(ConversationAdmin(Conversation, db.session))
    admin_instance.add_view(MessageAdmin(Message, db.session))
