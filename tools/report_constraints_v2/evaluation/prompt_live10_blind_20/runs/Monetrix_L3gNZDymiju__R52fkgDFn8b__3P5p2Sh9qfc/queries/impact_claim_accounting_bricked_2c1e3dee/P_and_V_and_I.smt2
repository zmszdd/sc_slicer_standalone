; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2f557382_accounting_available () Bool)
(declare-fun c2f557382_hedge_order_submitted_flag () Bool)
(declare-fun c2f557382_pm_enabled_flag () Bool)
(declare-fun c2f557382_supplied_slot_absent () Bool)
(assert
 (= c2f557382_accounting_available c2f557382_accounting_available))
(assert
 (= c2f557382_hedge_order_submitted_flag c2f557382_hedge_order_submitted_flag))
(assert
 (= c2f557382_pm_enabled_flag c2f557382_pm_enabled_flag))
(assert
 (= c2f557382_supplied_slot_absent c2f557382_supplied_slot_absent))
(define-fun report_preconditions () Bool (and c2f557382_pm_enabled_flag
     c2f557382_hedge_order_submitted_flag
     c2f557382_supplied_slot_absent))
(define-fun report_safety () Bool (=> (and c2f557382_pm_enabled_flag
         c2f557382_hedge_order_submitted_flag
         c2f557382_supplied_slot_absent)
    c2f557382_accounting_available))
(define-fun report_effects () Bool (and c2f557382_pm_enabled_flag
     c2f557382_hedge_order_submitted_flag
     c2f557382_supplied_slot_absent
     (not c2f557382_accounting_available)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
