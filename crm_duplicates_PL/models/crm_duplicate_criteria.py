# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

from odoo.exceptions import ValidationError
from odoo.osv.expression import AND, OR
from odoo.tools.safe_eval import safe_eval


class crm_duplicate_criteria(models.Model):
    _name = "crm.duplicate.criteria"
    _description = "Schemat duplikatów CRM"
    _rec_name = "duplicate_field_ids"

    @api.depends("duplicate_field_ids.field_description")
    def _compute_display_name(self):
        title = _("--> skonfiguruj kryteria duplikatów")
        if self._context.get("params") and self._context.get("params").get("model") == "res.config.settings":
            title =  _("--> kliknij, aby skonfigurować kryteria duplikatów")
        for criteria in self:
            name = title
            if criteria.duplicate_field_ids:
                name = "{} {}".format(", ".join(criteria.duplicate_field_ids.mapped("field_description")), title)
            criteria.display_name = name

    duplicate_field_ids = fields.Many2many(
        "ir.model.fields",
        "crm_duplicate_criteria_ir_model_fields_partner_rigid",
        "crm_duplicate_criteria_id",
        "ir_model_fields_id",
        string="Zduplikowane pola",
        domain="""[
            ('model', '=', res_model), ('store', '=', True),
            ('ttype', 'not in', ['one2many', 'many2many', 'binary', 'reference', 'serialized']),
        ]""",
    )
    res_model = fields.Char(string="Model")

    @api.model
    def _get_duplicates_schema(self, config_param, model_name="res.partner"):
        self = self.sudo()
        schema_id = False
        extra_domain = []
        criteria_id = self.env.ref(config_param, False)
        if criteria_id:
            schema_id = criteria_id
            Config = self.env["ir.config_parameter"]
            if model_name == "res.partner":
                if safe_eval(Config.get_param("crm_duplicates.search_crm_duplicates_for_companies_only", "False")):
                    extra_domain = [("parent_id", "=", False)]
            elif model_name == "crm.lead":
                if safe_eval(Config.get_param("crm_duplicates.search_crm_duplicates_for_opportunities_only", "False")):
                    extra_domain = [("type", "=", "opportunity")]
                elif safe_eval(Config.get_param("crm_duplicates.search_crm_duplicates_for_leads_only", "False")):
                    extra_domain = [("type", "=", "lead")]
        return schema_id, extra_domain

    def _get_duplicates_count(self, record, extra_domain, model_name="res.partner"):
        self = self.sudo()
        duplicates_count = 0
        field_domain = self._construct_field_domain(record, "ilike")
        if field_domain:
             if self._check_record_for_extra_domain(record, extra_domain, model_name):
                duplicates_count = self.env[model_name].search_count(AND([field_domain, extra_domain]))
        return duplicates_count

    def _check_rigid_duplicates(self, records, extra_domain, model_name="res.partner"):
        self = self.sudo()
        warning = _("Aktualizacja nie jest możliwa, ponieważ wykryto duplikaty: {}")
        for record in records:
            if self._check_record_for_extra_domain(record, extra_domain, model_name):
                field_domain = self._construct_field_domain(record, "=")
                if field_domain:
                    duplicate_ids = self.env[model_name].search(AND([field_domain, extra_domain]))
                    if duplicate_ids:
                        warn_text = ", ".join(duplicate_ids.mapped(lambda rec: "[{}] {} (Sprzedawca: {})".format(rec.id, rec.name, rec.user_id.name or _("Brak sprzedawcy"))))
                        raise ValidationError(warning.format(warn_text))

    def _get_soft_duplicates(self, record, extra_domain, model_name="res.partner"):
        self = self.sudo()
        duplicates = []
        if self._check_record_for_extra_domain(record, extra_domain, model_name):
            field_domain = self._construct_field_domain(record, "ilike")
            if field_domain:
                duplicates = self.env[model_name].search(AND([field_domain, extra_domain])).ids
        return duplicates

    def _check_record_for_extra_domain(self, record, extra_domain, model_name="res.partner"):
        this_extra_id = True
        if extra_domain:
            this_extra_id = self.env[model_name].search_count(AND([[("id", "=", record.id)], extra_domain]), limit=1)
        return this_extra_id

    def _construct_field_domain(self, record, char_operator="="):
        fields_domain = []
        for field in self.duplicate_field_ids:
            if record[field.name]:
                if field.ttype == "many2one":
                    fields_domain = OR([fields_domain, [(field.name, "in", record[field.name].ids)]])
                elif field.ttype == "char":
                    fields_domain = OR([fields_domain, [(field.name, char_operator, record[field.name])]])
                else:
                    fields_domain = OR([fields_domain, [(field.name, "=", record[field.name])]])

        if fields_domain:
            fields_domain = AND([
                fields_domain,
                [("id", "!=", record.id), "|", ("company_id", "=", False), ("company_id", "=", record.company_id.id)]
            ])
        return fields_domain
