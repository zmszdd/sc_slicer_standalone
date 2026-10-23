; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca593784f_hype_amount_at_confirmation () Int)
(declare-fun ca593784f_hype_amount_at_queue () Int)
(declare-fun ca593784f_hype_amount_paid_on_confirmation () Int)
(declare-fun ca593784f_min_period_elapsed () Bool)
(declare-fun ca593784f_rate_decreased_between () Bool)
(declare-fun ca593784f_withdrawal_queued () Bool)
(assert
 (= ca593784f_hype_amount_at_confirmation ca593784f_hype_amount_at_confirmation))
(assert
 (= ca593784f_hype_amount_at_queue ca593784f_hype_amount_at_queue))
(assert
 (= ca593784f_hype_amount_paid_on_confirmation ca593784f_hype_amount_paid_on_confirmation))
(assert
 (= ca593784f_min_period_elapsed ca593784f_min_period_elapsed))
(assert
 (= ca593784f_rate_decreased_between ca593784f_rate_decreased_between))
(assert
 (= ca593784f_withdrawal_queued ca593784f_withdrawal_queued))
(define-fun report_preconditions () Bool (and ca593784f_withdrawal_queued
     (< 0 ca593784f_hype_amount_at_queue)
     ca593784f_min_period_elapsed
     ca593784f_rate_decreased_between))
(define-fun report_safety () Bool (=> (and ca593784f_withdrawal_queued
         ca593784f_min_period_elapsed
         ca593784f_rate_decreased_between)
    (= ca593784f_hype_amount_paid_on_confirmation
       ca593784f_hype_amount_at_confirmation)))
(define-fun report_effects () Bool (and ca593784f_withdrawal_queued
     ca593784f_min_period_elapsed
     ca593784f_rate_decreased_between
     (not (= ca593784f_hype_amount_paid_on_confirmation
             ca593784f_hype_amount_at_confirmation))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
