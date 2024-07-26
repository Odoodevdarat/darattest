# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class res_config_settings(models.TransientModel):
    """
    Re-write to show company duplicates settings
    """
    _inherit = "res.config.settings"

    @api.model
    def _default_rigid_crm_partner_duplicate_schema_id(self):
        """
        The default method for rigid_crm_partner_duplicate_schema_id
        """
        return self._get_default_schema_id("crm_duplicates.rigid_crm_partner_duplicate_schema_id")

    @api.model
    def _default_soft_crm_partner_duplicate_schema_id(self):
        """
        The default method for soft_crm_partner_duplicate_schema_id
        """
        return self._get_default_schema_id("crm_duplicates.soft_crm_partner_duplicate_schema_id")

    @api.model
    def _default_rigid_crm_lead_duplicate_schema_id(self):
        """
        The default method for rigid_crm_lead_duplicate_schema_id
        """
        return self._get_default_schema_id("crm_duplicates.rigid_crm_lead_duplicate_schema_id")

    @api.model
    def _default_soft_crm_lead_duplicate_schema_id(self):
        """
        The default method for soft_crm_lead_duplicate_schema_id
        """
        return self._get_default_schema_id("crm_duplicates.soft_crm_lead_duplicate_schema_id")

    @api.constrains("search_crm_duplicates_for_opportunities_only", "search_crm_duplicates_for_leads_only")
    def _check_opportunity_type_schema(self):
        """
        Constraint on opportunity type options
        """
        for setting in self:
            if setting.search_crm_duplicates_for_leads_only and setting.search_crm_duplicates_for_opportunities_only:
                raise ValidationError(
                    _("Nie można ograniczyć wykrywania duplikatów w CRM dla potencjalnych klientów i szans jednocześnie!")
                )

    rigid_crm_partner_duplicate_schema_id = fields.Many2one(
        "crm.duplicate.criteria",
        string="Kryteria duplikatów kontaktów sztywnych",
        default=_default_rigid_crm_partner_duplicate_schema_id,
    )
    soft_crm_partner_duplicate_schema_id = fields.Many2one(
        "crm.duplicate.criteria",
        string="Kryteria duplikatów kontaktów programowych",
        default=_default_soft_crm_partner_duplicate_schema_id,
    )
    search_crm_duplicates_for_companies_only = fields.Boolean(
        string="Traktuj firmy i samodzielne osoby jako duplikaty",
        config_parameter="crm_duplicates.search_crm_duplicates_for_companies_only",
    )
    rigid_crm_lead_duplicate_schema_id = fields.Many2one(
        "crm.duplicate.criteria",
        string="Sztywne kryteria duplikatów możliwości",
        config_parameter="crm_duplicates.rigid_crm_lead_duplicate_schema_id",
        default=_default_rigid_crm_lead_duplicate_schema_id,
    )
    soft_crm_lead_duplicate_schema_id = fields.Many2one(
        "crm.duplicate.criteria",
        string="Kryteria zduplikowanych możliwości miękkich",
        default=_default_soft_crm_lead_duplicate_schema_id,
    )
    search_crm_duplicates_for_opportunities_only = fields.Boolean(
        string="Jako duplikaty traktowane są tylko możliwości",
        config_parameter="crm_duplicates.search_crm_duplicates_for_opportunities_only",
    )
    search_crm_duplicates_for_leads_only = fields.Boolean(
        string="Tylko potencjalni klienci są traktowani jako duplikaty",
        config_parameter="crm_duplicates.search_crm_duplicates_for_leads_only",
    )
    group_crm_duplicates_show_soft = fields.Boolean(
        "Nie pokazuj liczby duplikatów w Soft CRM (przycisk widoku formularza)",
        implied_group="crm_duplicates.group_crm_duplicates_show_soft",
    )
    group_crm_duplicates_show_soft_list = fields.Boolean(
        "Nie wyświetlaj liczby duplikatów w CRM (widok drzewa i kanban)",
        implied_group="crm_duplicates.group_crm_duplicates_show_soft_list",
    )
    no_check_under_sudo_lead = fields.Boolean(
        "Nie sprawdzaj sztywnych duplikatów leadów pod nadzorem superużytkownika",
        config_parameter="crm_duplicates.no_check_under_sudo_lead",
    )
    no_check_under_sudo_contact = fields.Boolean(
        "Nie należy sprawdzać duplikatów sztywnych kontaktów w trybie superużytkownika",
        config_parameter="crm_duplicates.no_check_under_sudo_contact",
    )


    def _get_default_schema_id(self, config):
        """
        The helper method to try/catch reference

        Returns:
         * crm.duplicate.criteria object or False
        """
        try:
            res = self.sudo().env.ref(config, False)
        except:
            res = False
        return res
