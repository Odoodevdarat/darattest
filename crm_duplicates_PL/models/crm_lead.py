# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class crm_lead(models.Model):
    """
    Re-write to add duplciates search features
    """
    _inherit = "crm.lead"

    def _compute_duplicates_count(self):
        """
        Compute method for duplicates_count

        Methods:
         * _get_duplicates_schema of crm.duplicate.criteria
         * _get_duplicates_count of crm.duplicate.criteria
        """
        schema_id, extra_domain = self.env["crm.duplicate.criteria"]._get_duplicates_schema(
            "crm_duplicates.soft_crm_lead_duplicate_schema_id", self._name,
        )
        for partner in self:
            duplicates_count = 0
            if schema_id:
                duplicates_count = schema_id._get_duplicates_count(partner, extra_domain, self._name)
            partner.duplicates_count = duplicates_count

    @api.model
    def search_duplicates_count(self, operator, value):
        """
        Search method for duplicates_count
        Introduced since the field is not stored
        """
        partners = self.search([])
        potential_dupplicates = []
        for partner in partners:
            if partner.duplicates_count > 0:
                potential_dupplicates.append(partner.id)
        return [("id", "in", potential_dupplicates)]

    duplicates_count = fields.Integer(
        string="Liczba duplikatów", compute=_compute_duplicates_count, search="search_duplicates_count",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overwrite to force "write" in "create"

        Methods:
         * _check_rigid_duplicates
        """
        partner_ids = super(crm_lead, self).create(vals_list)
        partner_ids._check_rigid_duplicates()
        return partner_ids

    def write(self, vals):
        """
        Overwrite to check for rigid duplicates and raise UserError in such a case

        Methods:
         * _check_rigid_duplicates
        """
        partner_ids = super(crm_lead, self).write(vals)
        self._check_rigid_duplicates()
        return partner_ids

    def action_open_duplicates(self):
        """
        The method to open tree of potential duplicates

        Methods:
         * _get_duplicates_schema of crm.duplicate.criteria
         * _get_soft_duplicates of crm.duplicate.criteria

        Returns:
         * dict - action to open partners duplicates list

        Extra info:
         * Expected singleton
        """
        schema_id, extra_domain = self.env["crm.duplicate.criteria"]._get_duplicates_schema(
            "crm_duplicates.soft_crm_lead_duplicate_schema_id", self._name,
        )
        if schema_id:
            duplicates = schema_id._get_soft_duplicates(self, extra_domain, self._name)
            return {
                "name": "Duplikaty",
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "crm.lead",
                "domain": [("id", "in", duplicates + self.ids)],
                "type": "ir.actions.act_window",
                "target": "current",
            }

    def merge_opportunity(self, user_id=False, team_id=False, auto_unlink=True):
        """
        Overwrite to pass context and let merge duplicats
        """
        context = {"no_duplication_check": True,}
        return super(crm_lead, self.with_context(context)).merge_opportunity(
            user_id=user_id, team_id=team_id, auto_unlink=auto_unlink,
        )

    def _check_rigid_duplicates(self):
        """
        The method to check each updated partner for rigid duplicates

        Methods:
         * _get_duplicates_schema of crm.duplicate.criteria
         * _check_rigid_duplicates of crm.duplicate.criteria

        Raises:
         * Validation error if any duplicates are found
        """
        if not self._context.get("no_duplication_check"):
            if self.env.is_superuser():
                Config = self.env["ir.config_parameter"]
                if safe_eval(Config.get_param("crm_duplicates.no_check_under_sudo_lead", "False")):
                    return
            schema_id, extra_domain = self.env["crm.duplicate.criteria"]._get_duplicates_schema(
                "crm_duplicates.rigid_crm_lead_duplicate_schema_id", self._name,
            )
            if schema_id:
                schema_id._check_rigid_duplicates(self, extra_domain, self._name)
