# -*- coding: utf-8 -*-
from functools import partial

from openprocurement.api.validation import validate_data, validate_json_data
from .utils import update_logging_context, raise_operation_error
from openprocurement.api.validation import (  # noqa: F401
    validate_accreditations,
    validate_change_status, # noqa forwarded import
    validate_document_data, # noqa forwarded import
    validate_file_upload, # noqa forwarded import
    validate_items_uniq, # noqa forwarded import
    validate_decision_uniq, # noqa forwarded import
    validate_patch_document_data, # noqa forwarded import
    validate_t_accreditation,
    validate_decision_post, # noqa forwarded import
    validate_decision_patch_data, # noqa forwarded import
    validate_decision_after_rectificationPeriod,
    validate_decision_update_in_not_allowed_status
)

validate_decision_after_rectificationPeriod = partial(
    validate_decision_after_rectificationPeriod,
    parent_resource='lot'
)
validate_decision_update_in_not_allowed_status = partial(
    validate_decision_update_in_not_allowed_status,
    parent_resource='lot'
)


def validate_lot_data(request, **kwargs):
    update_logging_context(request, {'lot_id': '__new__'})
    data = validate_json_data(request)
    model = request.lot_from_data(data, create=False)

    validate_accreditations(request, model, 'lot')

    data = validate_data(request, model, "lot", data=data)
    validate_t_accreditation(request, data, 'lot')


def validate_post_lot_role(request, error_handler, **kwargs):
    if request.authenticated_role in ('convoy', 'concierge'):
        request.errors.add('body', 'accreditation', 'Can\'t create lot as bot')
        request.errors.status = 403
        raise error_handler(request)


def validate_patch_lot_data(request, error_handler, **kwargs):
    data = validate_json_data(request)
    editing_roles = request.content_configurator.available_statuses[request.context.status]['editing_permissions']
    if request.authenticated_role not in editing_roles:
        msg = 'Can\'t update {} in current ({}) status'.format(request.validated['resource_type'],
                                                               request.context.status)
        raise_operation_error(request, error_handler, msg)
    default_status = type(request.lot).fields['status'].default
    if data.get('status') == default_status and data.get('status') != request.context.status:
        raise_operation_error(request, error_handler, 'Can\'t switch lot to {} status'.format(default_status))
    validate_change_status(request, error_handler, **kwargs)
    return validate_data(request, type(request.lot), data=data)


def validate_lot_document_update_not_by_author_or_lot_owner(request, error_handler, **kwargs):
    if request.authenticated_role != (request.context.author or 'lot_owner'):
        request.errors.add('url', 'role', 'Can update document only author')
        request.errors.status = 403
        raise error_handler(request)


def validate_update_item_in_not_allowed_status(request, error_handler, **kwargs):
    status = request.validated['lot_status']
    editing_statuses = request.content_configurator.item_editing_allowed_statuses
    if status not in editing_statuses:
        raise_operation_error(request, error_handler,
                              'Can\'t update item in current ({}) lot status'.format(status))
