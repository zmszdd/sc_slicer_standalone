; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0ec0039c_is_first_claim () Bool)
(declare-fun c0ec0039c_is_new_passive_staker () Bool)
(declare-fun c0ec0039c_penalty_applied () Bool)
(declare-fun c0ec0039c_raw_utilization_delta () Int)
(assert
 (= c0ec0039c_is_first_claim c0ec0039c_is_first_claim))
(assert
 (= c0ec0039c_is_new_passive_staker c0ec0039c_is_new_passive_staker))
(assert
 (= c0ec0039c_penalty_applied c0ec0039c_penalty_applied))
(assert
 (= c0ec0039c_raw_utilization_delta c0ec0039c_raw_utilization_delta))
(define-fun report_preconditions () Bool (and c0ec0039c_is_new_passive_staker
     c0ec0039c_is_first_claim
     (= 0 c0ec0039c_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and c0ec0039c_is_new_passive_staker
         c0ec0039c_is_first_claim
         (= 0 c0ec0039c_raw_utilization_delta))
    (not c0ec0039c_penalty_applied)))
(define-fun report_effects () Bool (and c0ec0039c_is_new_passive_staker
     c0ec0039c_is_first_claim
     (= 0 c0ec0039c_raw_utilization_delta)
     (not (not c0ec0039c_penalty_applied))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
