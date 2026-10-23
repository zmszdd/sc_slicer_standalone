; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c871b6d5b_hedge_order_submitted () Bool)
(declare-fun c871b6d5b_pm_enabled () Bool)
(declare-fun c871b6d5b_settle_bricked () Bool)
(declare-fun c871b6d5b_slot_absent () Bool)
(assert
 (= c871b6d5b_hedge_order_submitted c871b6d5b_hedge_order_submitted))
(assert
 (= c871b6d5b_pm_enabled c871b6d5b_pm_enabled))
(assert
 (= c871b6d5b_settle_bricked c871b6d5b_settle_bricked))
(assert
 (= c871b6d5b_slot_absent c871b6d5b_slot_absent))
(define-fun report_preconditions () Bool (and c871b6d5b_pm_enabled c871b6d5b_hedge_order_submitted c871b6d5b_slot_absent))
(define-fun report_safety () Bool (=> (and c871b6d5b_pm_enabled
         c871b6d5b_hedge_order_submitted
         c871b6d5b_slot_absent)
    (not c871b6d5b_settle_bricked)))
(define-fun report_effects () Bool (and c871b6d5b_pm_enabled
     c871b6d5b_hedge_order_submitted
     c871b6d5b_slot_absent
     (not (not c871b6d5b_settle_bricked))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
