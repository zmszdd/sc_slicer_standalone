; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c339c3706_alice_locked_amount () Int)
(declare-fun c339c3706_alice_personal_utilization () Int)
(declare-fun c339c3706_alice_prior_claimed () Int)
(declare-fun c339c3706_alice_prior_eligible () Int)
(declare-fun c339c3706_applied_utilization_ratio () Int)
(declare-fun c339c3706_protocol_swept_amount () Int)
(assert
 (= c339c3706_alice_locked_amount c339c3706_alice_locked_amount))
(assert
 (= c339c3706_alice_personal_utilization c339c3706_alice_personal_utilization))
(assert
 (= c339c3706_alice_prior_claimed c339c3706_alice_prior_claimed))
(assert
 (= c339c3706_alice_prior_eligible c339c3706_alice_prior_eligible))
(assert
 (= c339c3706_applied_utilization_ratio c339c3706_applied_utilization_ratio))
(assert
 (= c339c3706_protocol_swept_amount c339c3706_protocol_swept_amount))
(define-fun report_preconditions () Bool (and (= 100000 c339c3706_alice_locked_amount)
     (= 0 c339c3706_alice_prior_eligible)
     (= 0 c339c3706_alice_prior_claimed)
     (= 0 c339c3706_alice_personal_utilization)))
(define-fun report_safety () Bool (=> (and (= 0 c339c3706_alice_prior_eligible)
         (= 0 c339c3706_alice_prior_claimed))
    (= 100 c339c3706_applied_utilization_ratio)))
(define-fun report_effects () Bool (= 343 c339c3706_protocol_swept_amount))
