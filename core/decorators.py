# -*- encoding: utf-8 -*-
from __future__ import absolute_import
import trafaret as t
import settings

from functools import wraps

from flask import abort, request, g, json, current_app
from flask.ext.babel import get_locale

from flamaster.extensions import db
from flamaster.core.models import CRUDMixin

from sqlalchemy.ext.hybrid import hybrid_property

from . import http
from .utils import jsonify_status_code, plural_underscored


def api_resource(bp, endpoint, pk_def):
    pk = pk_def.keys()[0]
    pk_type = pk_def[pk] and pk_def[pk].__name__ or None
    # building url from the endpoint
    url = "/{}/".format(endpoint)
    collection_methods = ['GET', 'POST']
    item_methods = ['GET', 'PUT', 'DELETE']

    def wrapper(resource_class):
        resource = resource_class().as_view(endpoint)
        bp.add_url_rule(url, view_func=resource, methods=collection_methods)
        if pk_type is None:
            url_rule = "{}<{}>".format(url, pk)
        else:
            url_rule = "{}<{}:{}>".format(url, pk_type, pk)

        bp.add_url_rule(url_rule, view_func=resource, methods=item_methods)
        return resource_class

    return wrapper


def multilingual(cls):

    locale = get_locale()
    if locale is None:
        lang = unicode(settings.BABEL_DEFAULT_LOCALE)
    else:
        lang = unicode(locale.language)

    def create_property(cls, localized, columns, field):

        def getter(self):
            instance = localized.query.filter_by(id=self.id,
                                                 locale=lang).first()
            return instance and getattr(instance, field) or None

        def setter(self, value):
            from_db = localized.query.filter_by(id=self.id,
                                                locale=lang).first()

            instance = from_db or localized(parent=self, locale=lang)
            setattr(instance, field, value)
            instance.save()

        def expression(self):
            return db.Query(columns[field]) \
                .filter(localized.parent_id == self.id,
                        localized.locale == lang).as_scalar()

        setattr(cls, field, hybrid_property(getter, setter, expr=expression))

    def closure(cls):
        class_name = cls.__name__ + 'Localized'
        tablename = plural_underscored(class_name)

        if db.metadata.tables.get(tablename) is not None:
            return cls

        cls_columns = cls.__table__.get_children()
        columns = dict([(c.name, c.copy()) for c in cls_columns
                        if isinstance(c.type, (db.Unicode, db.UnicodeText))])
        localized_names = columns.keys()

        columns.update({
            'parent_id': db.Column(db.Integer,
                                   db.ForeignKey(cls.__tablename__ + '.id',
                                                 ondelete="CASCADE",
                                                 onupdate="CASCADE"),
                                   nullable=True),
            'parent': db.relationship(cls, backref='localized_ref'),
            'locale': db.Column(db.Unicode(255), default=lang, index=True)
        })

        cls_localized = type(class_name, (db.Model, CRUDMixin), columns)

        for field in localized_names:
            create_property(cls, cls_localized, columns, field)

        return cls

    return closure(cls)


def method_wrapper(success_status, error_status=http.BAD_REQUEST):
    def method_catcher(meth):
        @wraps(meth)
        def wrapper(*args, **kwargs):
            try:
                if request.method != 'DELETE':
                    try:
                        if request.form:
                            g.request_data = request.form.copy()
                        elif request.json:
                            g.request_data = request.json
                        elif request.data:
                            g.request_data = json.loads(request.data)
                        else:
                            abort(http.BAD_REQUEST)
                    except Exception as e:
                        raise t.DataError({'message': e.message})
                else:
                    g.request_data = None
                method_response = meth(*args, **kwargs)
                if isinstance(method_response, current_app.response_class):
                    return method_response
                else:
                    return jsonify_status_code(method_response, success_status)
            except t.DataError as e:
                return jsonify_status_code(e.as_dict(), error_status)
        return wrapper
    return method_catcher


class ClassProperty(property):
    def __init__(self, method, *args, **kwargs):
        method = classmethod(method)
        super(ClassProperty, self).__init__(method, *args, **kwargs)

    def __get__(self, cls, type=None):
        return self.fget.__get__(None, type)()


classproperty = ClassProperty
