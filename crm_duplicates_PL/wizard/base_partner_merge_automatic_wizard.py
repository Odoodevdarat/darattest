# -*- coding: utf-8 -*-

from odoo import models

class base_partner_merge_automatic_wizard(models.TransientModel):
    """
    Re-write to pass context and allow merging partner
    """
    _inherit = "base.partner.merge.automatic.wizard"

    def action_merge(self):
        """
        Re-write to pass context
        """
        return super(base_partner_merge_automatic_wizard, self.with_context(no_duplication_check=True)).action_merge()
