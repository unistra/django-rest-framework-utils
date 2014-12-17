# -*- coding: utf-8 -*-

"""
"""

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.contenttypes.models import ContentType

from django.db.models import Q
from .models import FieldPermission, UserFieldPermissions, FilterPermissionModel
from .utils import get_field_permissions
from .serializers import QSerializer


class UserFieldPermissionsForm(forms.ModelForm):

    """
    """

    permissions = forms.MultipleChoiceField(
        widget=FilteredSelectMultiple(
            verbose_name='User field permissions',
            is_stacked=False,
        )
    )

    class Meta:
        model = UserFieldPermissions
        exclude = ('content_type',)

    def __init__(self, *args, **kwargs):
        super(UserFieldPermissionsForm, self).__init__(*args, **kwargs)

        # Choices
        choice_str = lambda model, field, sep:\
            '{model[0]}{sep}{model[1]}{sep}{field}'\
                .format(model=model.split('.'), field=field, sep=sep)

        choices = []
        for model, fields in get_field_permissions().items():
            choices += [(choice_str(model, field, '.'), choice_str(model, field, ' | '))
                        for field in fields]
        self.fields['permissions'].choices = sorted(choices)

        # Initial datas
        instance = kwargs.get('instance')
        if instance:
            fps = ['.'.join(fp) for fp in instance.permissions.all()
                   .values_list(
                        'content_type__app_label',
                        'content_type__model',
                        'name'
                    )
            ]
            self.initial['permissions'] = fps

    def save(self, commit=True):
        form = super(UserFieldPermissionsForm, self).save(commit=False)
        cleaned = self.cleaned_data

        field_permissions = []
        for permission in cleaned['permissions']:
            app_label, model_name, field = permission.split('.')
            ct = ContentType.objects.get_by_natural_key(app_label, model_name)
            fp = FieldPermission.objects.get_or_create(
                content_type=ct,
                name=field
            )[0]
            field_permissions.append(fp.pk)

        self.cleaned_data['permissions'] = field_permissions

        if commit:
            form.save()
            form.save_m2m()

        return form


class UserFieldPermissionsAdmin(admin.ModelAdmin):

    """
    """
    list_display = ('user', )
    form = UserFieldPermissionsForm


class UserFilterPermissionsForm(forms.ModelForm):
    """
    filter permissions form
    """

    current_filter = forms.CharField()

    class Meta:
        model = FilterPermissionModel

    def __init__(self, *args, **kwargs):
        form = super(UserFilterPermissionsForm, self).__init__(*args, **kwargs)

        # Initial datas
        instance = kwargs.get('instance')
        if instance:
            print(instance.filter)
            self.fields['current_filter'].widget.attrs['readonly'] = True
            self.fields['current_filter'].widget.attrs['size'] = 130
            self.initial['current_filter'] = QSerializer().loads(instance.filter)
            self.initial['filter'] = ""

    def clean_filter(self):
        data = self.cleaned_data['filter']
        if data:
            try:
                myq = Q(eval(data))
            except:
                raise Exception("filter is not a valid entry for a q object !")
            else:
                if isinstance(myq, Q):
                    data = QSerializer().dumps(myq)
                else:
                    raise Exception("filter is not a q object !")

        return data

    def save(self, commit=True):
        form = super(UserFilterPermissionsForm, self).save(commit=False)

        if commit:
            form.save()
            form.save_m2m()

        return form


class UserFilterPermissionsAdmin(admin.ModelAdmin):
    """
    filter permissions admin
    """
    list_display = ('user', 'content_type')
    form = UserFilterPermissionsForm


admin.site.register(UserFieldPermissions, UserFieldPermissionsAdmin)
admin.site.register(FilterPermissionModel, UserFilterPermissionsAdmin)
